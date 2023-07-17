from flask import Flask, send_file, request
from image_to_annotations import image_to_annotations
from annotations_to_animation import annotations_to_animation
from pathlib import Path
import logging
from pkg_resources import resource_filename


app = Flask(__name__)

@app.route('/ping')
def ping():
    return 'animated_drawings test ping success!!'

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
@app.route('/image_to_annotations')
def api_image_to_annotations():
    parameter_dict = request.args.to_dict()
    if len(parameter_dict) == 0:
        return 'No parameter'

    path = parameter_dict['path']
    file_name = parameter_dict['file_name']
    extension = parameter_dict['extension']
    img_fn = path + file_name + extension
    out_dir = ANNOTATIONS + file_name
    image_to_annotations(img_fn = img_fn, out_dir = out_dir)

    annotation_info = {
        'path' : ANNOTATIONS + file_name + '/',
        'joint_filename' : 'char_cfg.yaml'
    }

    return annotation_info

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port='8001')