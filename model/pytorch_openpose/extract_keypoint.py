import cv2
import matplotlib.pyplot as plt
import copy
import numpy as np

from src import model
from src import util
from src.body import Body
from src.hand import Hand

import os

import json

# TEST_IMAGE = '/opt/ml/dataset/ganddddi/sw2_0.jpg'
# OUTPUT_JSON = '/opt/ml/pytorch-openpose/output/sw2_0_hi.json'

# target_image 512, 384
def main_openpose(target_buffer_dir, output_buffer_dir):
    
    img_name = 'target.jpg'
    test_image = os.path.join(target_buffer_dir , img_name)
    
    # Body, Hand model load
    body_estimation = Body('/opt/ml/checkpoints/body_pose_model.pth')
    # hand_estimation = Hand('model/hand_pose_model.pth')


    # image read
    # test_image = test_image
    oriImg = cv2.imread(test_image)  # B,G,R order
    oriImg = cv2.resize(oriImg, (384, 512)) # resize

    # body_estimation foreward
    candidate, subset = body_estimation(oriImg)

    while True:
        if len(candidate) == 18:
            break
        elif len(candidate) > 18:
            candidate = candidate[:-1]
        elif len(candidate) < 18:
            candidate = list(candidate)
            candidate.append(np.array([-1.0, -1.0, 0.0, -1.0]))
            candidate = np.array(candidate)

    json_dict = {
        'keypoints' : candidate.tolist()
    }

    # json 파일 저장
    with open(f'{output_buffer_dir}/{img_name[:-4]}.json', 'w') as f:
        json.dump(json_dict, f, indent=4)

