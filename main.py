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
    st.title("🚗 차량 위반 관리 시스템 v4.2")

    # 데이터 디렉토리 및 파일 설정
    DATA_DIR = "Data"
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

    history_file = os.path.join(DATA_DIR, '누적위반기록.csv')
    detail_log_file = os.path.join(DATA_DIR, '위반상세이력_로그.csv')

    # --- [섹션 1] 시스템 운영 모드 설정 ---
    st.info("💡 분석 기준(운영 모드)을 선택한 후 파일을 업로드해 주세요.")
    mode = st.radio("운영 모드 선택", ["5부제", "2부제"], horizontal=True)
    st.divider()

    # --- [섹션 2] 분석 영역 ---
    st.subheader("1. 분석 실행")
    uploaded_file = st.file_uploader("출입기록 엑셀 파일(.xlsx, .ods) 업로드", type=['xlsx', 'ods'])

    # 날짜 기본값 설정 (어제~오늘)
    today = datetime.date.today()
    yesterday = today - datetime.timedelta(days=1)

    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("시작일 설정", yesterday)
    with col2:
        end_date = st.date_input("종료일 설정", today)

    if st.button("🚀 통합 분석 및 보고서 생성", use_container_width=True):
        if uploaded_file is not None:
            try:
                with st.spinner(f'{mode} 기준으로 분석 중...'):
                    # 데이터 로드
                    engine = 'odf' if uploaded_file.name.endswith('.ods') else 'openpyxl'
                    df_all = pd.read_excel(uploaded_file, engine=engine)

                    # 제외 리스트 로드
                    ex_set = set()
                    if os.path.exists("제외리스트.xlsx"):
                        ex_df_tmp = pd.read_excel("제외리스트.xlsx", engine='openpyxl')
                        ex_set = set(ex_df_tmp['차량번호'].astype(str).str.strip().tolist())

                    # 날짜 필터링
                    df_all['입차일시'] = pd.to_datetime(df_all['입차일시'])
                    mask = (df_all['입차일시'].dt.date >= start_date) & (df_all['입차일시'].dt.date <= end_date)
                    df_filtered = df_all.loc[mask].copy()

                    # 기존 기록 로드
                    df_h = pd.read_csv(history_file) if os.path.exists(history_file) else pd.DataFrame(columns=['이름', '부서', '차량번호', '누적횟수', '최근위반일'])
                    df_log = pd.read_csv(detail_log_file) if os.path.exists(detail_log_file) else pd.DataFrame(columns=['날짜', '차량번호'])

                    # 분석 규칙
                    rules_5 = {0: [1, 6], 1: [2, 7], 2: [3, 8], 3: [4, 9], 4: [5, 0]}
                    dates = sorted(df_filtered['입차일시'].dt.date.unique())

                    output = BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        for d in dates:
                            day_df = df_filtered[df_filtered['입차일시'].dt.date == d].copy()
                            day_df['차량번호'] = day_df['차량번호'].astype(str).str.strip()
                            day_df = day_df.drop_duplicates('차량번호')

                            def is_violating(car_no):
                                if not car_no[-1].isdigit(): return False
                                last_digit = int(car_no[-1])
                                if mode == "2부제":
                                    return (d.day % 2) != (last_digit % 2)
                                else:
                                    if d.weekday() >= 5: return False
                                    return last_digit in rules_5.get(d.weekday(), [])

                            vios = day_df[day_df['차량번호'].apply(is_violating)].copy()
                            vios = vios[~vios['차량번호'].isin(ex_set)]

                            if not vios.empty:
                                actions = []
                                for idx, row in vios.iterrows():
                                    c_no, d_str = str(row['차량번호']), str(d)
                                    # 중복 기록 방지
                                    if not ((df_log['날짜'] == d_str) & (df_log['차량번호'] == c_no)).any():
                                        new_log = pd.DataFrame({'날짜':[d_str], '차량번호':[c_no]})
                                        df_log = pd.concat([df_log, new_log], ignore_index=True)
                                        
                                        if c_no in df_h['차량번호'].astype(str).values:
                                            h_idx = df_h[df_h['차량번호'].astype(str) == c_no].index[0]
                                            df_h.at[h_idx, '누적횟수'] += 1
                                            df_h.at[h_idx, '최근위반일'] = d_str
                                        else:
                                            nr = pd.DataFrame({
                                                '이름':[row.get('정기권성명', row.get('성명', '미확인'))], 
                                                '부서':[row.get('부서(동)', '미확인')], 
                                                '차량번호':[c_no], 
                                                '누적횟수':[1], 
                                                '최근위반일':[d_str]
                                            })
                                            df_h = pd.concat([df_h, nr], ignore_index=True)
                                    
                                    current_cnt = df_h[df_h['차량번호'].astype(str) == c_no]['누적횟수'].values[0]
                                    actions.append(f"{current_cnt}회 위반")
                                
                                vios['조치사항'] = actions
                                vios.to_excel(writer, sheet_name=str(d), index=False)

                        df_h.to_excel(writer, sheet_name='전체누적현황', index=False)

                # 파일 저장 및 다운로드
                df_h.to_csv(history_file, index=False, encoding='utf-8-sig')
                df_log.to_csv(detail_log_file, index=False, encoding='utf-8-sig')
                
                st.success("✅ 분석 완료!")
                st.download_button(
                    label="📊 분석 보고서 다운로드 (Excel)", 
                    data=output.getvalue(), 
                    file_name=f"{mode}_보고서_{datetime.date.today()}.xlsx", 
                    use_container_width=True
                )
            except Exception as e:
                st.error(f"오류 발생: {e}")
        else:
            st.warning("분석할 파일을 먼저 선택해 주세요.")

    # --- [섹션 3] 차량 통합 조회 (최하단) ---
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.divider()
    st.subheader("🔍 차량 통합 조회")
    
    with st.form(key='search_form_bottom', clear_on_submit=True):
        search_car = st.text_input("차량번호 뒷자리 검색")
        submit_search = st.form_submit_button("조회 하기", use_container_width=True)
    
    if submit_search and search_car:
        reg_df = pd.read_excel("전체차량리스트.xlsx", engine='openpyxl') if os.path.exists("전체차량리스트.xlsx") else pd.DataFrame()
        ex_df = pd.read_excel("제외리스트.xlsx", engine='openpyxl') if os.path.exists("제외리스트.xlsx") else pd.DataFrame()
        df_h_load = pd.read_csv(history_file) if os.path.exists(history_file) else pd.DataFrame()

        if not reg_df.empty:
            reg_res = reg_df[reg_df['차량번호'].astype(str).str.contains(search_car)]
            if not reg_res.empty:
                for i, row in reg_res.iterrows():
                    full_car_no = str(row['차량번호'])
                    is_excluded = False
                    if not ex_df.empty:
                        ex_res = ex_df[ex_df['차량번호'].astype(str) == full_car_no]
                        if not ex_res.empty:
                            is_excluded = True
                            ex_info = ex_res.iloc[0]

                    with st.expander(f"🚗 {full_car_no} ({row.get('성명', row.get('이름', '이름없음'))})", expanded=True):
                        if is_excluded:
                            st.info(f"✅ **제외 대상**: {ex_info.get('제외사유','-')}")
                        else:
                            st.success("✅ **일반 등록 차량**")
                        
                        if not df_h_load.empty:
                            h_res = df_h_load[df_h_load['차량번호'].astype(str) == full_car_no]
                            if not h_res.empty:
                                st.write(f"🚩 **위반:** {h_res.iloc[0]['누적횟수']}회 (최근: {h_res.iloc[0]['최근위반일']})")
            else:
                st.error(f"❌ '{search_car}' 검색 결과가 없습니다.")
        else:
            st.warning("전체차량리스트.xlsx 파일이 없습니다.")
