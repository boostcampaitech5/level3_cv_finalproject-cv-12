from fastapi import FastAPI, UploadFile, File
from fastapi.param_functions import Depends
from fastapi.responses import StreamingResponse
from uuid import UUID, uuid4
from typing import List, Union, Optional, Dict, Any
from PIL import Image
import io

# scp setting
import sys, os
sys.path.append('/opt/ml/level3_cv_finalproject-cv-12/model/Self_Correction_Human_Parsing/')
from simple_extractor import main_schp

# openpose
sys.path.append('/opt/ml/level3_cv_finalproject-cv-12/model/pytorch_openpose/')
from extract_keypoint import main_openpose

# ladi
sys.path.append('/opt/ml/level3_cv_finalproject-cv-12/model/ladi_vton')
sys.path.append('/opt/ml/level3_cv_finalproject-cv-12/model/ladi_vton/src')
sys.path.append('/opt/ml/level3_cv_finalproject-cv-12/model/ladi_vton/src/utils')

from get_clothing_mask import main_mask

from inference import main_ladi
from face_cut_and_paste import cut_and_paste

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


sys.path.append('/opt/ml/level3_cv_finalproject-cv-12/backend/app')
from .utils import PIL2Byte

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

def inference_preprocess(target_bytes, garment_bytes, garment_lower_bytes=None):
    # schp  - (1024, 784), (512, 384)
    schp_img = main_schp(target_bytes)

    # openpose 
    keypoint_dict = main_openpose(target_bytes)

    ## garment_mask 형식 - Image
    garment_mask = main_mask(garment_bytes) 
    if garment_lower_bytes is None : 
        return schp_img, keypoint_dict, garment_mask
    else : 
        garment_lower_mask = main_mask(garment_lower_bytes) 
        
        return schp_img, keypoint_dict, garment_mask, garment_lower_mask

# post!!
@app.post("/order", description="주문을 요청합니다")
async def make_order(files: List[UploadFile] = File(...)):

    input_dir = f'{user_name}/input'

    # category : files[0], target:files[1], garment:files[2]
    byte_string = await files[0].read()
    string_io = io.BytesIO(byte_string)
    category = string_io.read().decode('utf-8')

    ## category가 upper & lower일 경우
    target_bytes = await files[1].read()

    gcs.upload_blob(target_bytes, f'{input_dir}/buffer/target/target.jpg')

    if category == 'upper_lower': 
        garment_upper_bytes = await files[2].read()
        garment_lower_bytes = await files[3].read()
        
        schp_img, keypoint_dict, garment_upper_mask, garment_lower_mask = inference_preprocess(target_bytes, garment_upper_bytes, garment_lower_bytes)
        ladi_img = main_ladi('upper_body', target_bytes, schp_img, keypoint_dict, garment_upper_bytes, garment_upper_mask, ladi_models)
        ladi_bytes = PIL2Byte(ladi_img)
        ladi_img = main_ladi('lower_body', ladi_bytes, schp_img, keypoint_dict, garment_lower_bytes, garment_lower_mask, ladi_models)
        finalResult_img = cut_and_paste(target_bytes, ladi_img, schp_img)


    else : 
        ## file로 전송됐을 때
        garment_bytes = await files[2].read()

        schp_img, keypoint_dict, garment_mask = inference_preprocess(target_bytes, garment_bytes)
        ladi_img = main_ladi(category, target_bytes, schp_img, keypoint_dict, garment_bytes, garment_mask, ladi_models)
        finalResult_img = cut_and_paste(target_bytes, ladi_img, schp_img)

    finalResult_bytes = PIL2Byte(finalResult_img)
    gcs.upload_blob(finalResult_bytes, f'{input_dir}/ladi/buffer/final.jpg')

    return StreamingResponse(io.BytesIO(finalResult_bytes), media_type="image/jpg")