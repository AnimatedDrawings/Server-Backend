import numpy as np

mock_pose_results = [
    {
        "keypoints": [
            [92.16015625, 96.23828125, 0.8404031991958618],
            [119.89453125, 85.14453125, 0.6275597810745239],
            [64.42578125, 79.59765625, 0.6586964130401611],
            [147.62890625, 99.01171875, 0.7912260293960571],
            [36.69140625, 93.46484375, 0.8299789428710938],
            [111.57421875, 218.26953125, 0.8811711072921753],
            [53.33203125, 212.72265625, 0.9031049013137817],
            [130.98828125, 196.08203125, 0.8813555836677551],
            [36.69140625, 193.30859375, 0.9174546003341675],
            [150.40234375, 173.89453125, 0.8557842969894409],
            [17.27734375, 173.89453125, 0.8439995050430298],
            [94.93359375, 243.23046875, 0.8867484331130981],
            [67.19921875, 240.45703125, 0.8969118595123291],
            [92.16015625, 257.09765625, 0.9074493646621704],
            [67.19921875, 257.09765625, 0.8993232250213623],
            [94.93359375, 273.73828125, 0.8985602259635925],
            [67.19921875, 273.73828125, 0.9380176663398743],
        ]
    },
]

mock_kpts = np.array(mock_pose_results[0]["keypoints"])[:, :2]

mock_skeleton = [
    {"loc": [81, 242], "name": "root", "parent": None},
    {"loc": [81, 242], "name": "hip", "parent": "root"},
    {"loc": [82, 215], "name": "torso", "parent": "hip"},
    {"loc": [92, 96], "name": "neck", "parent": "torso"},
    {"loc": [53, 213], "name": "right_shoulder", "parent": "torso"},
    {"loc": [37, 193], "name": "right_elbow", "parent": "right_shoulder"},
    {"loc": [17, 174], "name": "right_hand", "parent": "right_elbow"},
    {"loc": [112, 218], "name": "left_shoulder", "parent": "torso"},
    {"loc": [131, 196], "name": "left_elbow", "parent": "left_shoulder"},
    {"loc": [150, 174], "name": "left_hand", "parent": "left_elbow"},
    {"loc": [67, 240], "name": "right_hip", "parent": "root"},
    {"loc": [67, 257], "name": "right_knee", "parent": "right_hip"},
    {"loc": [67, 274], "name": "right_foot", "parent": "right_knee"},
    {"loc": [95, 243], "name": "left_hip", "parent": "root"},
    {"loc": [92, 257], "name": "left_knee", "parent": "left_hip"},
    {"loc": [95, 274], "name": "left_foot", "parent": "left_knee"},
]

mock_char_cfg_dict = {
    "skeleton": [
        {"loc": [81, 242], "name": "root", "parent": None},
        {"loc": [81, 242], "name": "hip", "parent": "root"},
        {"loc": [82, 215], "name": "torso", "parent": "hip"},
        {"loc": [92, 96], "name": "neck", "parent": "torso"},
        {"loc": [53, 213], "name": "right_shoulder", "parent": "torso"},
        {"loc": [37, 193], "name": "right_elbow", "parent": "right_shoulder"},
        {"loc": [17, 174], "name": "right_hand", "parent": "right_elbow"},
        {"loc": [112, 218], "name": "left_shoulder", "parent": "torso"},
        {"loc": [131, 196], "name": "left_elbow", "parent": "left_shoulder"},
        {"loc": [150, 174], "name": "left_hand", "parent": "left_elbow"},
        {"loc": [67, 240], "name": "right_hip", "parent": "root"},
        {"loc": [67, 257], "name": "right_knee", "parent": "right_hip"},
        {"loc": [67, 274], "name": "right_foot", "parent": "right_knee"},
        {"loc": [95, 243], "name": "left_hip", "parent": "root"},
        {"loc": [92, 257], "name": "left_knee", "parent": "left_hip"},
        {"loc": [95, 274], "name": "left_foot", "parent": "left_knee"},
    ],
    "height": 284,
    "width": 176,
}
