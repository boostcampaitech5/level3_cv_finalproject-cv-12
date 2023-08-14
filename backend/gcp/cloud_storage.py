# Python built-in modules
import io
import yaml

# Google
from google.cloud import storage
from google.oauth2 import service_account

# datetime
from datetime import datetime, timedelta


class GCSUploader:
    def __init__(self, gcp_config: dict):
        credentials_path = gcp_config["credentials_path"]
        self.bucket_name = gcp_config["cloud_storage"]["bucket_name"]

        credentials = service_account.Credentials.from_service_account_file(
            credentials_path
        )
        self.client = storage.Client(credentials=credentials)

    def upload_blob(self, source_file_data: bytes, destination_blob_name: str) -> str:
        bucket = self.client.get_bucket(self.bucket_name)
        blob = bucket.blob(destination_blob_name)

        file_obj = io.BytesIO(source_file_data)
        blob.upload_from_file(file_obj)

        # permanent_url = f"https://storage.cloud.google.com/{self.bucket_name}/{destination_blob_name}"

        user_expiration_time = datetime.now() + timedelta(days=30)
        user_url = blob.generate_signed_url(expiration=user_expiration_time)

        print(f"File uploaded to {destination_blob_name}.")

        return user_url

    # Uploads image to GCS and returns the URL
    def save_image_to_gcs(self, urls: list) -> str:
        image_urls = []
        for i, (byte_arr, url_name) in enumerate(urls):
            url = self.upload_blob(byte_arr, url_name)
            image_urls.append(url)

        return image_urls
    
    def list_images_in_folder(self, folder_name):
        bucket = self.client.get_bucket(self.bucket_name)
        blobs = bucket.list_blobs(prefix=folder_name)

        image_names = [blob.name for blob in blobs if blob.name.lower().endswith(('.jpg', '.jpeg', '.png', '.gif'))]
        return image_names

def load_gcp_config_from_yaml(yaml_path):
    with open(yaml_path, 'r') as yaml_file:
        gcp_config = yaml.safe_load(yaml_file)
    return gcp_config

def read_image_as_bytes(image_path):
    with open(image_path, "rb") as image_file:
        image_bytes = image_file.read()
    return image_bytes

# gcp_config.yaml 파일에서 정보를 읽어옵니다.
# gcp_config = load_gcp_config_from_yaml("../config/gcs.yaml")

# # GCSUploader 클래스의 인스턴스를 생성합니다.
# gcs_uploader = GCSUploader(gcp_config)

# # 이미지 데이터와 함께 GCSUploader 클래스를 사용하여 이미지를 업로드하고 URL을 가져옵니다.
# image_path = "/opt/ml/user_db/input/garment/lower_body/18_1.jpg"
# image_data_list = [(read_image_as_bytes(image_path), 'hi/18_1.jpg' )]
# uploaded_image_urls = gcs_uploader.save_image_to_gcs(image_data_list)

# # 업로드된 이미지 URL들을 출력합니다.
# for i, url in enumerate(uploaded_image_urls, start=1):
#     print(f"Uploaded Image {i} URL: {url}")