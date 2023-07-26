import io
import os
from pathlib import Path

import requests
from PIL import Image

import streamlit as st
from app.confirm_button_hack import cache_on_button_press
import base64

# SETTING PAGE CONFIG TO WIDE MODE
ASSETS_DIR_PATH = os.path.join(Path(__file__).parent.parent.parent.parent, "assets")

st.set_page_config(layout="wide")

root_password = 'a'
category_pair = {'Upper':'upper_body', 'Lower':'lower_body', 'Upper & Lower':'upper_lower', 'Dress':'dresses'}

db_dir = '/opt/ml/user_db'

def apply_custom_font(text, font_size=48):
    # 글꼴 로드
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    font_filename = 'NanumSquareB.ttf'
    font_path = os.path.join(parent_dir, "assets", font_filename)

    try:
        with open(font_path, "rb") as f:
            font_data = f.read()
        font_base64 = base64.b64encode(font_data).decode("utf-8")
        font_style = f"font-family: 'CustomFont' ; font-size: {font_size}px;"
        styled_text = f'<div style="{font_style}";>{text}</div>'
        return f'<style>@font-face {{font-family: "CustomFont"; src: url(data:font/ttf;base64,{font_base64})}}</style>{styled_text}'
    except Exception as e:
        st.error(f"Error loading the font: {e}")
        return None

def user_guideline_for_human():

    st.write(' ')
    text1 = """<h6 style=''> 1. 전신 사진을 넣어주세요.  </h6>"""
    text2 = """<h6 style=''> 2. 아래 예시 사진과 같이, 최대한 사진의 위아래 테두리에 맞게 찍어주세요. </h6>"""
    
    st.markdown(text1, unsafe_allow_html=True)
    st.markdown(text2, unsafe_allow_html=True)

def user_guideline_for_garment():

    st.write(' ')
    text1 = """<h5 style=''> 1. 상의, 하의, 상의&하의, 드레스 카테고리를 선택해주세요. </h5>""" #text-align: center;
    text2 = """<h5 style=''> 2. 단일 옷 사진을 넣어주세요. </h5>"""
    
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

def read_image_as_bytes(image_path):
    with open(image_path, "rb") as file:
        image_data = file.read()
    return image_data
## 이미지 리스트에 저장
def append_imgList(uploaded_garment, category):

    garment_bytes = uploaded_garment.getvalue()
    file = [
        ('files', category),
        ('files', (uploaded_garment.name, garment_bytes,
                                    uploaded_garment.type))]
    response = requests.post("http://localhost:8001/add_data", files=file)
    response.raise_for_status() ## 200이 아니면 예외처리

## 저장된 이미지 리스트들을 체크박스와 함께 띄우는 함수 
def show_garments_and_checkboxes(category):

    category_dir = os.path.join(db_dir, 'input/garment', category)
    filenames = os.listdir(category_dir)
    
    num_columns = 3 
    num_rows = (len(filenames) - 1) // num_columns + 1

    # 이미지들을 오른쪽으로 정렬하여 표시하기 위해 컬럼 생성
    cols = st.columns(num_columns)
    for i, filename in enumerate(filenames):
        im_dir = os.path.join(category_dir, filename)
        garment_img = Image.open(im_dir)
        garment_byte = read_image_as_bytes(im_dir)
        # st.image(garment_img, caption=filename[:-4], width=100)
        cols[i % num_columns].image(garment_img, width=100, use_column_width=True, caption=filename[:-4])
        # if st.checkbox(filename[:-4]) :
        #     return True, garment_byte
        # else : 
        #     return False, None
    
    selected_garment = st.selectbox('입을 옷을 선택해주세요.', [f[:-4] for f in filenames])
    return filenames, selected_garment

