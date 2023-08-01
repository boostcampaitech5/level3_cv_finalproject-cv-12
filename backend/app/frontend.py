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


# st.set_page_config(layout="wide")

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
    text3 = """<h6 style=''> 2. 입을 옷을 선택해주세요. </h6>"""
    text4 = """<h6 style=''> 3. '옷 입히기 시작' 버튼을 눌러주세요. </h6>"""
    
    st.markdown(text1, unsafe_allow_html=True)
    st.markdown(text3, unsafe_allow_html=True)
    st.markdown(text4, unsafe_allow_html=True)

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
    filenames_ = [None]
    filenames_.extend([f[:-4] for f in filenames])
    selected_garment = st.selectbox('입을 옷을 선택해주세요.', filenames_, index=0)
    print('selected_garment', selected_garment)

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
        is_selected_upper = False
        is_selected_lower = False
        is_selected_dress = False
        gen_start = False

        with col1:
            st.markdown("<h3 class='center-aligned-header'>상의👚</h3>", unsafe_allow_html=True)
            # user_guideline_for_garment()
            category = 'upper_body'

            uploaded_garment = st.file_uploader("추가할 상의를 넣어주세요.", type=["jpg", "jpeg", "png"])

            if uploaded_garment :
                append_imgList(uploaded_garment, category)

            filenames, selected_upper = show_garments_and_checkboxes(category)
            if selected_upper :
                is_selected_upper = True
                files[2] = ('files', f'{selected_upper}.jpg')
            print('selected_upper', selected_upper)

        with col3:  
            
            st.markdown("<h3 class='center-aligned-header'>하의👖</h3>", unsafe_allow_html=True)
            category = 'lower_body'
            
            uploaded_garment = st.file_uploader("추가할 하의를 넣어주세요.", type=["jpg", "jpeg", "png"])

            if uploaded_garment :
                append_imgList(uploaded_garment, category)

            filenames, selected_lower = show_garments_and_checkboxes(category)
            if selected_lower :
                is_selected_lower = True
                files[3] = ('files', f'{selected_lower}.jpg')

            st.write(' ')
            st.write(' ')
            st.markdown("<h3 class='center-aligned-header'>드레스👗</h3>", unsafe_allow_html=True)
            category = 'dresses'
            
            uploaded_garment = st.file_uploader("추가할 드레스를 넣어주세요.", type=["jpg", "jpeg", "png"])

            if uploaded_garment :
                append_imgList(uploaded_garment, category)

            filenames, selected_dress = show_garments_and_checkboxes(category)
            if selected_dress :
                is_selected_dress = True
                files[2] = ('files', f'{selected_dress}.jpg')
            print('is_selected_lower', is_selected_lower)
            print('is_selected_dress', is_selected_dress)


        with col2:
            st.markdown("<h3 class='center-aligned-header'>드레스룸🚪</h3>", unsafe_allow_html=True)

            uploaded_target = st.file_uploader("전신 사진을 넣어주세요.", type=["jpg", "jpeg", "png"])
            user_guideline_for_human()
            
            # start_button = st.markdown("<div class='center-aligned-button'><button class='custom-button'>옷 입히기 시작</button></div>", unsafe_allow_html=True)
            start_button = st.button("옷 입히기 시작", use_container_width=True)

            human_slot = st.empty()
            if uploaded_target:
                target_bytes = uploaded_target.getvalue()
                target_img = Image.open(io.BytesIO(target_bytes))

                human_slot.empty()
                human_slot.image(target_img)
                
            # else : 
                
            #     example_img = Image.open('/opt/ml/level3_cv_finalproject-cv-12/backend/app/utils/example.jpg')
            #     human_slot.image(example_img, width=300, use_column_width=True, caption='Example of target image')

            print('start_button', start_button)
            if start_button and uploaded_target:
                if is_selected_upper and is_selected_lower  : 
                    gen_start = True
                    category = 'upper_lower'
                    
                elif is_selected_upper : 
                    print('catogory upperrr')
                    gen_start = True
                    category = 'upper_body'
                elif is_selected_lower : 
                    gen_start = True
                    category = 'lower_body'
                    files[2] = files[3] ## lower가 3index에 저장됨, upper&lower가 아닐 경우엔 2로 저장
                elif is_selected_dress : 
                    gen_start = True
                    category = 'dresses'
                else : 
                    gen_start = False

                files[0] = ('files', category)
                files[1] = ('files', (uploaded_target.name, target_bytes,
                            uploaded_target.type))
                print('category', category)
                print('files2', files[2])
                print('files3', files[3])

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

                
                is_selected_upper = False
                is_selected_lower = False
                is_selected_dress = False

main()