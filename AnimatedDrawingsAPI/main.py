from flask import Flask, request
import cv2
from pathlib import Path
import requests
import json
import numpy as np
import yaml
from skimage import measure
from scipy import ndimage

import logging

app = Flask(__name__)
FILES = Path('/mycode/files')
SOURCES = Path('/mycode/AnimatedDrawingsAPI/sources')

import sys
sys.path.append(SOURCES.as_posix())
import animated_drawings.render

@app.route('/ping')
def ping():
    return 'animated_drawings test ping success!!'


def fail(msg: str) -> dict:
    return {
        'is_success' : False,
        'msg' : msg
    }

def success() -> dict:
    return {
        'is_success' : True,
        'msg' : ''
    }


@app.route('/upload_a_drawing')
def upload_a_drawing():
    # check request parameter
    request_dict = request.args.to_dict()
    key_ad_id = 'ad_id'
    if key_ad_id not in request_dict:
        return fail(msg='no request parameter')

    ad_id = request_dict[key_ad_id]
    base_path: Path = FILES.joinpath(ad_id)
    file_name = 'image.png'
    img_fn = base_path.joinpath(file_name).as_posix()

    # read image
    img = cv2.imread(img_fn)

    # ensure it's rgb
    if len(img.shape) != 3:
        msg = f'image must have 3 channels (rgb). Found {len(img.shape)}'
        return fail(msg=msg)
    
    # convert to bytes and send to torchserve
    img_b = cv2.imencode('.png', img)[1].tobytes()
    request_data = {'data': img_b}
    resp = requests.post("http://torchserve:8080/predictions/drawn_humanoid_detector", files=request_data, verify=False)
    if resp is None or resp.status_code >= 300:
        msg = f"Failed to get bounding box, please check if the 'docker_torchserve' is running and healthy, resp: {resp}"
        return fail(msg=msg)

    detection_results = json.loads(resp.content)

    # error check detection_results
    if type(detection_results) == dict and 'code' in detection_results.keys() and detection_results['code'] == 404:
        msg = f'Error performing detection. Check that drawn_humanoid_detector.mar was properly downloaded. Response: {detection_results}'
        return fail(msg=msg)

    # order results by score, descending
    detection_results.sort(key=lambda x: x['score'], reverse=True)

    # if no drawn humanoids detected, abort
    if len(detection_results) == 0:
        msg = 'Could not detect any drawn humanoids in the image. Aborting'
        return fail(msg=msg)

    # otherwise, report # detected and score of highest.
    log_file_path = base_path.joinpath('logs/log.txt')
    logging.basicConfig(filename=log_file_path.as_posix(), level=logging.DEBUG)
    msg = f'Detected {len(detection_results)} humanoids in image. Using detection with highest score {detection_results[0]["score"]}.'
    logging.info(msg)
    
    # calculate the coordinates of the character bounding box
    bbox = np.array(detection_results[0]['bbox'])
    l, t, r, b = [round(x) for x in bbox]

    # dump the bounding box results to file
    bouding_box_path = base_path.joinpath('bounding_box.yaml')
    with open(bouding_box_path.as_posix(), 'w') as f:
        yaml.dump({
            'left': l,
            'top': t,
            'right': r,
            'bottom': b
        }, f)

    return success()


@app.route('/find_the_character')
def find_the_character():
    # check request parameter
    request_dict = request.args.to_dict()
    key_ad_id = 'ad_id'
    if key_ad_id not in request_dict:
        return fail(msg='no request parameter')

    ad_id = request_dict['ad_id']
    base_path: Path = FILES.joinpath(ad_id)
    
    # crop the image
    bounding_box_path = base_path.joinpath('bounding_box.yaml')
    bounding_box_dict = yaml.safe_load(bounding_box_path.read_text())
    t = int(bounding_box_dict['top'])
    b = int(bounding_box_dict['bottom'])
    l = int(bounding_box_dict['left'])
    r = int(bounding_box_dict['right'])
    original_image_path = base_path.joinpath('image.png')
    img = cv2.imread(original_image_path.as_posix())
    cropped = img[t:b, l:r]
    cropped_img_path = base_path.joinpath('texture.png')
    cv2.imwrite(cropped_img_path.as_posix(), cropped)

    # save mask
    mask_image_path = base_path.joinpath('mask.png')
    try:
        mask = segment(cropped)
    except:
        return fail('Found no contours within image')
    cv2.imwrite(mask_image_path.as_posix(), mask)

    # create masked_image(texture + mask)
    masked_img = cropped.copy()
    masked_img = cv2.cvtColor(masked_img, cv2.COLOR_BGR2BGRA)
    masked_img[:, :, 3] = mask
    masked_image_path = base_path.joinpath('masked_img.png')
    cv2.imwrite(masked_image_path.as_posix(), masked_img)

    return success()