def md_style():
    st.markdown(
        """
        <style>
        .center-aligned-title {
            text-align: center;
            margin-top: 0rem;
            margin-bottom: 1rem;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <style>
        .custom-button {
            background-color: #3498db;
            color: white;
            font-size: 16px;
            padding: 10px 20px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
        }
        .custom-button:hover {
            background-color: #2980b9;
        }
        .center-aligned-button {
            display: flex;
            justify-content: center;
            margin-bottom: 20px; 

        }
        </style>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <style>
        .center-aligned-header {
            text-align: center;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
    st.markdown(
        """
        <style>
        .custom-column {
            padding: 10px;
            border-radius: 5px;
        }
        .center-column {
            background-color: #e0e0e0; /* 중앙 컬럼의 배경색 지정 */
        }
        .custom-text {
            background-color: #e0e0e0; /* 텍스트의 배경색 지정 */
            padding: 10px;
            border-radius: 5px;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

def main():
    md_style()
    # st.title("d") #🌳나만의 드레스룸🌳
    st.markdown("<h1 class='center-aligned-title'>🌳나만의 드레스룸🌳</h1>", unsafe_allow_html=True)

    with st.container():
        col1, col2, col3 = st.columns([1,1,1])
        files = [0, 0, 0, ('files', 0)]
        is_selected_garment = False
        gen_start = False
        
        with col1:
            st.markdown("<h3 class='center-aligned-header'>상의👚</h3>", unsafe_allow_html=True)

            # user_guideline_for_garment()
            category_list = ['Upper', 'Lower', 'Upper & Lower', 'Dress']
            selected_category = st.selectbox('Choose an category of garment', category_list)
            
            category = category_pair[selected_category]
            print('**category:', category)
            category = 'upper_body'

            if selected_category == 'Upper & Lower':
                uploaded_garment1 = st.file_uploader("Choose an upper image", type=["jpg", "jpeg", "png"])
                uploaded_garment2 = st.file_uploader("Choose an lower image", type=["jpg", "jpeg", "png"])
                # if not uploaded_garment1 and not uploaded_garment2 : 
                #     user_guideline_for_garment()

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

                uploaded_garment = st.file_uploader("추가할 상의를 넣어주세요.", type=["jpg", "jpeg", "png"])

                if uploaded_garment :
                    append_imgList(uploaded_garment, category)

                filenames, selected_upper = show_garments_and_checkboxes(category)
                if selected_upper :
                    is_selected_garment = True
                    files[0] = ('files', category)
                    files[2] = ('files', f'{selected_upper}.jpg')

        with col2:
            
            # st.markdown("<div class='custom-column center-column'>", unsafe_allow_html=True) # 중앙 컬럼에 .center-column 클래스 추가
            # st.markdown("<div class='custom-text'>This is column 2 content.</div>", unsafe_allow_html=True) # 텍스트를 배경색과 함께 출력
            # st.markdown("</div>", unsafe_allow_html=True)

            st.markdown("<h3 class='center-aligned-header'>드레스룸🚪</h3>", unsafe_allow_html=True)
            # st.markdown("</div>", unsafe_allow_html=True)
             # is_checked_garment
            user_guideline_for_human()
            uploaded_target = st.file_uploader("Choose an target image", type=["jpg", "jpeg", "png"])
            
            start_button = st.markdown("<div class='center-aligned-button'><button class='custom-button'>옷 입히기 시작</button></div>", unsafe_allow_html=True)

            if start_button:
                if  uploaded_target and is_selected_garment : 
                    gen_start = True
            
            human_slot = st.empty()
            if uploaded_target:
                target_bytes = uploaded_target.getvalue()
                target_img = Image.open(io.BytesIO(target_bytes))

                human_slot.empty()
                human_slot.image(target_img, caption='Uploaded target image')
                
                files[1] = ('files', (uploaded_target.name, target_bytes,
                            uploaded_target.type))
            else : 
                example_img = Image.open('/opt/ml/level3_cv_finalproject-cv-12/backend/app/utils/example.jpg')
                human_slot.image(example_img, width=300, use_column_width=True, caption='Example of target image')
            
            if gen_start : 
                
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
                
                human_slot.empty()
                human_slot.image(final_img, caption='Final Image', use_column_width=True)


        with col3:  
            st.markdown("<h3 class='center-aligned-header'>하의👖</h3>", unsafe_allow_html=True)
            category = 'lower_body'
            
            uploaded_garment = st.file_uploader("추가할 하의를 넣어주세요.", type=["jpg", "jpeg", "png"])

            if uploaded_garment :
                append_imgList(uploaded_garment, category)

            filenames, selected_upper = show_garments_and_checkboxes(category)
            if selected_upper :
                is_selected_garment = True
                files[0] = ('files', category)
                files[2] = ('files', f'{selected_upper}.jpg')



        # if is_all_uploaded:
        #     with col3:  
        #         st.write(' ')
        #         empty_slot = st.empty()
        #         empty_slot.markdown("<h2 style='text-align: center;'>\nLoading...</h2>", unsafe_allow_html=True)
                
        #         while check_modelLoading() :
        #             pass

        #         import time
        #         t = time.time()
        #         response = requests.post("http://localhost:8001/order", files=files)
        #         response.raise_for_status() ## 200이 아니면 예외처리
        #         print('total processing time: ', time.time() - t)
                
        #         empty_slot.empty()
        #         empty_slot.markdown("<h2 style='text-align: center;'>Here it is !</h2>", unsafe_allow_html=True)

        #         output_ladi_buffer_dir = '/opt/ml/user_db/ladi/buffer'
        #         final_result_dir = output_ladi_buffer_dir
        #         if category =='upper_lower':
        #             final_img = Image.open(os.path.join(final_result_dir, 'lower_body.png'))
        #         else : 
        #             final_img = Image.open(os.path.join(final_result_dir, f'{category}.png'))
                
        #         st.write(' ')
        #         st.write(' ')
        #         st.write(' ')
        #         st.write(' ')
        #         st.write(' ')
        #         st.write(' ')
        #         st.image(final_img, caption='Final Image', use_column_width=True)
                
        #         # option = '선택 안 함'
        #         # down_btn = st.download_button(
        #         #     label='Download Image',
        #         #     data=dehaze_image_bytes,
        #         #     file_name='dehazed_image.jpg',
        #         #     mime='image/jpg',
        #         #     on_click=save_btn_click(option, dehaze_image_bytes)
        #         # )

main()