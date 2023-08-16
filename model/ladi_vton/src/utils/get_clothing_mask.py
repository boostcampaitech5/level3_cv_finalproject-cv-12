from rembg import remove
from PIL import Image
import os
from io import BytesIO

# garment, lower_body, upper_body

def main_mask(category, garment_dir, output_mask_dir):
    input_path = os.path.join(garment_dir, f'{category}.jpg')
    print(input_path)

    output_path = os.path.join(output_mask_dir, f'{category}.jpg')
    
    def create_mask_from_png(jpg_file, jpg_mask_file):
        # PNG 파일 열기
        image = Image.open(jpg_file)
        
        image = remove(image)
        
        # output.save(output_path)
        
        # 새로운 이미지 생성 (RGB 모드, 크기는 원본 이미지와 같음)
        mask_image = Image.new("RGB", image.size)

        # 이미지의 너비와 높이
        width, height = image.size

        # 픽셀 데이터 가져오기
        pixel_data = image.load()

        # 마스크 이미지 생성
        for y in range(height):
            for x in range(width):
                # 각 픽셀의 RGB 값과 알파 값 가져오기
                r, g, b, alpha = pixel_data[x, y]

                # alpha 값이 0인 경우 검정색으로, 그렇지 않은 경우 흰색으로 설정
                if alpha == 0:
                    mask_image.putpixel((x, y), (0, 0, 0))
                else:
                    mask_image.putpixel((x, y), (255, 255, 255))

        # JPG 파일로 저장
        mask_image.save(jpg_mask_file)

# if __name__ == "__main__":
#     # PNG 파일 경로와 생성할 JPG 마스크 파일 경로를 지정합니다.
#     input_png_file = "/opt/ml/level3_cv_finalproject-cv-12/backend/app/temp/WOODIE_누끼.png"
#     output_jpg_mask_file = "/opt/ml/level3_cv_finalproject-cv-12/backend/app/temp/output_mask.jpg"

#     # 함수 호출
#     create_mask_from_png(input_png_file, output_jpg_mask_file)
    
    
    create_mask_from_png(input_path, output_path)

def main_mask_fromImageByte(garment_bytes):
    
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

    # JPG 파일로 저장
    return mask_image
    