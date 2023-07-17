import io
import os
from pathlib import Path

import requests
from PIL import Image

import streamlit as st
from app.confirm_button_hack import cache_on_button_press

# SETTING PAGE CONFIG TO WIDE MODE
ASSETS_DIR_PATH = os.path.join(Path(__file__).parent.parent.parent.parent, "assets")

st.set_page_config(layout="wide")

root_password = 'a'


def main():
    st.title("Welcome to VTON World :)")
    
    with st.container():
        col1, col2, col3 = st.columns([1,1,1])
        
        with col1:
            st.header("Human")
            uploaded_target = st.file_uploader("Choose an target image", type=["jpg", "jpeg", "png"])
            
            if uploaded_target:
                target_bytes = uploaded_target.getvalue()
                target_img = Image.open(io.BytesIO(target_bytes))

                st.image(target_img, caption='Uploaded target Image')
        
        with col2:
            st.header("Cloth")
            uploaded_garment = st.file_uploader("Choose an garment image", type=["jpg", "jpeg", "png"])

            if uploaded_garment:
                # st.spinner("dehazing now...")
                
                garment_bytes = uploaded_garment.getvalue()
                garment_img = Image.open(io.BytesIO(garment_bytes))

                st.image(garment_img, caption='Uploaded garment Image')
                
        with col3:  
            st.header("Result")
        if uploaded_target and uploaded_garment:
            files = [
                ('files', (uploaded_target.name, target_bytes,
                        uploaded_target.type))
                ,
                ('files', (uploaded_garment.name, garment_bytes,
                        uploaded_garment.type))
            ]
            
            with col3:  
                st.write(' ')
                empty_slot = st.empty()
                empty_slot.markdown("<h2 style='text-align: center;'>\nLoading...</h2>", unsafe_allow_html=True)

                response = requests.post("http://localhost:8001/order", files=files)
                empty_slot.empty()
                empty_slot.markdown("<h2 style='text-align: center;'>Here it is !</h2>", unsafe_allow_html=True)

                category = 'lower_body'
                output_ladi_buffer_dir = '/opt/ml/user_db/ladi/buffer'
                final_result_dir = output_ladi_buffer_dir
                final_img = Image.open(os.path.join(final_result_dir, f'{category}.png'))
                
                st.write(' ')
                st.write(' ')
                st.write(' ')
                st.write(' ')
                st.write(' ')
                st.write(' ')
                st.image(final_img, caption='Final Image', use_column_width=True)
                
                # option = '선택 안 함'
                # down_btn = st.download_button(
                #     label='Download Image',
                #     data=dehaze_image_bytes,
                #     file_name='dehazed_image.jpg',
                #     mime='image/jpg',
                #     on_click=save_btn_click(option, dehaze_image_bytes)
                # )

# @cache_on_button_press('Authenticate')
# def authenticate(password) -> bool:
#     return password == root_password
# password = st.text_input('password', type="password")
# if authenticate(password):
#     st.success('You are authenticated!')
#     main()
# else:
#     st.error('The password is invalid.')


main()
