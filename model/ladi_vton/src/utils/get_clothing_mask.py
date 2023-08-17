from rembg import remove
from PIL import Image
import os
from io import BytesIO

# garment, lower_body, upper_body
def main_mask(garment_bytes):
    
    # image = Image.open(jpg_file)
    
    image = Image.open(BytesIO(garment_bytes))
    
    image = remove(image)
    
    mask_image = Image.new("RGB", image.size)
    width, height = image.size

    pixel_data = image.load()

    for y in range(height):
        for x in range(width):
            # 각 픽셀의 RGB 값과 알파 값 가져오기
            r, g, b, alpha = pixel_data[x, y]

            # alpha 값이 0인 경우 검정색으로, 그렇지 않은 경우 흰색으로 설정
            if alpha == 0:
                mask_image.putpixel((x, y), (0, 0, 0))
            else:
                mask_image.putpixel((x, y), (255, 255, 255))

    return mask_image
    