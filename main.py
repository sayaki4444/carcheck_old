import streamlit as st
import pandas as pd
import os
import datetime
from io import BytesIO

# 1. 페이지 설정 (모바일 최적화)
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
    st.title("🚗 차량 위반 통합 관리 시스템 v3.8")
    
    # 데이터 디렉토리 설정
    DATA_DIR = "Data"
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
    
    history_file = os.path.join(DATA_DIR, '누적위반기록.csv')
    detail_log_file = os.path.join(DATA_DIR, '위반상세이력_로그.csv')

    # 사이드바 설정
    with st.sidebar:
        st.header("⚙️ 시스템 설정")
        mode = st.radio("운영 모드 선택", ["5부제", "2부제"])
        st.info(f"현재 {mode} 모드로 작동 중입니다.")
        
        st.divider()
        st.header("🔍 차량 및 제외여부 조회")
        search_car = st.text_input("차량번호 뒷자리 검색")
        
        if search_car:
            # 1. 제외 리스트 확인
            is_excluded = False
            if os.path.exists("제외리스트.xlsx"):
                ex_df = pd.read_excel("제외리스트.xlsx")
                # 차량번호 컬럼에서 검색어가 포함된 행 찾기
                ex_res = ex_df[ex_df['차량번호'].astype(str).str.contains(search_car)]
                if not ex_res.empty:
                    is_excluded = True
                    st.info(f"💡 해당 차량({search_car})은 **[제외 리스트]**에 등록되어 있습니다.")

            # 2. 누적 위반 기록 확인
            if os.path.exists(history_file):
                df_h = pd.read_csv(history_file)
                res = df_h[df_h['차량번호'].astype(str).str.contains(search_car)]
                
                if not res.empty:
                    info = res.iloc[0]
                    st.success(f"📌 **위반 기록 검색 결과**\n\n**{info['이름']} ({info['부서']})**\n\n누적: {info['누적횟수']}회 / 최근: {info['최근위반일']}")
                elif not is_excluded:
                    st.warning("기록이 없습니다. (깨끗한 차량)")
            else:
                if not is_excluded:
                    st.error("데이터 파일이 없어 조회가 불가능합니다.")

    # 메인 영역 - 파일 업로드
    st.subheader("1. 분석용 파일 업로드")
    uploaded_file = st.file_uploader("출입기록 엑셀 파일(.xlsx, .ods)을 선택하세요", type=['xlsx', 'ods'])
    
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("시작일 설정", datetime.date.today())
    with col2:
        end_date = st.date_input("종료일 설정", datetime.date.today())

    # 분석 실행 버튼
    if st.button("🚀 통합 분석 및 보고서 생성", use_container_width=True):
        if uploaded_file is not None:
            try:
                # 데이터 로드
                with st.spinner('분석 중...'):
                    if uploaded_file.name.endswith('.ods'):
                        df_all = pd.read_excel(uploaded_file, engine='odf')
                    else:
                        df_all = pd.read_excel(uploaded_file)

                    # 제외 리스트 로드 (없으면 빈 셋)
                    ex_set = set()
                    if os.path.exists("제외리스트.xlsx"):
                        ex_set = set(pd.read_excel("제외리스트.xlsx")['차량번호'].astype(str).str.strip().tolist())

                    # 날짜 필터링
                    df_all['입차일시'] = pd.to_datetime(df_all['입차일시'])
                    mask = (df_all['입차일시'].dt.date >= start_date) & (df_all['입차일시'].dt.date <= end_date)
                    df_filtered = df_all.loc[mask].copy()

                    # 기록 파일 로드
                    df_h = pd.read_csv(history_file) if os.path.exists(history_file) else pd.DataFrame(columns=['이름', '부서', '차량번호', '누적횟수', '최근위반일'])
                    df_log = pd.read_csv(detail_log_file) if os.path.exists(detail_log_file) else pd.DataFrame(columns=['날짜', '차량번호'])

                    # 분석 로직 (5부제/2부제)
                    rules_5 = {0: [1, 6], 1: [2, 7], 2: [3, 8], 3: [4, 9], 4: [5, 0]}
                    dates = sorted(df_filtered['입차일시'].dt.date.unique())
                    
                    # 엑셀 생성을 위한 메모리 버퍼
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
                                # 누적 기록 업데이트
                                actions = []
                                for idx, row in vios.iterrows():
                                    c_no, d_str = row['차량번호'], str(d)
                                    # 중복 로그 방지
                                    if not ((df_log['날짜'] == d_str) & (df_log['차량번호'] == c_no)).any():
                                        df_log = pd.concat([df_log, pd.DataFrame({'날짜':[d_str], '차량번호':[c_no]})], ignore_index=True)
                                        if c_no in df_h['차량번호'].astype(str).values:
                                            h_idx = df_h[df_h['차량번호'].astype(str) == c_no].index[0]
                                            df_h.at[h_idx, '누적횟수'] += 1
                                            df_h.at[h_idx, '최근위반일'] = d_str
                                        else:
                                            nr = pd.DataFrame({'이름':[row.get('정기권성명','미확인')], '부서':[row.get('부서(동)','미확인')], 
                                                              '차량번호':[c_no], '누적횟수':[1], '최근위반일':[d_str]})
                                            df_h = pd.concat([df_h, nr], ignore_index=True)
                                    
                                    cnt = df_h[df_h['차량번호'].astype(str) == c_no]['누적횟수'].values[0]
                                    actions.append(f"{cnt}회 위반")
                                
                                vios['조치사항'] = actions
                                vios.to_excel(writer, sheet_name=str(d), index=False)

                        df_h.to_excel(writer, sheet_name='전체누적현황', index=False)

                # 파일 저장 및 다운로드 버튼
                df_h.to_csv(history_file, index=False, encoding='utf-8-sig')
                df_log.to_csv(detail_log_file, index=False, encoding='utf-8-sig')
                
                st.success("✅ 분석이 완료되었습니다!")
                st.download_button(
                    label="📊 분석 보고서 다운로드 (Excel)",
                    data=output.getvalue(),
                    file_name=f"{mode}_위반보고서_{datetime.date.today()}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            except Exception as e:
                st.error(f"오류가 발생했습니다: {e}")
        else:
            st.warning("먼저 파일을 업로드해 주세요.")
