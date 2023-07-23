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

category_pair = {'Upper':'upper_body', 'Lower':'lower_body', 'Upper & Lower':'upper_lower', 'Dress':'dresses'}

def user_guideline_for_human():

    st.write(' ')
    text1 = """<h4 style='text-align: center;'> 전신 사진을 넣어주세요.  </h4>"""
    text1 = """<h4 style='text-align: center;'> 최대한 머리와 발끝을  </h4>"""
    text2 = """<h4 style='text-align: center;'> 사진의 위아래 테두리에 맞게 찍어주세요! </h4>"""
    
    st.markdown(text1, unsafe_allow_html=True)
    st.markdown(text2, unsafe_allow_html=True)

def user_guideline_for_garment():

    st.write(' ')
    text1 = """<h4 style='text-align: center;'> 상의, 하의, 드레스 카테고리를 선택 후, </h4>"""
    text2 = """<h4 style='text-align: center;'> 단일 옷 사진을 넣어주세요 !  </h4>"""
    
    st.markdown(text1, unsafe_allow_html=True)
    st.markdown(text2, unsafe_allow_html=True)

def check_modelLoading():
    api_url = "http://localhost:8001/get_boolean"
    is_modelLoading = True
    try:
        response = requests.get(api_url)
        if response.status_code == 200:
            data = response.json()
            is_modelLoading = data["is_modelLoading"]
    except requests.exceptions.RequestException as e:
        pass
    return is_modelLoading

def main():
    st.title("Welcome to VTON World :)")
    is_all_uploaded = False
    with st.container():
        col1, col2, col3 = st.columns([1,1,1])
        
        with col1:
            st.header("Human")
            
            # target_img = Image.open('/opt/ml/user_db/input/buffer/target/target.jpg')
            uploaded_target = st.file_uploader("Choose an target image", type=["jpg", "jpeg", "png"])

            if uploaded_target:
                target_bytes = uploaded_target.getvalue()
                target_img = Image.open(io.BytesIO(target_bytes))

                st.image(target_img, caption='Uploaded target Image')
            else : 
                user_guideline_for_human()
        
        with col2:
            st.header("Cloth")

            category_list = ['Upper', 'Lower', 'Upper & Lower', 'Dress']
            selected_category = st.selectbox('Choose an category of garment', category_list)
            # uploaded_garment = Image.open('/opt/ml/user_db/input/buffer/garment/garment.jpg')
            
            category = category_pair[selected_category]
            print('**category:', category)

            if selected_category == 'Upper & Lower':
                uploaded_garment1 = st.file_uploader("Choose an upper image", type=["jpg", "jpeg", "png"])
                uploaded_garment2 = st.file_uploader("Choose an lower image", type=["jpg", "jpeg", "png"])
                print(uploaded_garment1, uploaded_garment2)
                if not uploaded_garment1 and not uploaded_garment2 : 
                    user_guideline_for_garment()

                col2_1, col2_2, = st.columns([1,1])
                with col2_1:
                    if uploaded_garment1:
                        garment_bytes1 = uploaded_garment1.getvalue()
                        garment_img1 = Image.open(io.BytesIO(garment_bytes1))
                        st.image(garment_img1, caption='Uploaded upper Image')
                
                with col2_2:
                    if uploaded_garment2:
                        garment_bytes2 = uploaded_garment2.getvalue()
                        garment_img2 = Image.open(io.BytesIO(garment_bytes2))
                        st.image(garment_img2, caption='Uploaded lower Image')

                if uploaded_target and uploaded_garment1 and uploaded_garment2:
                    is_all_uploaded = True
                    files = [
                        ('files', category),
                        ('files', (uploaded_target.name, target_bytes,
                                uploaded_target.type)),
                        ('files', (uploaded_garment1.name, garment_bytes1,
                                uploaded_garment1.type)),
                        ('files', (uploaded_garment2.name, garment_bytes2,
                                uploaded_garment2.type))
                    ]


            else : 
                uploaded_garment = st.file_uploader("Choose an garment image", type=["jpg", "jpeg", "png"])

                if not uploaded_garment : 
                    user_guideline_for_garment()

                if uploaded_garment:
                    garment_bytes = uploaded_garment.getvalue()
                    garment_img = Image.open(io.BytesIO(garment_bytes))
                    st.image(garment_img, caption='Uploaded garment Image')

                if uploaded_target and uploaded_garment :
                    is_all_uploaded = True
                    files = [
                        ('files', category),
                        ('files', (uploaded_target.name, target_bytes,
                                uploaded_target.type)),
                        ('files', (uploaded_garment.name, garment_bytes,
                                uploaded_garment.type)),
                    ]

        with col3:  
            st.header("Result")


        if is_all_uploaded:
            
            with col3:  
                st.write(' ')
                empty_slot = st.empty()
                empty_slot.markdown("<h2 style='text-align: center;'>\nLoading...</h2>", unsafe_allow_html=True)
                
                while check_modelLoading() :
                    pass

                import time
                t = time.time()
                response = requests.post("http://localhost:8001/order", files=files)
                response.raise_for_status() ## 200이 아니면 예외처리
                print('total processing time: ', time.time() - t)
                
                empty_slot.empty()
                empty_slot.markdown("<h2 style='text-align: center;'>Here it is !</h2>", unsafe_allow_html=True)

                output_ladi_buffer_dir = '/opt/ml/user_db/ladi/buffer'
                final_result_dir = output_ladi_buffer_dir
                if category =='upper_lower':
                    final_img = Image.open(os.path.join(final_result_dir, 'lower_body.png'))
                else : 
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

main()