import streamlit as st
import pandas as pd
import os
import datetime
from io import BytesIO

# 1. 페이지 설정
st.set_page_config(page_title="차량 위반 관리 시스템", layout="centered")

# 2. 보안 로그인 로직
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False

def check_password():
    st.title("🔒 보안 접속")
    pwd = st.text_input("접속 비밀번호를 입력하세요", type="password")
    if st.button("로그인"):
        if pwd == "316497":
            st.session_state['authenticated'] = True
            st.rerun()
        else:
            st.error("비밀번호가 올바르지 않습니다.")

if not st.session_state['authenticated']:
    check_password()
else:
    # 3. 메인 프로그램 시작
    st.title("🚗 차량 위반 통합 관리 시스템 v3.9")

    # 데이터 디렉토리 설정
    DATA_DIR = "Data"
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

    history_file = os.path.join(DATA_DIR, '누적위반기록.csv')
    detail_log_file = os.path.join(DATA_DIR, '위반상세이력_로그.csv')

    # --- 사이드바 설정 ---
    with st.sidebar:
        st.header("⚙️ 시스템 설정")
        mode = st.radio("운영 모드 선택", ["5부제", "2부제"])
        st.info(f"현재 {mode} 모드로 작동 중입니다.")
        st.divider()
        st.header("🔍 차량 통합 조회")
        
        with st.form(key='search_form', clear_on_submit=True):
            search_car = st.text_input("차량번호 뒷자리 검색")
            submit_search = st.form_submit_button("검색")
        
        if submit_search and search_car:
            st.markdown(f"### '{search_car}' 검색 결과")
            reg_df = pd.read_excel("전체차량리스트.xlsx", engine='openpyxl') if os.path.exists("전체차량리스트.xlsx") else pd.DataFrame()
            if not reg_df.empty:
                reg_res = reg_df[reg_df['차량번호'].astype(str).str.contains(search_car)]
                if not reg_res.empty:
                    for i, row in reg_res.iterrows():
                        full_car_no = str(row['차량번호'])
                        with st.expander(f"🚗 {full_car_no} ({row.get('성명', '이름없음')})", expanded=True):
                            st.success("✅ 등록 차량 확인")
                else:
                    st.error(f"❌ '{search_car}' 미등록 차량")

    # --- 메인 영역 ---
    st.subheader("1. 분석용 파일 업로드")
    uploaded_file = st.file_uploader("출입기록 엑셀 파일(.xlsx, .ods) 선택", type=['xlsx', 'ods'])

    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("시작일 설정", datetime.date.today())
    with col2:
        end_date = st.date_input("종료일 설정", datetime.date.today())

    if st.button("🚀 통합 분석 및 보고서 생성", use_container_width=True):
        if uploaded_file is not None:
            try:
                with st.spinner('분석 중...'):
                    engine = 'odf' if uploaded_file.name.endswith('.ods') else 'openpyxl'
                    df_all = pd.read_excel(uploaded_file, engine=engine)
                    st.success(f"✅ {len(df_all)}건 로드 완료")
            except Exception as e:
                st.error(f"오류 발생: {e}")
        else:
            st.warning("먼저 파일을 업로드해 주세요.")
