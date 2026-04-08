import streamlit as st
import pandas as pd
import os
import datetime
from io import BytesIO

# 1. 페이지 설정: 사이드바를 숨기고 중앙 레이아웃 고정
st.set_page_config(
    page_title="차량 위반 통합 관리 시스템", 
    layout="centered", 
    initial_sidebar_state="collapsed"
)

# [강력 조치] 사이드바와 메뉴 버튼을 아예 삭제하는 디자인 설정
st.markdown("""
    <style>
        /* 사이드바 여는 화살표 버튼 숨기기 */
        [data-testid="collapsedControl"] {
            display: none;
        }
        /* 왼쪽 사이드바 영역 자체를 화면에서 제거 */
        section[data-testid="stSidebar"] {
            display: none !important;
        }
        /* 메인 콘텐츠 상단 여백 조절 */
        .main .block-container {
            padding-top: 2rem;
        }
    </style>
    """, unsafe_allow_html=True)

# 2. 보안 로그인 로직
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False

def check_password():
    st.title("🔒 보안 접속")
    st.write("인가된 사용자만 접근 가능합니다. 비밀번호를 입력하세요.")
    pwd = st.text_input("접속 비밀번호", type="password", key="final_login_key")
    if st.button("로그인"):
        if pwd == "316497":
            st.session_state['authenticated'] = True
            st.rerun()
        else:
            st.error("비밀번호가 올바르지 않습니다.")

# 로그인 상태 확인
if not st.session_state['authenticated']:
    check_password()
else:
    # 3. 메인 프로그램 시작
    st.title("🚗 차량 위반 통합 관리 시스템 v4.7")

    # 데이터 폴더 자동 생성
    DATA_DIR = "Data"
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

    # --- [섹션 1] 시스템 설정 ---
    with st.expander("⚙️ 시스템 운영 설정", expanded=False):
        mode = st.radio("운영 모드 선택", ["5부제", "2부제"], horizontal=True)
        st.info(f"현재 **{mode} 모드**로 분석이 진행됩니다.")

    st.divider()

    # --- [섹션 2] 차량 통합 조회 (중복 모두 표시 및 사유 노출) ---
    st.subheader("🔍 차량 통합 조회")
    search_car = st.text_input("차량번호 뒷자리 검색 (예: 1234)", placeholder="번호 4자리 입력 후 Enter")
    
    if search_car:
        if os.path.exists("전체차량리스트.xlsx"):
            try:
                reg_df = pd.read_excel("전체차량리스트.xlsx", engine='openpyxl')
                # 검색어가 포함된 모든 차량 데이터 필터링 (중복 차량 처리)
                reg_res = reg_df[reg_df['차량번호'].astype(str).str.contains(search_car)]
                
                if not reg_res.empty:
                    st.success(f"💡 총 {len(reg_res)}건의 등록 내역이 발견되었습니다.")
                    
                    for i, row in reg_res.iterrows():
                        c_no = str(row.get('차량번호', '정보없음'))
                        c_name = str(row.get('성명', '이름없음'))
                        c_exc = str(row.get('제외사유', '-'))
                        c_det = str(row.get('상세사유', '-'))
                        
                        # 카드 스타일로 중복 차량 정보를 하나씩 나열
                        with st.container(border=True):
                            col_a, col_b = st.columns([1, 2])
                            with col_a:
                                st.subheader(c_no)
                                st.write(f"👤 {c_name}")
                            with col_b:
                                st.markdown(f"**🚫 제외사유:** {c_exc}")
                                st.markdown(f"**📝 상세사유:** {c_det}")
                else:
                    st.error(f"❌ '{search_car}' 미등록 차량입니다.")
            except Exception as e:
                st.error(f"엑셀 파일을 읽는 중 오류가 발생했습니다: {e}")
        else:
            st.warning("⚠️ '전체차량리스트.xlsx' 파일이 없습니다. 경로를 확인해 주세요.")

    st.divider()

    # --- [섹션 3] 분석용 파일 업로드 및 날짜 설정 ---
    st.subheader("📊 출입 기록 분석")
    
    # 시작일 기본값을 '어제'로 설정
    yesterday = datetime.date.today() - datetime.timedelta(days=1)
    
    with st.container(border=True):
        uploaded_file = st.file_uploader("출입기록 엑셀 파일 선택", type=['xlsx', 'ods'])

        d_col1, d_col2 = st.columns(2)
        with d_col1:
            # 시작일을 어제로 고정
            start_date = st.date_input("분석 시작일", yesterday)
        with d_col2:
            # 종료일을 오늘로 고정
            end_date = st.date_input("분석 종료일", datetime.date.today())

        if st.button("🚀 통합 분석 시작", use_container_width=True):
            if uploaded_file is not None:
                try:
                    with st.spinner('데이터 분석 중...'):
                        engine = 'odf' if uploaded_file.name.endswith('.ods') else 'openpyxl'
                        df_all = pd.read_excel(uploaded_file, engine=engine)
                        st.success(f"✅ {len(df_all)}건 데이터 로드 완료")
                        st.write(f"📅 분석 기간: {start_date} ~ {end_date}")
                        # (기존 분석 로직이 들어갈 자리)
                except Exception as e:
                    st.error(f"분석 중 오류 발생: {e}")
            else:
                st.warning("분석할 파일을 먼저 선택해 주세요.")
