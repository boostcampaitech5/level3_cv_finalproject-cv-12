
import io
def PIL2Byte(image):
    image_bytes = io.BytesIO()
    image.save(image_bytes, format="JPEG") 
    image_bytes = image_bytes.getvalue()
    return image_bytes