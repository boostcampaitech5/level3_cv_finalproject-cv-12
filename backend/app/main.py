from fastapi import FastAPI, UploadFile, File
from fastapi.param_functions import Depends
from pydantic import BaseModel, Field
from uuid import UUID, uuid4
from typing import List, Union, Optional, Dict, Any

from datetime import datetime

from app.model import MyEfficientNet, get_model, get_config, predict_from_image_byte
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
from inference import main_ladi



# sys.path.append('/opt/ml/level3_cv_finalproject-cv-12/model')
# print('sys.path:', sys.path)
# from Self_Correction_Human_Parsing.simple_extractor import main_schp
# from pytorch_openpose.extract_keypoint import main_openpose
# from ladi_vton.src.inference import main_ladi
app = FastAPI()

orders = []


@app.get("/")
def hello_world():
    return {"hello": "world"}

class Product(BaseModel):
    name: str
    price: float
    result: Optional[List]

class Order(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    products: List[Product] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    @property
    def bill(self):
        return sum([product.price for product in self.products])

    def add_product(self, product: Product):
        if product.id in [existing_product.id for existing_product in self.products]:
            return self

        self.products.append(product)
        self.updated_at = datetime.now()
        return self


class OrderUpdate(BaseModel):
    products: List[Product] = Field(default_factory=list)


class InferenceImageProduct(Product):
    name: str = "inference_image_product"
    price: float = 100.0
    result: Optional[List]


@app.get("/order", description="주문 리스트를 가져옵니다")
async def get_orders() -> List[Order]:
    return orders


@app.get("/order/{order_id}", description="Order 정보를 가져옵니다")
async def get_order(order_id: UUID) -> Union[Order, dict]:
    order = get_order_by_id(order_id=order_id)
    if not order:
        return {"message": "주문 정보를 찾을 수 없습니다"}
    return order


def get_order_by_id(order_id: UUID) -> Optional[Order]:
    return next((order for order in orders if order.id == order_id), None)

def convert_png_to_jpg(png_file, jpg_file):
    # PNG 파일 열기
    image = Image.open(png_file)

    # JPG로 변환하기
    image = image.convert("RGB")
    image.save(jpg_file, "JPEG")

# post!!
@app.post("/order", description="주문을 요청합니다")
async def make_order(files: List[UploadFile] = File(...),
#  def make_order(files: List[UploadFile] = File(...),
                     model: MyEfficientNet = Depends(get_model),
                     config: Dict[str, Any] = Depends(get_config)):
    products = []

    # target:files[0], garment:files[1]

    target_bytes = await files[0].read()
    garment_bytes = await files[1].read()
    
    # TODO image byte 
    target_image = Image.open(io.BytesIO(target_bytes))
    target_image = target_image.convert("RGB")

    garment_image = Image.open(io.BytesIO(garment_bytes))
    garment_image = garment_image.convert("RGB")

    input_dir = '/opt/ml/user_db/input/'

    os.makedirs(f'{input_dir}/buffer', exist_ok=True)

    target_image.save(f'{input_dir}/target.jpg')
    target_image.save(f'{input_dir}/buffer/target/target.jpg')

    garment_image.save(f'{input_dir}/garment.jpg')
    garment_image.save(f'{input_dir}/buffer/garment/garment.jpg')

    # schp  - (1024, 784), (512, 384)
    target_buffer_dir = f'{input_dir}/buffer/target'
    main_schp(target_buffer_dir)


    
    # openpose 
    output_openpose_buffer_dir = '/opt/ml/user_db/openpose/buffer'
    os.makedirs(output_openpose_buffer_dir, exist_ok=True)
    main_openpose(target_buffer_dir, output_openpose_buffer_dir)
    
    # ladi-vton 
    output_ladi_buffer_dir = '/opt/ml/user_db/ladi/buffer'
    db_dir = '/opt/ml/user_db'
    os.makedirs(output_ladi_buffer_dir, exist_ok=True)
    main_ladi(db_dir, output_ladi_buffer_dir)

    
    inference_result = predict_from_image_byte(model=model, image_bytes=image_bytes, config=config)
    product = InferenceImageProduct(result=inference_result)
    products.append(product)


    new_order = Order(products=products)
    orders.append(new_order)
    return new_order


def update_order_by_id(order_id: UUID, order_update: OrderUpdate) -> Optional[Order]:
    """
    Order를 업데이트 합니다

    Args:
        order_id (UUID): order id
        order_update (OrderUpdate): Order Update DTO

    Returns:
        Optional[Order]: 업데이트 된 Order 또는 None
    """
    existing_order = get_order_by_id(order_id=order_id)
    if not existing_order:
        return

    updated_order = existing_order.copy()
    for next_product in order_update.products:
        updated_order = existing_order.add_product(next_product)

    return updated_order


@app.patch("/order/{order_id}", description="주문을 수정합니다")
async def update_order(order_id: UUID, order_update: OrderUpdate):
    updated_order = update_order_by_id(order_id=order_id, order_update=order_update)

    if not updated_order:
        return {"message": "주문 정보를 찾을 수 없습니다"}
    return updated_order


@app.get("/bill/{order_id}", description="계산을 요청합니다")
async def get_bill(order_id: UUID):
    found_order = get_order_by_id(order_id=order_id)
    if not found_order:
        return {"message": "주문 정보를 찾을 수 없습니다"}
    return found_order.bill
