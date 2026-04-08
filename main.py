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
    pwd = st.text_input("접속 비밀번호를 입력하세요", type="password", key="login_pwd")
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
    st.title("🚗 차량 위반 통합 관리 시스템 v4.1")

    # 데이터 디렉토리 설정
    DATA_DIR = "Data"
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

    # --- [구역 1] 시스템 설정 (기존 사이드바 내용) ---
    with st.expander("⚙️ 시스템 운영 설정", expanded=False):
        mode = st.radio("운영 모드 선택", ["5부제", "2부제"], horizontal=True)
        st.info(f"현재 **{mode} 모드**로 분석이 진행됩니다.")

    st.divider()

    # --- [구역 2] 차량 통합 조회 (중복 처리 및 사유 표시 강화) ---
    st.subheader("🔍 차량 통합 조회")
    search_car = st.text_input("차량번호 뒷자리 검색 (예: 1234)", placeholder="번호를 입력하고 엔터를 누르세요")
    
    if search_car:
        if os.path.exists("전체차량리스트.xlsx"):
            reg_df = pd.read_excel("전체차량리스트.xlsx", engine='openpyxl')
            # 검색어 포함 데이터 필터링
            reg_res = reg_df[reg_df['차량번호'].astype(str).str.contains(search_car)]
            
            if not reg_res.empty:
                st.write(f"💡 '{search_car}' 검색 결과 총 {len(reg_res)}건이 발견되었습니다.")
                
                for i, row in reg_res.iterrows():
                    full_car_no = str(row.get('차량번호', '정보없음'))
                    owner_name = str(row.get('성명', '이름없음'))
                    # 제외사유와 상세사유 가져오기 (컬럼명이 정확해야 합니다)
                    exc_reason = str(row.get('제외사유', '-'))
                    det_reason = str(row.get('상세사유', '-'))
                    
                    # 카드 형태의 UI로 출력
                    with st.container(border=True):
                        col_car, col_info = st.columns([1, 2])
                        with col_car:
                            st.success(f"**{full_car_no}**")
                            st.write(f"👤 {owner_name}")
                        with col_info:
                            st.markdown(f"**🚫 제외사유:** {exc_reason}")
                            st.markdown(f"**📝 상세사유:** {det_reason}")
            else:
                st.error(f"❌ '{search_car}'로 등록된 차량을 찾을 수 없습니다.")
        else:
            st.warning("⚠️ '전체차량리스트.xlsx' 파일이 존재하지 않습니다.")

    st.divider()

    # --- [구역 3] 분석용 파일 업로드 ---
    st.subheader("📊 데이터 분석 및 보고서")
    
    with st.container(border=True):
        uploaded_file = st.file_uploader("출입기록 엑셀 파일(.xlsx, .ods) 선택", type=['xlsx', 'ods'])

        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("분석 시작일", datetime.date.today())
        with col2:
            end_date = st.date_input("분석 종료일", datetime.date.today())

        if st.button("🚀 통합 분석 및 보고서 생성", use_container_width=True):
            if uploaded_file is not None:
                try:
                    with st.spinner('데이터 분석 중...'):
                        engine = 'odf' if uploaded_file.name.endswith('.ods') else 'openpyxl'
                        df_all = pd.read_excel(uploaded_file, engine=engine)
                        st.success(f"✅ {len(df_all)}건의 출입 데이터를 성공적으로 로드했습니다.")
                        # 여기에 기존에 작성하셨던 상세 분석 로직을 연결하시면 됩니다.
                except Exception as e:
                    st.error(f"파일 로드 중 오류 발생: {e}")
            else:
                st.warning("분석할 파일을 먼저 업로드해 주세요.")
