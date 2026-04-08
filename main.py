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

# [초강력 CSS] PC와 모바일에서 사이드바와 메뉴 버튼을 완전히 제거
st.markdown("""
    <style>
        /* 사이드바 영역 제거 */
        section[data-testid="stSidebar"] {
            display: none !important;
        }
        /* 사이드바 여는 화살표 제거 */
        [data-testid="collapsedControl"] {
            display: none !important;
        }
        /* 상단 여백 조절 */
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
    pwd = st.text_input("접속 비밀번호를 입력하세요", type="password", key="security_gate_v5")
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
    # 3. 메인 프로그램 시작 (버전 5.0)
    st.title("🚗 차량 위반 통합 관리 시스템 v5.0")

    # 데이터 저장 폴더
    DATA_DIR = "Data"
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

    # --- [메뉴 1] 차량 통합 조회 (최상단 배치) ---
    st.subheader("🔍 1. 차량 통합 조회")
    search_car = st.text_input("차량번호 뒷자리 검색 (예: 6365)", placeholder="번호 4자리 입력 후 Enter")
    
    if search_car:
        if os.path.exists("전체차량리스트.xlsx"):
            try:
                # 엑셀 파일 로드 (모든 시트 중 첫번째 시트 기준)
                reg_df = pd.read_excel("전체차량리스트.xlsx", engine='openpyxl')
                
                # 검색어가 포함된 모든 차량 찾기
                reg_res = reg_df[reg_df['차량번호'].astype(str).str.contains(search_car)]
                
                if not reg_res.empty:
                    st.info(f"💡 '{search_car}' 검색 결과: 총 {len(reg_res)}건 발견")
                    
                    for i, row in reg_res.iterrows():
                        c_no = str(row.get('차량번호', '정보없음'))
                        c_name = str(row.get('성명', '이름없음'))
                        
                        # 엑셀 컬럼명 매칭 (공백 제거 후 비교하여 정확도 향상)
                        # '제외사유' 또는 '상세사유' 컬럼이 있는지 확인
                        c_exc = row.get('제외사유') if '제외사유' in reg_df.columns else "컬럼명 확인 필요"
                        c_det = row.get('상세사유') if '상세사유' in reg_df.columns else "컬럼명 확인 필요"
                        
                        # 데이터가 NaN(비어있음)인 경우 처리
                        c_exc = str(c_exc) if pd.notna(c_exc) else "등록된 내용 없음"
                        c_det = str(c_det) if pd.notna(c_det) else "등록된 내용 없음"
                        
                        # 카드 형태로 상세 정보 출력
                        with st.container(border=True):
                            st.markdown(f"### 🚗 {c_no} ({c_name})")
                            col_a, col_b = st.columns(2)
                            with col_a:
                                st.error(f"**🚫 제외 사유**\n\n{c_exc}")
                            with col_b:
                                st.warning(f"**📝 상세 사유**\n\n{c_det}")
                else:
                    st.error(f"❌ '{search_car}' 미등록 차량입니다.")
            except Exception as e:
                st.error(f"엑셀 읽기 오류: {e}")
        else:
            st.warning("⚠️ '전체차량리스트.xlsx' 파일을 찾을 수 없습니다.")

    st.divider()

    # --- [메뉴 2] 운영 모드 설정 ---
    st.subheader("⚙️ 2. 운영 모드 설정")
    with st.expander("모드 변경 (5부제/2부제)", expanded=False):
        mode = st.radio("현재 모드 선택", ["5부제", "2부제"], horizontal=True)
        st.write(f"설정된 모드: **{mode}**")

    st.divider()

    # --- [메뉴 3] 데이터 분석 및 보고서 ---
    st.subheader("📊 3. 출입 기록 분석")
    
    # 시작일 기본값을 '어제'로 설정
    yesterday = datetime.date.today() - datetime.timedelta(days=1)
    
    with st.container(border=True):
        uploaded_file = st.file_uploader("출입기록 엑셀 파일 선택", type=['xlsx', 'ods'])

        d_col1, d_col2 = st.columns(2)
        with d_col1:
            start_date = st.date_input("분석 시작일 (기본: 어제)", yesterday)
        with d_col2:
            end_date = st.date_input("분석 종료일 (기본: 오늘)", datetime.date.today())

        if st.button("🚀 통합 분석 시작", use_container_width=True):
            if uploaded_file is not None:
                st.success(f"데이터 로드 완료! 분석 기간: {start_date} ~ {end_date}")
                # 이후 분석 로직 추가
            else:
                st.warning("분석할 파일을 선택해 주세요.")
