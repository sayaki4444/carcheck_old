import streamlit as st  # <-- 이 줄이 반드시 맨 위에 있어야 합니다!

# 세션 상태 확인 및 비밀번호 로직
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False

def check_password():
    # type="password"를 넣어야 입력할 때 별표(*)로 표시됩니다.
    if st.text_input("접속 비밀번호", type="password") == "316497": # 사용할 비밀번호 설정
        st.session_state['authenticated'] = True
    elif st.button("로그인"):
        st.error("비밀번호가 틀렸습니다.")

if not st.session_state['authenticated']:
    check_password()
else:
    # 로그인 성공 시 보여줄 메인 화면 (어제 만든 코드)
    st.title("🚗 위반차량 점검 시스템")
    st.write("현장 점검을 시작합니다.")
    # ... 나머지 코드 ...
    # ... 기존 코드 ...

import pandas as pd
from tkinter import filedialog, messagebox, Toplevel
from tkcalendar import Calendar
import os
import datetime
import shutil
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

# 테마 설정
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class ViolationApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("차량 위반 통합 관리 시스템 v3.8")
        self.geometry("950x850")

        self.data_dir = "Data"
        self.backup_dir = "Backup"
        for d in [self.data_dir, self.backup_dir]:
            if not os.path.exists(d): os.makedirs(d)

        self.history_file = os.path.join(self.data_dir, '누적위반기록.csv')
        self.detail_log_file = os.path.join(self.data_dir, '위반상세이력_로그.csv')
        self.record_path = ""
        self.mode_var = ctk.StringVar(value="5부제")

        # --- UI 레이아웃 ---
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # [사이드바]
        self.sidebar = ctk.CTkFrame(self, width=250, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        ctk.CTkLabel(self.sidebar, text="⚙️ 시스템 설정", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(20, 10))
        self.mode_switch = ctk.CTkSwitch(self.sidebar, text="5부제 ↔ 2부제", command=self.update_mode_label,
                                         variable=self.mode_var, onvalue="2부제", offvalue="5부제")
        self.mode_switch.pack(pady=10, padx=20)
        self.lbl_mode_status = ctk.CTkLabel(self.sidebar, text="현재 모드: 5부제", text_color="cyan")
        self.lbl_mode_status.pack(pady=5)

        ctk.CTkLabel(self.sidebar, text="🔍 차량 검색", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(30, 10))
        self.search_entry = ctk.CTkEntry(self.sidebar, placeholder_text="차량번호 입력")
        self.search_entry.pack(padx=20, pady=5)
        ctk.CTkButton(self.sidebar, text="검색하기", command=self.search_vehicle).pack(padx=20, pady=5)

        # [메인 영역]
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        ctk.CTkLabel(self.main_frame, text="🚗 차량 출입 제한 관리 시스템", font=ctk.CTkFont(size=26, weight="bold")).pack(pady=10)

        self.file_frame = ctk.CTkFrame(self.main_frame)
        self.file_frame.pack(fill="x", pady=10)
        ctk.CTkButton(self.file_frame, text="파일 선택", command=self.load_record).grid(row=0, column=0, padx=10, pady=10)
        self.lbl_record = ctk.CTkLabel(self.file_frame, text="선택된 파일 없음", text_color="gray")
        self.lbl_record.grid(row=0, column=1, sticky="w")

        self.start_date_var = ctk.StringVar(value=datetime.date.today().strftime("%Y-%m-%d"))
        ctk.CTkButton(self.file_frame, text="시작일 설정", command=lambda: self.pick_date(self.start_date_var)).grid(row=1, column=0, padx=10, pady=5)
        ctk.CTkLabel(self.file_frame, textvariable=self.start_date_var).grid(row=1, column=1, sticky="w")

        self.end_date_var = ctk.StringVar(value=datetime.date.today().strftime("%Y-%m-%d"))
        ctk.CTkButton(self.file_frame, text="종료일 설정", command=lambda: self.pick_date(self.end_date_var)).grid(row=2, column=0, padx=10, pady=5)
        ctk.CTkLabel(self.file_frame, textvariable=self.end_date_var).grid(row=2, column=1, sticky="w")

        self.btn_run = ctk.CTkButton(self.main_frame, text="통합 분석 및 보고서 생성", height=60, 
                                     font=ctk.CTkFont(size=18, weight="bold"), fg_color="#2ecc71", command=self.run_analysis)
        self.btn_run.pack(fill="x", pady=20)

        self.status_box = ctk.CTkTextbox(self.main_frame, height=300)
        self.status_box.pack(fill="both", pady=10)

    def update_mode_label(self):
        self.lbl_mode_status.configure(text=f"현재 모드: {self.mode_var.get()}")

    def log(self, msg):
        self.status_box.insert("end", f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {msg}\n")
        self.status_box.see("end")
        self.update()

    def pick_date(self, var_to_update):
        top = Toplevel(self)
        top.title("날짜 선택")
        cal = Calendar(top, selectmode='day', date_pattern='y-mm-dd')
        cal.pack(pady=10, padx=10)
        ctk.CTkButton(top, text="확인", command=lambda: [var_to_update.set(cal.get_date()), top.destroy()]).pack(pady=5)

    def load_record(self):
        path = filedialog.askopenfilename(filetypes=[("엑셀파일", "*.ods *.xlsx")])
        if path:
            self.record_path = path
            self.lbl_record.configure(text=os.path.basename(path), text_color="white")

    def search_vehicle(self):
        car = self.search_entry.get().strip()
        if not car: return
        if not os.path.exists(self.history_file):
            messagebox.showinfo("결과", "기록이 없습니다.")
            return
        df = pd.read_csv(self.history_file)
        res = df[df['차량번호'].astype(str).str.contains(car)]
        if not res.empty:
            info = res.iloc[0]
            msg = f"이름: {info['이름']}\n부서: {info['부서']}\n누적: {info['누적횟수']}회\n최근: {info['최근위반일']}"
            messagebox.showinfo("조회 결과", msg)
        else:
            messagebox.showinfo("결과", "기록 없음")

    def run_analysis(self):
        if not self.record_path:
            messagebox.showwarning("경고", "파일을 선택하세요.")
            return
        
        current_mode = self.mode_var.get()
        report_name = f"최종_{current_mode}_위반보고서.xlsx"
        
        try:
            self.log(f"{current_mode} 분석 및 엑셀 꾸미기 시작...")
            df_all = pd.read_excel(self.record_path, engine='odf') if self.record_path.endswith('.ods') else pd.read_excel(self.record_path)
            
            ex_set = set()
            if os.path.exists("제외리스트.xlsx"):
                ex_set = set(pd.read_excel("제외리스트.xlsx")['차량번호'].astype(str).str.strip().tolist())

            df_all['입차일시'] = pd.to_datetime(df_all['입차일시'])
            s_str, e_str = self.start_date_var.get(), self.end_date_var.get()
            limit_dt = pd.to_datetime(e_str) + pd.Timedelta(days=1)
            df_filtered = df_all[(df_all['입차일시'] >= s_str) & (df_all['입차일시'] < limit_dt)].copy()

            df_h = pd.read_csv(self.history_file) if os.path.exists(self.history_file) else pd.DataFrame(columns=['이름', '부서', '차량번호', '누적횟수', '최근위반일'])
            df_log = pd.read_csv(self.detail_log_file) if os.path.exists(self.detail_log_file) else pd.DataFrame(columns=['날짜', '차량번호'])

            writer = pd.ExcelWriter(report_name, engine='openpyxl')
            dates = sorted(df_filtered['입차일시'].dt.date.unique())
            rules_5 = {0: [1, 6], 1: [2, 7], 2: [3, 8], 3: [4, 9], 4: [5, 0]}

            # 엑셀 서식 정의
            header_fill = PatternFill(start_color="CCE5FF", end_color="CCE5FF", fill_type="solid")
            border = Border(left=Side(style='thin'), right=Side(style='thin'), top=Side(style='thin'), bottom=Side(style='thin'))
            center_align = Alignment(horizontal='center', vertical='center')

            for d in dates:
                day_df = df_filtered[df_filtered['입차일시'].dt.date == d].copy()
                day_df['차량번호'] = day_df['차량번호'].astype(str).str.strip()
                day_df = day_df.drop_duplicates('차량번호')

                def is_violating(car_no):
                    if not car_no[-1].isdigit(): return False
                    last_digit = int(car_no[-1])
                    if current_mode == "2부제":
                        return (d.day % 2) != (last_digit % 2)
                    else:
                        if d.weekday() >= 5: return False
                        return last_digit in rules_5.get(d.weekday(), [])

                vios = day_df[day_df['차량번호'].apply(is_violating)].copy()
                vios = vios[~vios['차량번호'].isin(ex_set)]

                if not vios.empty:
                    actions = []
                    for idx, row in vios.iterrows():
                        c_no, d_str = row['차량번호'], str(d)
                        if not ((df_log['날짜'] == d_str) & (df_log['차량번호'] == c_no)).any():
                            df_log = pd.concat([df_log, pd.DataFrame({'날짜':[d_str], '차량번호':[c_no]})], ignore_index=True)
                            if c_no in df_h['차량번호'].astype(str).values:
                                h_idx = df_h[df_h['차량번호'].astype(str) == c_no].index[0]
                                df_h.at[h_idx, '누적횟수'] += 1
                                df_h.at[h_idx, '최근위반일'] = d_str
                            else:
                                nr = pd.DataFrame({'이름':[row.get('정기권성명','미확인')], '부서':[row.get('부서(동)','미확인')], '차량번호':[c_no], '누적횟수':[1], '최근위반일':[d_str]})
                                df_h = pd.concat([df_h, nr], ignore_index=True)
                        cnt = df_h[df_h['차량번호'].astype(str) == c_no]['누적횟수'].values[0]
                        actions.append(f"{cnt}회 위반")
                    
                    vios['조치사항'] = actions
                    vios.to_excel(writer, sheet_name=str(d), index=False)
                    
                    # 시트별 디자인 입히기
                    ws = writer.sheets[str(d)]
                    for col in ws.columns:
                        max_length = 0
                        col_letter = col[0].column_letter
                        for cell in col:
                            cell.border = border
                            cell.alignment = center_align
                            if cell.row == 1:
                                cell.fill = header_fill
                                cell.font = Font(bold=True)
                            if cell.value:
                                max_length = max(max_length, len(str(cell.value)))
                        ws.column_dimensions[col_letter].width = max_length + 5

            # 전체 누적 현황 시트 꾸미기
            df_h.to_excel(writer, sheet_name='전체누적현황', index=False)
            ws_h = writer.sheets['전체누적현황']
            for col in ws_h.columns:
                col_letter = col[0].column_letter
                for cell in col:
                    cell.border = border
                    cell.alignment = center_align
                    if cell.row == 1:
                        cell.fill = header_fill
                        cell.font = Font(bold=True)
                ws_h.column_dimensions[col_letter].width = 20

            writer.close()
            df_h.to_csv(self.history_file, index=False, encoding='utf-8-sig')
            df_log.to_csv(self.detail_log_file, index=False, encoding='utf-8-sig')
            self.log(f"분석 및 엑셀 서식 적용 완료!")
            messagebox.showinfo("성공", "보고서 생성 완료 (서식 적용됨)")
        except Exception as e:
            messagebox.showerror("오류", f"에러: {e}")

if __name__ == "__main__":
    app = ViolationApp()
    app.mainloop()
