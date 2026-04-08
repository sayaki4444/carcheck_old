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
    pwd = st.text_input("접속 비밀번호를 입력하세요", type="password", key="gate_v5_2")
    if st.button("로그인"):
        if pwd == "316497":
            st.session_state['authenticated'] = True
            st.rerun()
        else:
            st.error("비밀번호가 올바르지 않습니다.")

if not st.session_state['authenticated']:
    check_password()
else:
    st.title("🚗 차량 위반 통합 관리 시스템 v5.2")

    # --- [메뉴 1] 차량 통합 조회 (순차적 검색 로직) ---
    st.subheader("🔍 1. 차량 통합 조회")
    search_car = st.text_input("차량번호 뒷자리 검색 (예: 6365)", placeholder="번호 4자리 입력 후 Enter")
    
    if search_car:
        # 파일명 변경 반영
        file_reg = "전체차량리스트_업로드용.xlsx"
        file_exc = "제외리스트.xlsx"
        
        if os.path.exists(file_reg) and os.path.exists(file_exc):
            try:
                # 데이터 로드
                df_reg = pd.read_excel(file_reg, engine='openpyxl')
                df_exc = pd.read_excel(file_exc, engine='openpyxl')
                
                # 검색어 포함 차량 필터링 (전체리스트 기준)
                target_cars = df_reg[df_reg['차량번호'].astype(str).str.contains(search_car)]
                
                if not target_cars.empty:
                    st.info(f"💡 '{search_car}' 관련 차량 {len(target_cars)}건 발견")
                    
                    for i, row in target_cars.iterrows():
                        c_no = str(row.get('차량번호', '정보없음'))
                        c_name = str(row.get('성명', '이름없음'))
                        c_dept = str(row.get('소속', '소속 정보 없음')) # 소속 정보 가져오기
                        
                        # 해당 차량이 제외리스트에 있는지 확인
                        exc_info = df_exc[df_exc['차량번호'].astype(str) == c_no]
                        
                        with st.container(border=True):
                            if not exc_info.empty:
                                # [경우 1] 제외 대상 차량인 경우
                                st.markdown(f"### 🚗 {c_no} ({c_name})")
                                st.caption(f"소속: {c_dept}")
                                col_a, col_b = st.columns(2)
                                with col_a:
                                    st.error(f"**🚫 제외 사유**\n\n{exc_info.iloc[0].get('제외사유', '내용 없음')}")
                                with col_b:
                                    st.warning(f"**📝 상세 사유**\n\n{exc_info.iloc[0].get('상세사유', '내용 없음')}")
                            else:
                                # [경우 2] 제외 대상은 아니지만 등록된 차량인 경우
                                st.markdown(f"### 🚗 {c_no} ({c_name})")
                                st.success("✅ 회사 등록 차량 (제외 대상 아님)")
                                st.write(f"**🏢 소속 정보:** {c_dept}")
                else:
                    # [경우 3] 전체리스트에도 없는 경우
                    st.error(f"❌ '{search_car}' 미등록 차량입니다. (사내 명단에 없음)")
                    
            except Exception as e:
                st.error(f"조회 중 오류 발생: {e}")
        else:
            st.warning(f"⚠️ '{file_reg}' 또는 '{file_exc}' 파일이 없습니다.")

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
