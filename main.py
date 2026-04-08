import streamlit as st
import pandas as pd
import os
import datetime
from io import BytesIO

# 1. 페이지 설정: 사이드바 숨김 및 레이아웃 설정
st.set_page_config(
    page_title="차량 위반 통합 관리 시스템", 
    layout="centered", 
    initial_sidebar_state="collapsed"
)

# [초강력 조치] PC와 모바일 모두에서 사이드바를 완전히 제거하는 CSS
st.markdown("""
    <style>
        /* 사이드바 전체 영역 제거 */
        section[data-testid="stSidebar"] {
            display: none !important;
        }
        /* 사이드바 여는 화살표 버튼 제거 */
        [data-testid="collapsedControl"] {
            display: none !important;
        }
        /* 메인 콘텐츠 상단 여백 및 가로 폭 최적화 */
        .main .block-container {
            padding-top: 2rem;
            max-width: 800px;
        }
    </style>
    """, unsafe_allow_html=True)

# 2. 보안 로그인 로직
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False

def check_password():
    st.title("🔒 보안 접속")
    st.write("인가된 사용자만 접근 가능합니다.")
    pwd = st.text_input("접속 비밀번호", type="password", key="final_security_key")
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
    st.title("🚗 차량 위반 통합 관리 시스템 v4.8")

    # 데이터 저장 경로 설정
    DATA_DIR = "Data"
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

    # --- [섹션 1] 시스템 운영 설정 ---
    with st.expander("⚙️ 운영 모드 설정 (현재 설정 확인)", expanded=False):
        mode = st.radio("모드 선택", ["5부제", "2부제"], horizontal=True)
        st.write(f"현재 **{mode}** 모드로 작동 중입니다.")

    st.divider()

    # --- [섹션 2] 차량 통합 조회 (중복 조회 및 상세 사유 출력) ---
    st.subheader("🔍 차량 통합 조회")
    search_car = st.text_input("차량번호 뒷자리 검색 (예: 1234)", placeholder="번호 입력 후 Enter")
    
    if search_car:
        if os.path.exists("전체차량리스트.xlsx"):
            try:
                # 엑셀 로드
                reg_df = pd.read_excel("전체차량리스트.xlsx", engine='openpyxl')
                
                # 검색어 포함된 모든 차량 데이터 필터링
                reg_res = reg_df[reg_df['차량번호'].astype(str).str.contains(search_car)]
                
                if not reg_res.empty:
                    st.info(f"💡 '{search_car}' 검색 결과: 총 {len(reg_res)}건 발견")
                    
                    for i, row in reg_res.iterrows():
                        # 데이터 추출 (엑셀의 정확한 컬럼명을 사용해야 합니다)
                        c_no = str(row.get('차량번호', '정보없음'))
                        c_name = str(row.get('성명', '이름없음'))
                        
                        # 엑셀 파일에 '제외사유'와 '상세사유'라는 제목의 칸이 있어야 합니다.
                        c_exc = str(row.get('제외사유', '내용 없음')) 
                        c_det = str(row.get('상세사유', '내용 없음'))
                        
                        # 각 차량 정보를 박스 형태로 출력
                        with st.container(border=True):
                            st.markdown(f"### 🚗 {c_no} ({c_name})")
                            col_res1, col_res2 = st.columns(2)
                            with col_res1:
                                st.error(f"**🚫 제외 사유**\n\n{c_exc}")
                            with col_res2:
                                st.warning(f"**📝 상세 사유**\n\n{c_det}")
                else:
                    st.error(f"❌ '{search_car}'로 등록된 차량이 없습니다.")
            except Exception as e:
                st.error(f"엑셀 파일을 읽는 도중 오류가 발생했습니다: {e}")
        else:
            st.warning("⚠️ '전체차량리스트.xlsx' 파일을 찾을 수 없습니다.")

    st.divider()

    # --- [섹션 3] 분석용 파일 업로드 및 날짜 설정 ---
    st.subheader("📊 출입 기록 분석")
    
    # 시작일 기본값을 '어제'로 설정
    yesterday = datetime.date.today() - datetime.timedelta(days=1)
    
    with st.container(border=True):
        uploaded_file = st.file_uploader("출입기록 엑셀 파일 선택", type=['xlsx', 'ods'])

        col_d1, col_d2 = st.columns(2)
        with col_d1:
            # 시작일 어제 날짜
            start_date = st.date_input("분석 시작일", yesterday)
        with col_d2:
            # 종료일 오늘 날짜
            end_date = st.date_input("분석 종료일", datetime.date.today())

        if st.button("🚀 통합 분석 및 보고서 생성", use_container_width=True):
            if uploaded_file is not None:
                try:
                    with st.spinner('데이터 로드 중...'):
                        engine = 'odf' if uploaded_file.name.endswith('.ods') else 'openpyxl'
                        df_all = pd.read_excel(uploaded_file, engine=engine)
                        st.success(f"✅ {len(df_all)}건 데이터 로드 완료")
                        st.write(f"📅 분석 기간: {start_date} ~ {end_date}")
                        # 여기에 위반자 필터링 로직을 연결하세요.
                except Exception as e:
                    st.error(f"분석 중 오류 발생: {e}")
            else:
                st.warning("분석할 파일을 먼저 선택해 주세요.")
