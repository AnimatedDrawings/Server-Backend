from flask import Flask, send_file, request
import cv2
from pathlib import Path
import requests
import json
import numpy as np
import yaml
from skimage import measure
from scipy import ndimage

app = Flask(__name__)
FILES = Path('/mycode/files')

@app.route('/ping')
def ping():
    return 'animated_drawings test ping success!!'

@app.route('/upload_a_drawing')
def upload_a_drawing():
    request_dict = request.args.to_dict()
    # check request parameter
    if len(request_dict) == 0:
        return 'no request parameter'

    ad_id = request_dict['ad_id']
    base_path: Path = FILES.joinpath(ad_id)
    file_name = 'image.png'
    img_fn = base_path.joinpath(file_name).as_posix()

    # read image
    img = cv2.imread(img_fn)

    # ensure it's rgb
    if len(img.shape) != 3:
        return 'image is not rgb'
    
    # convert to bytes and send to torchserve
    img_b = cv2.imencode('.png', img)[1].tobytes()
    request_data = {'data': img_b}
    resp = requests.post("http://torchserve:8080/predictions/drawn_humanoid_detector", files=request_data, verify=False)

    if resp is None or resp.status_code >= 300:
        return 'torchserve connection error : bounding box' 

    detection_results = json.loads(resp.content)

    # error check detection_results
    if type(detection_results) == dict and 'code' in detection_results.keys() and detection_results['code'] == 404:
        msg = 'Error performing detection. Check that drawn_humanoid_detector.mar was properly downloaded. Response: {detection_results}'
        return msg

    # order results by score, descending
    detection_results.sort(key=lambda x: x['score'], reverse=True)
    # if no drawn humanoids detected, abort
    if len(detection_results) == 0:
        msg = 'Could not detect any drawn humanoids in the image. Aborting'
        return msg
    
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

    bounding_box_dict = {
        'left' : l,
        'top' : t,
        'right' : r,
        'bottom' : b
    }
    return bounding_box_dict


@app.route('/find_the_character')
def find_the_character():
    request_dict = request.args.to_dict()

    # check request parameter
    if len(request_dict) == 0:
        return 'no request parameter'
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
    cropped_image_path = base_path.joinpath('texture.png')
    cv2.imwrite(cropped_image_path.as_posix(), cropped)

    # save mask
    mask_image_path = base_path.joinpath('mask.png')
    mask = segment(cropped)
    cv2.imwrite(mask_image_path.as_posix(), mask)

    return { 'ad_id' : ad_id }


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

    # if mask is None:
    #     msg = 'Found no contours within image'
    #     logging.critical(msg)
    #     assert False, msg

    mask = ndimage.binary_fill_holes(mask).astype(int)
    mask = 255 * mask.astype(np.uint8)

    return mask.T



'''
1. [Fast] masked file 로컬 저장
2. [Fast] masked file_location postgres ad_db에 저장
3. [AD]
    1. image_to_annotations/
    2. masked_file_url로 annotation file(char_cfg.yaml) 생성
    3. annotation file url return
    [Fast]
    1. annotation file url postgres ad_db에 저장
    2. annotation file url -> char_cfg.yaml -> Json 변환후 리턴
'''
# @app.route('/image_to_annotations')
# def api_image_to_annotations():
#     parameter_dict = request.args.to_dict()
#     if len(parameter_dict) == 0:
#         return 'No parameter'

#     path = parameter_dict['path']
#     file_name = parameter_dict['file_name']
#     extension = parameter_dict['extension']
#     img_fn = path + file_name + extension
#     out_dir = ANNOTATIONS + file_name
#     image_to_annotations(img_fn = img_fn, out_dir = out_dir)

#     annotation_info = {
#         'path' : ANNOTATIONS + file_name + '/',
#         'joint_filename' : 'char_cfg.yaml'
#     }

#     return annotation_info

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port='8001')