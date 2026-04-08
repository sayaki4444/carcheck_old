import streamlit as st
import pandas as pd
import os
import datetime
from io import BytesIO

# 1. 페이지 설정 (사이드바 메뉴가 나타나지 않도록 설정)
st.set_page_config(
    page_title="차량 위반 통합 관리 시스템", 
    layout="centered", 
    initial_sidebar_state="collapsed"
)

# 2. 보안 로그인 로직
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False

def check_password():
    st.title("🔒 보안 접속")
    pwd = st.text_input("접속 비밀번호를 입력하세요", type="password", key="login_input")
    if st.button("로그인"):
        if pwd == "316497":
            st.session_state['authenticated'] = True
            st.rerun()
        else:
            st.error("비밀번호가 올바르지 않습니다.")

# 로그인 체크 후 메인 프로그램 실행
if not st.session_state['authenticated']:
    check_password()
else:
    # 3. 메인 프로그램 시작
    st.title("🚗 차량 위반 통합 관리 시스템 v4.3")

    # 데이터 디렉토리 설정
    DATA_DIR = "Data"
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

    # --- [섹션 1] 시스템 운영 설정 ---
    # 사이드바 대신 메인 화면 상단에 배치
    with st.expander("⚙️ 시스템 운영 모드 설정", expanded=False):
        mode = st.radio("운영 모드 선택", ["5부제", "2부제"], horizontal=True)
        st.info(f"현재 **{mode} 모드**로 설정되어 있습니다.")

    st.divider()

    # --- [섹션 2] 차량 통합 조회 (중복 조회 및 상세사유 포함) ---
    st.subheader("🔍 차량 통합 조회")
    search_car = st.text_input("차량번호 뒷자리 검색 (예: 1234)", placeholder="번호 입력 후 Enter")
    
    if search_car:
        # 파일 존재 여부 확인
        if os.path.exists("전체차량리스트.xlsx"):
            try:
                reg_df = pd.read_excel("전체차량리스트.xlsx", engine='openpyxl')
                # 검색어가 포함된 모든 차량 필터링
                reg_res = reg_df[reg_df['차량번호'].astype(str).str.contains(search_car)]
                
                if not reg_res.empty:
                    st.info(f"💡 '{search_car}' 검색 결과: 총 {len(reg_res)}건 발견")
                    
                    # 발견된 모든 차량 정보를 반복문으로 표시
                    for i, row in reg_res.iterrows():
                        full_car_no = str(row.get('차량번호', '정보없음'))
                        owner_name = str(row.get('성명', '이름없음'))
                        exc_reason = str(row.get('제외사유', '-'))  # 제외사유 컬럼
                        det_reason = str(row.get('상세사유', '-'))  # 상세사유 컬럼
                        
                        # 각 차량 정보를 깔끔한 박스(Container)에 담아 표시
                        with st.container(border=True):
                            col_info, col_detail = st.columns([1, 2])
                            with col_info:
                                st.markdown(f"### {full_car_no}")
                                st.caption(f"성명: {owner_name}")
                            with col_detail:
                                st.markdown(f"**🚫 제외사유:** {exc_reason}")
                                st.markdown(f"**📝 상세사유:** {det_reason}")
                else:
                    st.error(f"❌ '{search_car}' 미등록 차량입니다.")
            except Exception as e:
                st.error(f"데이터를 읽는 중 오류가 발생했습니다: {e}")
        else:
            st.warning("⚠️ '전체차량리스트.xlsx' 파일이 경로에 없습니다.")

    st.divider()

    # --- [섹션 3] 데이터 분석 및 보고서 생성 ---
    st.subheader("📊 출입 기록 분석")
    
    # 시작일 설정을 '어제'로 계산 (today - 1일)
    yesterday = datetime.date.today() - datetime.timedelta(days=1)
    
    with st.container(border=True):
        uploaded_file = st.file_uploader("출입기록 엑셀 파일(.xlsx, .ods) 선택", type=['xlsx', 'ods'])

        col_date1, col_date2 = st.columns(2)
        with col_date1:
            # 기본값을 어제로 설정
            start_date = st.date_input("시작일 설정", yesterday)
        with col_date2:
            end_date = st.date_input("종료일 설정", datetime.date.today())

        if st.button("🚀 통합 분석 및 보고서 생성", use_container_width=True):
            if uploaded_file is not None:
                try:
                    with st.spinner('분석 데이터 로드 중...'):
                        engine = 'odf' if uploaded_file.name.endswith('.ods') else 'openpyxl'
                        df_all = pd.read_excel(uploaded_file, engine=engine)
                        
                        # 분석 성공 메시지
                        st.success(f"✅ {len(df_all)}건의 데이터를 로드했습니다.")
                        st.write(f"📅 분석 기간: {start_date} ~ {end_date}")
                        
                        # [참고] 여기에 기존에 사용하시던 상세 분석/필터링 로직 코드를 
                        # 이 부분 바로 아래에 붙여넣으시면 됩니다.
                        
                except Exception as e:
                    st.error(f"분석 중 오류 발생: {e}")
            else:
                st.warning("먼저 분석할 파일을 업로드해 주세요.")
