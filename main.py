import streamlit as st
import pandas as pd
import os
import datetime
from io import BytesIO

# 1. 페이지 설정
st.set_page_config(
    page_title="차량 위반 통합 관리 시스템", 
    layout="centered", 
    initial_sidebar_state="collapsed"
)

# [초강력 CSS] 사이드바 완전 제거
st.markdown("""
    <style>
        section[data-testid="stSidebar"] { display: none !important; }
        [data-testid="collapsedControl"] { display: none !important; }
        .main .block-container { padding-top: 2rem; max-width: 800px; }
    </style>
    """, unsafe_allow_html=True)

# 2. 보안 로그인 로직
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False

def check_password():
    st.title("🔒 보안 접속")
    pwd = st.text_input("접속 비밀번호를 입력하세요", type="password", key="gate_v5_1")
    if st.button("로그인"):
        if pwd == "316497":
            st.session_state['authenticated'] = True
            st.rerun()
        else:
            st.error("비밀번호가 올바르지 않습니다.")

if not st.session_state['authenticated']:
    check_password()
else:
    st.title("🚗 차량 위반 통합 관리 시스템 v5.1")

    # --- [메뉴 1] 차량 통합 조회 (전체리스트 + 제외리스트 결합) ---
    st.subheader("🔍 1. 차량 통합 조회")
    search_car = st.text_input("차량번호 뒷자리 검색 (예: 6365)", placeholder="번호 4자리 입력 후 Enter")
    
    if search_car:
        # 파일 존재 여부 확인
        f1 = os.path.exists("전체차량리스트.xlsx")
        f2 = os.path.exists("제외리스트.xlsx")
        
        if f1 and f2:
            try:
                # 1. 두 파일 로드
                df_all = pd.read_excel("전체차량리스트.xlsx", engine='openpyxl')
                df_exc = pd.read_excel("제외리스트.xlsx", engine='openpyxl')
                
                # 2. 차량번호를 기준으로 데이터 합치기 (Left Join)
                # 전체차량리스트에 있는 차량이 제외리스트에 정보가 있으면 가져옴
                merged_df = pd.merge(df_all, df_exc, on='차량번호', how='left')
                
                # 3. 검색어로 필터링
                reg_res = merged_df[merged_df['차량번호'].astype(str).str.contains(search_car)]
                
                if not reg_res.empty:
                    st.success(f"💡 '{search_car}' 검색 결과: 총 {len(reg_res)}건 발견")
                    
                    for i, row in reg_res.iterrows():
                        c_no = str(row.get('차량번호', '정보없음'))
                        c_name = str(row.get('성명', '이름없음'))
                        
                        # 제외리스트에서 가져온 정보 (컬럼명 확인 필요)
                        # 합쳐진 결과에서 제외사유와 상세사유를 가져옵니다.
                        c_exc = row.get('제외사유')
                        c_det = row.get('상세사유')
                        
                        # 비어있는 값 처리
                        c_exc = str(c_exc) if pd.notna(c_exc) else "제외 대상 아님"
                        c_det = str(c_det) if pd.notna(c_det) else "상세 정보 없음"
                        
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
                st.error(f"데이터 결합 중 오류 발생: {e}")
        else:
            st.warning("⚠️ '전체차량리스트.xlsx' 또는 '제외리스트.xlsx' 파일이 누락되었습니다.")

    st.divider()

    # --- [메뉴 2] 운영 모드 설정 ---
    st.subheader("⚙️ 2. 운영 모드 설정")
    with st.expander("모드 변경 (5부제/2부제)", expanded=False):
        mode = st.radio("현재 모드 선택", ["5부제", "2부제"], horizontal=True)
        st.info(f"선택된 모드: **{mode}**")

    st.divider()

    # --- [메뉴 3] 출입 기록 분석 ---
    st.subheader("📊 3. 출입 기록 분석")
    yesterday = datetime.date.today() - datetime.timedelta(days=1)
    
    with st.container(border=True):
        uploaded_file = st.file_uploader("출입기록 엑셀 파일 선택", type=['xlsx', 'ods'])
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            start_date = st.date_input("분석 시작일", yesterday)
        with col_d2:
            end_date = st.date_input("분석 종료일", datetime.date.today())

        if st.button("🚀 통합 분석 시작", use_container_width=True):
            if uploaded_file is not None:
                st.success(f"데이터 로드 완료! 분석 기간: {start_date} ~ {end_date}")
            else:
                st.warning("분석할 파일을 먼저 선택해 주세요.")