@app.route('/separate_character')
def separate_character():
    # check request parameter
    request_dict = request.args.to_dict()
    key_ad_id = 'ad_id'
    if key_ad_id not in request_dict:
        return fail(msg='no request parameter')
    
    ad_id = request_dict['ad_id']
    base_path: Path = FILES.joinpath(ad_id)

    cropped_img_path = base_path.joinpath('texture.png')
    masked_img_path = base_path.joinpath('masked_img.png')

    # resize masked_img.png
    cropped_img = cv2.imread(cropped_img_path.as_posix(), cv2.IMREAD_UNCHANGED)
    height, width, _ = cropped_img.shape
    masked_img = cv2.imread(masked_img_path.as_posix(), cv2.IMREAD_UNCHANGED)
    resized_masked_img = cv2.resize(masked_img, dsize=(width, height), interpolation=cv2.INTER_LINEAR)
    cv2.imwrite(masked_img_path.as_posix(), resized_masked_img)

    # resave mask.png
    masked_img = cv2.imread(masked_img_path.as_posix(), cv2.IMREAD_UNCHANGED)
    mask_path = base_path.joinpath('mask.png')
    mask = masked_img[:, :, 3]
    cv2.imwrite(mask_path.as_posix(), mask)

    # send cropped image to pose estimator
    cropped = cv2.imread(cropped_img_path.as_posix())
    data_file = {'data': cv2.imencode('.png', cropped)[1].tobytes()}
    resp = requests.post("http://torchserve:8080/predictions/drawn_humanoid_pose_estimator", files=data_file, verify=False)
    if resp is None or resp.status_code >= 300:
        msg = f"Failed to get skeletons, please check if the 'docker_torchserve' is running and healthy, resp: {resp}"
        return fail(msg=msg)

    pose_results = json.loads(resp.content)

    # error check pose_results
    if type(pose_results) == dict and 'code' in pose_results.keys() and pose_results['code'] == 404:
        msg = f'Error performing pose estimation. Check that drawn_humanoid_pose_estimator.mar was properly downloaded. Response: {pose_results}'
        return fail(msg=msg)
    
    # if cannot detect any skeleton, abort
    if len(pose_results) == 0:
        msg = 'Could not detect any skeletons within the character bounding box. Expected exactly 1. Aborting.'
        return msg
    
    # if more than one skeleton detected, abort
    if 1 < len(pose_results):
        msg = f'Detected {len(pose_results)} skeletons with the character bounding box. Expected exactly 1. Aborting.'
        return msg
    
    # get x y coordinates of detection joint keypoints
    kpts = np.array(pose_results[0]['keypoints'])[:, :2]

    # use them to build character skeleton rig
    skeleton = []
    skeleton.append({'loc' : [round(x) for x in (kpts[11]+kpts[12])/2], 'name': 'root'          , 'parent': None})
    skeleton.append({'loc' : [round(x) for x in (kpts[11]+kpts[12])/2], 'name': 'hip'           , 'parent': 'root'})
    skeleton.append({'loc' : [round(x) for x in (kpts[5]+kpts[6])/2  ], 'name': 'torso'         , 'parent': 'hip'})
    skeleton.append({'loc' : [round(x) for x in  kpts[0]             ], 'name': 'neck'          , 'parent': 'torso'})
    skeleton.append({'loc' : [round(x) for x in  kpts[6]             ], 'name': 'right_shoulder', 'parent': 'torso'})
    skeleton.append({'loc' : [round(x) for x in  kpts[8]             ], 'name': 'right_elbow'   , 'parent': 'right_shoulder'})
    skeleton.append({'loc' : [round(x) for x in  kpts[10]            ], 'name': 'right_hand'    , 'parent': 'right_elbow'})
    skeleton.append({'loc' : [round(x) for x in  kpts[5]             ], 'name': 'left_shoulder' , 'parent': 'torso'})
    skeleton.append({'loc' : [round(x) for x in  kpts[7]             ], 'name': 'left_elbow'    , 'parent': 'left_shoulder'})
    skeleton.append({'loc' : [round(x) for x in  kpts[9]             ], 'name': 'left_hand'     , 'parent': 'left_elbow'})
    skeleton.append({'loc' : [round(x) for x in  kpts[12]            ], 'name': 'right_hip'     , 'parent': 'root'})
    skeleton.append({'loc' : [round(x) for x in  kpts[14]            ], 'name': 'right_knee'    , 'parent': 'right_hip'})
    skeleton.append({'loc' : [round(x) for x in  kpts[16]            ], 'name': 'right_foot'    , 'parent': 'right_knee'})
    skeleton.append({'loc' : [round(x) for x in  kpts[11]            ], 'name': 'left_hip'      , 'parent': 'root'})
    skeleton.append({'loc' : [round(x) for x in  kpts[13]            ], 'name': 'left_knee'     , 'parent': 'left_hip'})
    skeleton.append({'loc' : [round(x) for x in  kpts[15]            ], 'name': 'left_foot'     , 'parent': 'left_knee'})

    # create the character config dictionary
    char_cfg = {'skeleton': skeleton, 'height': cropped.shape[0], 'width': cropped.shape[1]}
    char_cfg_path = base_path.joinpath('char_cfg.yaml')
    # dump character config to yaml
    with open(char_cfg_path.as_posix(), 'w') as f:
        yaml.dump(char_cfg, f)

    return success()


