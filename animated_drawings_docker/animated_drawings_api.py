from flask import Flask, send_file
from image_to_annotations import image_to_annotations
from annotations_to_animation import annotations_to_animation
from pathlib import Path
import logging
from pkg_resources import resource_filename

app = Flask(__name__)

@app.route('/ping')
def ping():
    return 'animated_drawings test ping success!!'

@app.route('/get_my_animated_drawings')
def get_my_animated_drawings():
    log_dir = Path('./logs')
    log_dir.mkdir(exist_ok=True, parents=True)
    logging.basicConfig(filename=f'{log_dir}/log.txt', level=logging.DEBUG)

    img_fn = resource_filename(__name__, 'drawings/garlic.png')  
    char_anno_dir = 'garlic_out'
    motion_cfg_fn = resource_filename(__name__, 'config/motion/dab.yaml')    
    retarget_cfg_fn = resource_filename(__name__, 'config/retarget/fair1_ppf.yaml')

    # create the annotations
    image_to_annotations(img_fn, char_anno_dir)
    # create the animation
    annotations_to_animation(char_anno_dir, motion_cfg_fn, retarget_cfg_fn)

    return 'animation success!'

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port='8001')