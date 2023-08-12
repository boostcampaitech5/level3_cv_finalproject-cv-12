from rembg import remove
from PIL import Image
import os

# garment, lower_body, upper_body

def main_mask(category, garment_dir, output_mask_dir):
    input_path = os.path.join(garment_dir, f'{category}.jpg')
    print(input_path)

    output_path = os.path.join(output_mask_dir, f'{category}.jpg')
    
    def create_mask_from_png(jpg_file, jpg_mask_file):
        image = Image.open(jpg_file)
        
        image = remove(image)
        
        
        mask_image = Image.new("RGB", image.size)

        width, height = image.size

        pixel_data = image.load()

        for y in range(height):
            for x in range(width):

                r, g, b, alpha = pixel_data[x, y]

                if alpha == 0:
                    mask_image.putpixel((x, y), (0, 0, 0))
                else:
                    mask_image.putpixel((x, y), (255, 255, 255))

        mask_image.save(jpg_mask_file)
    
    
    create_mask_from_png(input_path, output_path)
    
    
#     output = remove(input)
#     output.save(os.path.join(target_buffer_dir, output_mask_dir))
# target_buffer_dir =  '/opt/ml/user_db/input/buffer/garment'
# main_mask('lower_body', target_buffer_dir)
