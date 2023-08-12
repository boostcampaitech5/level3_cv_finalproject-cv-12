import argparse
import sys

label_map={
    "background": 0,
    "hat": 1,
    "hair": 2,
    "sunglasses": 3,
    "upper_clothes": 4,
    "skirt": 5,
    "pants": 6,
    "dress": 7,
    "belt": 8,
    "left_shoe": 9,
    "right_shoe": 10,
    "head": 11,
    "left_leg": 12,
    "right_leg": 13,
    "left_arm": 14,
    "right_arm": 15,
    "bag": 16,
    "scarf": 17,
}

from PIL import Image, ImageDraw, ImageOps
import PIL
import os
import numpy as np

import matplotlib.pyplot as plt
from time import time


def main_cut_and_paste(category, db_dir, target_name='target.jpg'):

    dataroot = db_dir
    im_name = target_name
    generative_name = 'lower_body.png'
    parse_name = im_name.replace('.jpg', '.png')



    origin_image = Image.open(os.path.join(dataroot, 'input/buffer/target', im_name))
    origin_image = origin_image.resize((384,512))
    origin_np = np.array(origin_image)


    generatived_image = Image.open(os.path.join(dataroot, 'ladi/buffer', f'{category}.png'))
    generatived_np = np.array(generatived_image)


    im_parse = Image.open(os.path.join(dataroot, 'schp/buffer', parse_name))
    im_parse = im_parse.resize((384, 512), Image.NEAREST)
    parse_array = np.array(im_parse)

    parser_mask_changeable = (parse_array == label_map["hair"]).astype(np.float32) + \
                        (parse_array == label_map["head"]).astype(np.float32) + \
                        (parse_array == label_map["sunglasses"]).astype(np.float32) + \
                        (parse_array == label_map["hat"]).astype(np.float32) + \
                        (parse_array == label_map["bag"]).astype(np.float32) + \
                        (parse_array == label_map["scarf"]).astype(np.float32)
                            
    indices = np.where(parser_mask_changeable == 1)


    def overlay_arrays(origin_np, generatived_np, indices):

        overlay_indices = (indices[0], indices[1])
        
        generatived_np[overlay_indices] = origin_np[overlay_indices]
        
        return generatived_np

    result_array = overlay_arrays(origin_np, generatived_np, indices)
    result_array = Image.fromarray(result_array)
    

    
    result_array.save(os.path.join(dataroot, 'ladi/buffer', f'{category}.png'))
