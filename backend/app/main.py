from fastapi import FastAPI, UploadFile, File
from fastapi.param_functions import Depends
from pydantic import BaseModel, Field
from uuid import UUID, uuid4
from typing import List, Union, Optional, Dict, Any
from datetime import datetime
from PIL import Image
import io

# scp setting
import sys, os
sys.path.append('/opt/ml/level3_cv_finalproject-cv-12/model/Self_Correction_Human_Parsing/')
from simple_extractor import main_schp, main_schp_from_image_byte

# openpose
sys.path.append('/opt/ml/level3_cv_finalproject-cv-12/model/pytorch_openpose/')
from extract_keypoint import main_openpose

# ladi
sys.path.append('/opt/ml/level3_cv_finalproject-cv-12/model/ladi_vton')
sys.path.append('/opt/ml/level3_cv_finalproject-cv-12/model/ladi_vton/src')
sys.path.append('/opt/ml/level3_cv_finalproject-cv-12/model/ladi_vton/src/utils')

from get_clothing_mask import main_mask

from inference import main_ladi
from face_cut_and_paste import main_cut_and_paste

import torch
from accelerate import Accelerator
from diffusers import DDIMScheduler
from diffusers.utils import check_min_version
from diffusers.utils.import_utils import is_xformers_available
from tqdm import tqdm
from transformers import CLIPTextModel, CLIPTokenizer, CLIPVisionModelWithProjection, AutoProcessor
from models.AutoencoderKL import AutoencoderKL
import shutil

sys.path.append('/opt/ml/level3_cv_finalproject-cv-12/backend/gcp')
from cloud_storage import GCSUploader, load_gcp_config_from_yaml

app = FastAPI()
ladi_models = None

db_dir = '/opt/ml/user_db'

gcp_config = load_gcp_config_from_yaml("/opt/ml/level3_cv_finalproject-cv-12/backend/config/gcs.yaml")
gcs = GCSUploader(gcp_config)
user_name = 'hi'

@app.post("/add_data", description="데이터 저장")
async def add_garment_to_db(files: List[UploadFile] = File(...)):
    byte_string = await files[0].read() ##await 
    string_io = io.BytesIO(byte_string) 
    category = string_io.read().decode('utf-8')
    
    print('category in main', category)

    garment_bytes = await files[1].read() ##await
    garment_name = files[1].filename  
    print('!!!! garment_name', garment_name)
    garment_image = Image.open(io.BytesIO(garment_bytes))
    garment_image = garment_image.convert("RGB")
    
    gcs.upload_blob(garment_bytes, os.path.join(user_name, 'input/garment', category, f'{garment_name}'))
    # garment_image.save(os.path.join(db_dir, 'input/garment', category, f'{garment_name}'))

def read_image_as_bytes(image_path):
    with open(image_path, "rb") as file:
        image_data = file.read()
    return image_data

@app.get("/get_db/{category}") 
async def get_DB(category: str) :
    category_dir = os.path.join(db_dir, 'input/garment', category)
    garment_db_bytes = {}
    for filename in os.listdir(category_dir):
        garment_id = filename[:-4]
        garment_byte = read_image_as_bytes(os.path.join(category_dir, filename))
        garment_db_bytes[garment_id] = garment_byte
    return garment_db_bytes

def load_ladiModels():
    pretrained_model_name_or_path = "stabilityai/stable-diffusion-2-inpainting"

    # Setup accelerator and device.
    mixed_precision = "fp16"
    accelerator = Accelerator(mixed_precision=mixed_precision)
    device = accelerator.device
    # Load scheduler, tokenizer and models.
    val_scheduler = DDIMScheduler.from_pretrained(pretrained_model_name_or_path, subfolder="scheduler")
    val_scheduler.set_timesteps(50, device=device)
    text_encoder = CLIPTextModel.from_pretrained(pretrained_model_name_or_path, subfolder="text_encoder")
    vae = AutoencoderKL.from_pretrained(pretrained_model_name_or_path, subfolder="vae")
    vision_encoder = CLIPVisionModelWithProjection.from_pretrained("laion/CLIP-ViT-H-14-laion2B-s32B-b79K")
    processor = AutoProcessor.from_pretrained("laion/CLIP-ViT-H-14-laion2B-s32B-b79K")
    tokenizer = CLIPTokenizer.from_pretrained(pretrained_model_name_or_path, subfolder="tokenizer")

    # Load the trained models from the hub
    unet = torch.hub.load(repo_or_dir='miccunifi/ladi-vton', source='github', model='extended_unet', dataset="dresscode")
    emasc = torch.hub.load(repo_or_dir='miccunifi/ladi-vton', source='github', model='emasc', dataset="dresscode")
    inversion_adapter = torch.hub.load(repo_or_dir='miccunifi/ladi-vton', source='github', model='inversion_adapter', dataset="dresscode")
    tps, refinement = torch.hub.load(repo_or_dir='miccunifi/ladi-vton', source='github', model='warping_module', dataset="dresscode")

    # Cast to weight_dtype
    weight_dtype = torch.float32
    if mixed_precision == 'fp16':
        weight_dtype = torch.float16

    text_encoder.to(device, dtype=weight_dtype)
    vae.to(device, dtype=weight_dtype)
    emasc.to(device, dtype=weight_dtype)
    inversion_adapter.to(device, dtype=weight_dtype)
    unet.to(device, dtype=weight_dtype)
    tps.to(device, dtype=weight_dtype)
    refinement.to(device, dtype=weight_dtype)
    vision_encoder.to(device, dtype=weight_dtype)

    global ladi_models
    ladi_models = (val_scheduler, text_encoder,vae , vision_encoder ,processor ,tokenizer ,unet ,emasc ,inversion_adapter, tps ,refinement)

    return None 

