from flask import Flask, send_file, request
import cv2
from pathlib import Path
import requests
import json
import numpy as np
import yaml

app = Flask(__name__)
FILES = Path('/mycode/files')

@app.route('/ping')
def ping():
    return 'animated_drawings test ping success!!'

@app.route('/detect_bounding_box')
def detect_bounding_box():
    request_dict = request.args.to_dict()
    # check request parameter
    if len(request_dict) == 0:
        return 'no request parameter'

    ad_id = request_dict['ad_id']
    base_path: Path = FILES.joinpath(ad_id)
    file_name = 'original_image.png'
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

    bounding_box_location = base_path.joinpath('bounding_box.yaml').as_posix()
    with open(bounding_box_location, 'w') as f:
        yaml.dump({
            'left': l,
            'top': t,
            'right': r,
            'bottom': b
        }, f)

    # cropped = img[t:b, l:r]
    tmp_params = {
        'left' : l,
        'top' : t,
        'right' : r,
        'bottom' : b
    }
    return tmp_params



ANNOTATIONS = '/mycode/files/annotations/'

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