def segment(img: np.ndarray):
    """ threshold """
    img = np.min(img, axis=2)
    img = cv2.adaptiveThreshold(img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 115, 8)
    img = cv2.bitwise_not(img)

    """ morphops """
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    img = cv2.morphologyEx(img, cv2.MORPH_CLOSE, kernel, iterations=2)
    img = cv2.morphologyEx(img, cv2.MORPH_DILATE, kernel, iterations=2)

    """ floodfill """
    mask = np.zeros([img.shape[0]+2, img.shape[1]+2], np.uint8)
    mask[1:-1, 1:-1] = img.copy()

    # im_floodfill is results of floodfill. Starts off all white
    im_floodfill = np.full(img.shape, 255, np.uint8)

    # choose 10 points along each image side. use as seed for floodfill.
    h, w = img.shape[:2]
    for x in range(0, w-1, 10):
        cv2.floodFill(im_floodfill, mask, (x, 0), 0)
        cv2.floodFill(im_floodfill, mask, (x, h-1), 0)
    for y in range(0, h-1, 10):
        cv2.floodFill(im_floodfill, mask, (0, y), 0)
        cv2.floodFill(im_floodfill, mask, (w-1, y), 0)

    # make sure edges aren't character. necessary for contour finding
    im_floodfill[0, :] = 0
    im_floodfill[-1, :] = 0
    im_floodfill[:, 0] = 0
    im_floodfill[:, -1] = 0

    """ retain largest contour """
    mask2 = cv2.bitwise_not(im_floodfill)
    mask = None
    biggest = 0

    contours = measure.find_contours(mask2, 0.0)
    for c in contours:
        x = np.zeros(mask2.T.shape, np.uint8)
        cv2.fillPoly(x, [np.int32(c)], 1)
        size = len(np.where(x == 1)[0])
        if size > biggest:
            mask = x
            biggest = size

    if mask is None:
        assert False, 'Found no contours within image'

    mask = ndimage.binary_fill_holes(mask).astype(int)
    mask = 255 * mask.astype(np.uint8)

    return mask.T


@app.route('/add_animation')
def add_animation():
    # check request parameter
    request_dict = request.args.to_dict()
    key_ad_id = 'ad_id'
    key_ad_animation = 'ad_animation'
    if key_ad_id not in request_dict or key_ad_animation not in request_dict:
        return fail(msg='no request parameter')
    
    ad_id = request_dict['ad_id']
    ad_animation = request_dict['ad_animation']

    file_path: Path = FILES.joinpath(ad_id)
    video_path = file_path.joinpath('video')
    video_path.mkdir(exist_ok = True)
    output_video_path: Path = video_path.joinpath(f'{ad_animation}.gif')
    if output_video_path.exists():
        return success()

    """
    Given a path to a directory with character annotations, a motion configuration file, and a retarget configuration file,
    creates an animation and saves it to {annotation_dir}/video.png
    """
    # package character_cfg_fn, motion_cfg_fn, and retarget_cfg_fn
    char_cfg_path = file_path.joinpath('char_cfg.yaml')
    motion_cfg_path = SOURCES.joinpath(f'examples/config/motion/{ad_animation}.yaml')
    retarget_cfg_path = SOURCES.joinpath('examples/config/retarget/fair1_ppf.yaml')
    animated_drawing_dict = {
        'character_cfg': char_cfg_path.as_posix(),
        'motion_cfg': motion_cfg_path.as_posix(),
        'retarget_cfg': retarget_cfg_path.as_posix()
    }

    # create mvc config
    mvc_cfg = {
        'scene': {'ANIMATED_CHARACTERS': [animated_drawing_dict]},  # add the character to the scene
        'controller': {
            'MODE': 'video_render',  # 'video_render' or 'interactive'
            'OUTPUT_VIDEO_PATH': output_video_path.as_posix() # set the output location
            }
    }

    # write the new mvc config file out
    output_mvc_cfg_path = file_path.joinpath('mvc_cfg.yaml')
    with open(output_mvc_cfg_path.as_posix(), 'w') as f:
        yaml.dump(dict(mvc_cfg), f)

    # render the video
    animated_drawings.render.start(output_mvc_cfg_path.as_posix())

    return success()


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port='8001')