is_modelLoading = True
load_ladiModels()
is_modelLoading = False

@app.get("/get_boolean")
async def get_boolean():
    global is_modelLoading
    return {"is_modelLoading": is_modelLoading}

def inference_allModels(target_bytes, garment_bytes, category, db_dir):
    
    input_dir = os.path.join(db_dir, 'input')
    # schp  - (1024, 784), (512, 384)
    target_buffer_dir = os.path.join(input_dir, 'buffer/target')
    # main_schp(target_buffer_dir)
    schp_img = main_schp_from_image_byte(target_bytes)
    schp_img.save('./schp.png')
    
    exit()
    # openpose 
    output_openpose_buffer_dir = os.path.join(db_dir, 'openpose/buffer')
    os.makedirs(output_openpose_buffer_dir, exist_ok=True)
    main_openpose(target_buffer_dir, output_openpose_buffer_dir)
    # /opt/ml/user_db/mask/buffer
    # mask 
    garment_dir = os.path.join(input_dir, 'buffer/garment')
    output_mask_dir = os.path.join(db_dir, 'mask/buffer')
    os.makedirs(output_mask_dir, exist_ok=True)
    main_mask(category, garment_dir, output_mask_dir) 

    # ladi-vton 
    output_ladi_buffer_dir = os.path.join(db_dir, 'ladi/buffer')
    os.makedirs(output_ladi_buffer_dir, exist_ok=True)

    main_ladi(category, db_dir, output_ladi_buffer_dir, ladi_models)
    main_cut_and_paste(category, db_dir)

def inference_ladi(category, db_dir, target_name='target.jpg'):
    input_dir = os.path.join(db_dir, 'input')
    garment_dir = os.path.join(input_dir, 'buffer/garment')
    output_mask_dir = os.path.join(db_dir, 'mask/buffer')
    main_mask(category, garment_dir, output_mask_dir) 

    # ladi-vton 
    output_ladi_buffer_dir = os.path.join(db_dir, 'ladi/buffer')
    os.makedirs(output_ladi_buffer_dir, exist_ok=True)
    
    main_ladi(category, db_dir, output_ladi_buffer_dir, ladi_models, target_name)
    main_cut_and_paste(category, db_dir, target_name)

# post!!
@app.post("/order", description="주문을 요청합니다")
async def make_order(files: List[UploadFile] = File(...)):

    # input_dir = '/opt/ml/user_db/input/'
    input_dir = f'{user_name}/input'

    # category : files[0], target:files[1], garment:files[2]
    byte_string = await files[0].read()
    string_io = io.BytesIO(byte_string)
    category = string_io.read().decode('utf-8')

    ## category가 upper & lower일 경우
    target_bytes = await files[1].read()

    target_image = Image.open(io.BytesIO(target_bytes))
    target_image = target_image.convert("RGB")

    os.makedirs(f'{input_dir}/buffer', exist_ok=True)
    # target_image.save(f'{input_dir}/buffer/target/target.jpg')

    gcs.upload_blob(target_bytes, f'{input_dir}/buffer/target/target.jpg')

    if category == 'upper_lower': 
        # garment_upper_bytes = await files[2].read()
        # garment_lower_bytes = await files[3].read()
        
        # garment_upper_image = Image.open(io.BytesIO(garment_upper_bytes))
        # garment_upper_image = garment_upper_image.convert("RGB")
        # garment_lower_image = Image.open(io.BytesIO(garment_lower_bytes))
        # garment_lower_image = garment_lower_image.convert("RGB")

        # # garment_upper_image.save(f'{input_dir}/upper_body.jpg')
        # garment_upper_image.save(f'{input_dir}/buffer/garment/upper_body.jpg')
        # # garment_lower_image.save(f'{input_dir}/lower_body.jpg')
        # garment_lower_image.save(f'{input_dir}/buffer/garment/lower_body.jpg')


        ## string으로 전송됐을 때(filename)
        string_upper_bytes = await files[2].read()
        string_lower_bytes = await files[3].read()
        string_io_upper = io.BytesIO(string_upper_bytes)
        string_io_lower = io.BytesIO(string_lower_bytes)
        filename_upper = string_io_upper.read().decode('utf-8')
        filename_lower = string_io_lower.read().decode('utf-8')

        garment_image_upper = Image.open(os.path.join(db_dir, 'input/garment', 'upper_body', filename_upper))
        garment_image_lower = Image.open(os.path.join(db_dir, 'input/garment', 'lower_body', filename_lower))
        garment_image_upper.save(f'{input_dir}/buffer/garment/upper_body.jpg')
        garment_image_lower.save(f'{input_dir}/buffer/garment/lower_body.jpg')

        
        inference_allModels('upper_body', db_dir)
        shutil.copy(os.path.join(db_dir, 'ladi/buffer', 'upper_body.png'), f'{input_dir}/buffer/target/upper_body.jpg')
        inference_ladi('lower_body', db_dir, target_name='upper_body.jpg')


    else : 
        ## file로 전송됐을 때

        garment_bytes = await files[2].read()
        garment_image = Image.open(io.BytesIO(garment_bytes))
        garment_image = garment_image.convert("RGB")

        ## string으로 전송됐을 때(filename)
        # byte_string = await files[2].read()
        # string_io = io.BytesIO(byte_string)
        # filename = string_io.read().decode('utf-8')

        # garment_image = Image.open(os.path.join(db_dir, 'input/garment', category, filename))
        # garment_image.save(f'{input_dir}/buffer/garment/{category}.jpg')

        gcs.upload_blob(garment_bytes, f'{input_dir}/buffer/garment/{category}.jpg')

        inference_allModels(target_bytes, garment_bytes, category, user_name)

    return None