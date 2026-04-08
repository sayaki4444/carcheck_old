import streamlit as st
import pandas as pd
import os
import datetime
from io import BytesIO

# 1. 페이지 설정 (사이드바 숨김 및 레이아웃 설정)
st.set_page_config(
    page_title="차량 위반 관리 시스템", 
    layout="centered", 
    initial_sidebar_state="collapsed"
)

# 2. 보안 로그인 로직
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False

def check_password():
    st.title("🔒 보안 접속")
    st.write("시스템 접근을 위해 비밀번호를 입력하세요.")
    pwd = st.text_input("접속 비밀번호", type="password", key="login_pwd")
    if st.button("로그인"):
        if pwd == "316497":
            st.session_state['authenticated'] = True
            st.rerun()
        else:
            st.error("비밀번호가 올바르지 않습니다.")

# 로그인 여부 확인
if not st.session_state['authenticated']:
    check_password()
else:
    # 3. 메인 프로그램 시작
    st.title("🚗 차량 위반 통합 관리 시스템 v4.4")

    # 데이터 저장 경로 설정
    DATA_DIR = "Data"
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

    # --- [섹션 1] 시스템 운영 설정 ---
    with st.expander("⚙️ 운영 모드 설정 (5부제/2부제)", expanded=False):
        mode = st.radio("운영 모드 선택", ["5부제", "2부제"], horizontal=True)
        st.info(f"현재 **{mode} 모드**로 작동 중입니다.")

    st.divider()

    # --- [섹션 2] 차량 통합 조회 (중복 모두 표시 및 상세사유) ---
    st.subheader("🔍 차량 통합 조회")
    search_car = st.text_input("차량번호 뒷자리 검색 (예: 1234)", placeholder="번호 입력 후 Enter")
    
    if search_car:
        if os.path.exists("전체차량리스트.xlsx"):
            try:
                reg_df = pd.read_excel("전체차량리스트.xlsx", engine='openpyxl')
                # 검색어가 포함된 모든 차량 데이터 필터링
                reg_res = reg_df[reg_df['차량번호'].astype(str).str.contains(search_car)]
                
                if not reg_res.empty:
                    st.info(f"💡 '{search_car}' 검색 결과: 총 {len(reg_res)}건 발견")
                    
                    for i, row in reg_res.iterrows():
                        full_car_no = str(row.get('차량번호', '정보없음'))
                        owner_name = str(row.get('성명', '이름없음'))
                        exc_reason = str(row.get('제외사유', '-'))
                        det_reason = str(row.get('상세사유', '-'))
                        
                        # 각 차량 정보를 박스 형태로 출력
                        with st.container(border=True):
                            col1, col2 = st.columns([1, 2])
                            with col1:
                                st.markdown(f"### {full_car_no}")
                                st.caption(f"성명: {owner_name}")
                            with col2:
                                st.markdown(f"**🚫 제외사유:** {exc_reason}")
                                st.markdown(f"**📝 상세사유:** {det_reason}")
                else:
                    st.error(f"❌ '{search_car}' 미등록 차량입니다.")
            except Exception as e:
                st.error(f"엑셀 읽기 오류: {e}")
        else:
            st.warning("⚠️ '전체차량리스트.xlsx' 파일이 없습니다.")

    st.divider()

    # --- [섹션 3] 분석용 파일 업로드 및 날짜 설정 ---
    st.subheader("📊 데이터 분석 및 보고서 생성")
    
    # 어제 날짜 계산
    yesterday = datetime.date.today() - datetime.timedelta(days=1)
    
    with st.container(border=True):
        uploaded_file = st.file_uploader("출입기록 엑셀 파일 선택", type=['xlsx', 'ods'])

        col_d1, col_d2 = st.columns(2)
        with col_d1:
            # 시작일을 '어제'로 설정
            start_date = st.date_input("시작일 설정", yesterday)
        with col_date2:
            end_date = st.date_input("종료일 설정", datetime.date.today())

        if st.button("🚀 통합 분석 및 보고서 생성", use_container_width=True):
            if uploaded_file is not None:
                try:
                    with st.spinner('데이터 로드 중...'):
                        engine = 'odf' if uploaded_file.name.endswith('.ods') else 'openpyxl'
                        df_all = pd.read_excel(uploaded_file, engine=engine)
                        st.success(f"✅ {len(df_all)}건 로드 완료 (분석 기간: {start_date} ~ {end_date})")
                        
                        # 여기에 분석 로직이 들어갑니다.
                        
                except Exception as e:
                    st.error(f"오류 발생: {e}")
            else:
                st.warning("분석할 파일을 먼저 업로드해 주세요.")
