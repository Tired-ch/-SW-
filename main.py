from tkinter import *
import customtkinter
from tkcalendar import Calendar
from datetime import datetime, timedelta

# 분리한 모듈 임포트
import database
import windows
import utils

customtkinter.set_appearance_mode("System")
customtkinter.set_default_color_theme("blue")

class App(customtkinter.CTk):
    width = 1100
    height = 900

    def __init__(self):
        super().__init__()
        
        # 1. 초기화
        database.init_db()
        self.music_player = utils.MusicPlayer()
        self.timer_logic = utils.TimerLogic()
        
        self.pomodoro_time_left = 0
        self.pomodoro_running = False
        self.pomodoro_timer_id = None
        self.current_filter = "TODO"
        self.search_keyword = "" 

        # 2. 윈도우 설정
        self.title("PlanBlock - My Planner")
        self.geometry(f"{self.width}x{self.height}")
        self.resizable(False, False)
        
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=2)
        self.rowconfigure(0, weight=0)
        self.rowconfigure(1, weight=1)
        self.rowconfigure(2, weight=0)

        # 3. UI 구성
        self.setup_sidebar()
        self.setup_main_area()
        
        # 4. 데이터 로드
        self.update_music_list()
        self.loadTask()

    def setup_sidebar(self):
        # --- 필터 프레임 ---
        self.filter_frame = customtkinter.CTkFrame(self)
        self.filter_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        
        for text, cmd in [('To Do', 'TODO'), ('Done', 'DONE'), ('All', 'ALL')]:
            btn = customtkinter.CTkButton(self.filter_frame, text=text, 
                                        command=lambda c=cmd: self.filter_tasks(c))
            btn.pack(pady=5, padx=20, fill="x")

        # --- 작업/타이머 프레임 ---
        self.task_frame = customtkinter.CTkFrame(self)
        self.task_frame.grid(row=1, column=0, padx=20, pady=0, sticky="nsew")
        self.task_frame.columnconfigure(0, weight=1)

        customtkinter.CTkButton(self.task_frame, text='Delete Task', command=self.delTask).grid(row=0, column=0, padx=20, pady=5, sticky="ew")
        customtkinter.CTkButton(self.task_frame, text='Mark Done', command=self.markDone).grid(row=1, column=0, padx=20, pady=5, sticky="ew")
        customtkinter.CTkButton(self.task_frame, text='Mark UnDone', command=self.markUnDone).grid(row=2, column=0, padx=20, pady=5, sticky="ew")

        # 타이머 UI
        self.pomodoro_label = customtkinter.CTkLabel(self.task_frame, text="00:00", font=("Arial", 30, "bold"))
        self.pomodoro_label.grid(row=3, column=0, pady=(10, 5), sticky="ew")
        
        self.pomodoro_minutes_entry = customtkinter.CTkEntry(self.task_frame, justify="center", placeholder_text="min")
        self.pomodoro_minutes_entry.grid(row=4, column=0, padx=40, pady=5, sticky="ew")
        self.pomodoro_minutes_entry.insert(0, "25")

        pomo_btn_frame = customtkinter.CTkFrame(self.task_frame, fg_color="transparent")
        pomo_btn_frame.grid(row=5, column=0, pady=5, sticky="ew")
        pomo_btn_frame.columnconfigure((0,1), weight=1)
        
        self.btn_start_timer = customtkinter.CTkButton(pomo_btn_frame, text="Start", command=self.start_pomodoro)
        self.btn_start_timer.grid(row=0, column=0, padx=5, sticky="ew")
        self.btn_stop_timer = customtkinter.CTkButton(pomo_btn_frame, text="Stop", command=self.stop_pomodoro, state="disabled")
        self.btn_stop_timer.grid(row=0, column=1, padx=5, sticky="ew")
        self.btn_reset_timer = customtkinter.CTkButton(pomo_btn_frame, text="reset", command=self.reset_pomodoro)
        self.btn_reset_timer.grid(row=0, column=2, padx=5, sticky="ew")

        # 음악 UI
        customtkinter.CTkLabel(self.task_frame, text="Background Music", font=("Arial", 12, "bold")).grid(row=6, column=0, pady=(15,5), sticky="w", padx=20)
        
        music_sel_frame = customtkinter.CTkFrame(self.task_frame, fg_color="transparent")
        music_sel_frame.grid(row=7, column=0, padx=20, pady=5, sticky="ew")
        music_sel_frame.columnconfigure(0, weight=1)
        
        self.music_option = customtkinter.CTkComboBox(music_sel_frame, values=["Select..."])
        self.music_option.grid(row=0, column=0, sticky="ew")
        
        customtkinter.CTkButton(music_sel_frame, text="+", width=30, command=self.open_add_link).grid(row=0, column=1, padx=2)
        customtkinter.CTkButton(music_sel_frame, text="-", width=30, fg_color="#C92C2C", command=self.open_del_link).grid(row=0, column=2)

        music_ctrl_frame = customtkinter.CTkFrame(self.task_frame, fg_color="transparent")
        music_ctrl_frame.grid(row=8, column=0, padx=20, pady=(5, 20), sticky="ew")
        music_ctrl_frame.columnconfigure((0,1), weight=1)
        
        self.btn_play_music = customtkinter.CTkButton(music_ctrl_frame, text="▶ Play", fg_color="#2CC985", command=self.play_music)
        self.btn_play_music.grid(row=0, column=0, padx=5, sticky="ew")
        self.btn_stop_music = customtkinter.CTkButton(music_ctrl_frame, text="■ Stop", fg_color="#C92C2C", state="disabled", command=self.stop_music)
        self.btn_stop_music.grid(row=0, column=1, padx=5, sticky="ew")

        # --- 새 작업 추가 프레임 ---
        self.task_new = customtkinter.CTkFrame(self)
        self.task_new.grid(row=2, column=0, padx=20, pady=20, sticky="nsew")
        self.task_new.columnconfigure(0, weight=1)
        self.task_new.columnconfigure(1, weight=0)

        self.task_name_entry = customtkinter.CTkTextbox(self.task_new, height=50)
        self.task_name_entry.grid(row=0, column=0, columnspan=2, padx=10, pady=(10,5), sticky="nsew")
        self.task_name_entry.insert("1.0", "[Tag] Task Name")

        # 데드라인
        customtkinter.CTkLabel(self.task_new, text="Deadline:", font=("Arial", 11)).grid(row=1, column=0, padx=10, sticky="w")
        self.deadline_var = StringVar()
        customtkinter.CTkEntry(self.task_new, textvariable=self.deadline_var, width=100, state="readonly").grid(row=1, column=0, padx=(70,0), sticky="w")
        customtkinter.CTkButton(self.task_new, text="📅", width=30, command=self.open_date_picker).grid(row=1, column=1, padx=10)

        # 루틴
        self.routine_var = customtkinter.IntVar()
        customtkinter.CTkCheckBox(self.task_new, text="Weekly Routine (4 weeks)", variable=self.routine_var).grid(row=2, column=0, columnspan=2, padx=10, pady=5, sticky="w")
        
        customtkinter.CTkButton(self.task_new, text="Add New Task", command=self.addTask).grid(row=3, column=0, columnspan=2, padx=20, pady=10, sticky="ew")

    def setup_main_area(self):
        # 캘린더
        cal_frame = customtkinter.CTkFrame(self)
        cal_frame.grid(row=0, column=1, rowspan=1, padx=20, pady=20, sticky="nsew")
        self.calendar = Calendar(cal_frame, selectmode='day', date_pattern='y-mm-dd', background="#242424", foreground="white", bordercolor="#242424", headersbackground="#242424", normalbackground="#343638", weekendbackground="#343638", selectbackground="#3B8ED0")
        self.calendar.pack(fill="both", expand=True, padx=10, pady=10)
        self.calendar.bind("<<CalendarSelected>>", lambda e: self.loadTask())

        # 할 일 목록 프레임
        list_frame = customtkinter.CTkFrame(self)
        list_frame.grid(row=1, column=1, rowspan=2, padx=20, pady=20, sticky="nsew")
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(1, weight=1)

        # 검색바 UI
        search_frame = customtkinter.CTkFrame(list_frame, fg_color="transparent")
        search_frame.grid(row=0, column=0, padx=10, pady=(10, 0), sticky="ew")
        search_frame.columnconfigure(0, weight=1)
        
        self.search_entry = customtkinter.CTkEntry(search_frame, placeholder_text="Search tasks...")
        self.search_entry.grid(row=0, column=0, padx=(0, 10), sticky="ew")
        self.search_entry.bind("<Return>", lambda e: self.searchTask())
        
        customtkinter.CTkButton(search_frame, text="검색", width=60, command=self.searchTask).grid(row=0, column=1)

        # 리스트박스
        self.task_view_area = Listbox(list_frame, height=15, selectmode=MULTIPLE, background='#474747', font=('Times', 15), fg='white')
        self.task_view_area.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        
        self.log_label = customtkinter.CTkLabel(list_frame, text="Logger")
        self.log_label.grid(row=2, column=0, padx=20, pady=5, sticky="w")

    # --- 기능 메서드들 ---
    def open_add_link(self):
        if hasattr(self, 'add_link_window') and self.add_link_window is not None and self.add_link_window.winfo_exists():
            self.add_link_window.lift()
        else:    
            self.add_link_window = windows.AddLinkWindow(self, self.update_music_list)
    def open_del_link(self):
        if hasattr(self, 'del_link_window') and self.del_link_window is not None and self.del_link_window.winfo_exists(): 
            self.del_link_window.lift()
        else:    
            self.del_link_window = windows.DeleteLinkWindow(self, self.update_music_list)
    def open_date_picker(self): 
        if hasattr(self, 'date_picker_window') and self.date_picker_window is not None and self.date_picker_window.winfo_exists():    
            self.date_picker_window.lift()
        else:
            self.date_picker_window = windows.DatePickerWindow(self, lambda d: self.deadline_var.set(d))

    def update_music_list(self):
        rows = database.fetch_query("SELECT NAME FROM YOUTUBE")
        self.music_option.configure(values=["Select..."] + [r[0] for r in rows])

    def play_music(self):
        name = self.music_option.get()
        if name == "Select...": return
        rows = database.fetch_query("SELECT URL FROM YOUTUBE WHERE NAME=?", (name,))
        if rows:
            self.btn_play_music.configure(state="disabled")
            self.btn_stop_music.configure(state="normal")
            self.music_player.play_youtube(rows[0][0], lambda msg: self.log_label.configure(text=msg))

    def stop_music(self):
        self.music_player.stop()
        self.btn_play_music.configure(state="normal")
        self.btn_stop_music.configure(state="disabled")
        self.log_label.configure(text="Music Stopped")

    def start_pomodoro(self):
        if self.pomodoro_running: return

        if self.pomodoro_time_left == 0:
            try: 
                minutes = int(self.pomodoro_minutes_entry.get())
            except: 
                minutes = 25
            self.pomodoro_time_left = minutes * 60

        self.pomodoro_running = True
        self.btn_start_timer.configure(state="disabled")
        self.btn_stop_timer.configure(state="normal", text="Pause")

        self.countdown()

    def stop_pomodoro(self):
        if not self.pomodoro_running and self.pomodoro_timer_id is None: return

        self.pomodoro_running = False
        if self.pomodoro_timer_id:
            self.after_cancel(self.pomodoro_timer_id)
            self.pomodoro_timer_id = None
        
        self.btn_start_timer.configure(state="normal", text="Start")
        self.btn_stop_timer.configure(state="disabled", text="Pause")

    def reset_pomodoro(self):
        self.pomodoro_running = False
        if self.pomodoro_timer_id:
            self.after_cancel(self.pomodoro_timer_id)
            self.pomodoro_timer_id = None
        
        self.pomodoro_time_left = 0
        self.pomodoro_label.configure(text="00:00")
        self.btn_start_timer.configure(state="normal")
        self.btn_stop_timer.configure(state="disabled")

    def countdown(self):
        if not self.pomodoro_running: return
        if self.pomodoro_time_left > 0:
            m, s = self.timer_logic.get_minutes_seconds(self.pomodoro_time_left)
            self.pomodoro_label.configure(text=f"{m:02d}:{s:02d}")
            self.pomodoro_time_left -= 1
            self.pomodoro_timer_id = self.after(1000, self.countdown)
        else:
            self.pomodoro_label.configure(text="Time's Up!")
            self.timer_logic.play_beep()
            self.stop_pomodoro()

    # --- DB 작업 (기간 검색 로직 적용) ---
    def filter_tasks(self, state): 
        self.current_filter = state
        self.search_keyword = "" 
        self.search_entry.delete(0, END)
        self.loadTask()
    
    def searchTask(self, event=None):
        self.search_keyword = self.search_entry.get().strip()
        self.loadTask()

    def loadTask(self):
        self.task_view_area.delete(0, END)
        date = self.calendar.get_date() # 현재 선택된 날짜 (예: 2025-11-20)
        
        query = "SELECT * FROM TRACKER WHERE " 
        params = []

        query += "("

        if self.search_keyword:
            # 검색어가 있으면 날짜 무시하고 전체 검색
            query += "TASK LIKE ?"
            params.append(f"%{self.search_keyword}%")
        else:
            # [핵심 변경] 검색어가 없으면: "시작일이 오늘이거나" OR "오늘이 기간(시작~마감) 사이에 포함된" 작업 조회
            # 조건: (TASK_DATE == date) OR (DEADLINE != '' AND TASK_DATE <= date AND DEADLINE >= date)
            query += "(TASK_DATE = ?) OR (DEADLINE != '' AND TASK_DATE <= ? AND DEADLINE >= ?)"
            params.append(date)
            params.append(date)
            params.append(date)

        query += ")"

        if self.current_filter == 'TODO': query += " AND STATE = 0"
        elif self.current_filter == 'DONE': query += " AND STATE = 1"
        
        query += " ORDER BY TASK_DATE ASC"

        rows = database.fetch_query(query, params)
        
        for i, row in enumerate(rows):
            # row: [ID, TASK, STATE, START_DATE, DEADLINE]
            start_date = row[3]
            deadline = row[4]
            
            # 검색 중일 때는 원래 시작일[start_date] 표시
            prefix_str = ""
            if self.search_keyword:
                prefix_str = f"[{start_date}] "
            
            # D-Day 계산 (기준: 현재 선택한 날짜 date vs 마감일 deadline)
            # 만약 검색 모드라면 '오늘 날짜(시스템 날짜)' 기준으로 D-Day를 보여주는 게 더 자연스럽지만,
            # 여기선 일관성을 위해 캘린더 선택 날짜 기준으로 계산하거나, 
            # 검색 시에는 그냥 마감일 자체를 보여주는 게 나을 수 있음.
            # 일단 기존 로직(캘린더 날짜 기준) 유지.
            
            d_str = ""
            if deadline:
                try:
                    # 기준일: 캘린더 선택 날짜
                    target_date = datetime.strptime(date, '%Y-%m-%d').date()
                    # 마감일
                    d_date = datetime.strptime(deadline, '%Y-%m-%d').date()
                    
                    delta = (d_date - target_date).days
                    
                    if delta == 0: d_str = "[D-Day] "
                    elif delta > 0: d_str = f"[D-{delta}] "
                    else: d_str = f"[D+{-delta}] " # 마감 지남
                except: pass
            
            display_text = f"{prefix_str}{d_str}{row[1]}"
            
            self.task_view_area.insert(i, display_text)
            self.task_view_area.itemconfig(i, {'fg': 'white'})
            if row[2] == 1: self.task_view_area.itemconfig(i, {'fg': 'gray', 'bg': '#2d2d2d'})

        status_msg = f"Found {len(rows)} tasks" if self.search_keyword else f"{date} Loaded ({len(rows)})"
        self.log_label.configure(text=status_msg)

    def addTask(self):
        name = self.task_name_entry.get("1.0", END).strip()
        date = self.calendar.get_date()
        deadline = self.deadline_var.get()

        if not name or name == '[Tag] Task Name': return

        database.execute_query("INSERT INTO TRACKER (TASK,STATE,TASK_DATE,DEADLINE) VALUES (?,0,?,?)", 
                               (name, date, deadline))
        
        if self.routine_var.get() == 1:
            base = datetime.strptime(date, '%Y-%m-%d')
            for i in range(1, 5):
                next_date = (base + timedelta(weeks=i)).strftime('%Y-%m-%d')
                # 루틴은 마감일도 같이 밀려야 하는지? 보통 루틴은 마감일이 그날이므로
                # 여기서는 Deadline도 똑같이 주 단위로 밀리도록 설정 (만약 데드라인이 설정되어 있다면)
                next_deadline = ""
                if deadline:
                    base_dl = datetime.strptime(deadline, '%Y-%m-%d')
                    next_deadline = (base_dl + timedelta(weeks=i)).strftime('%Y-%m-%d')
                
                database.execute_query("INSERT INTO TRACKER (TASK,STATE,TASK_DATE,DEADLINE) VALUES (?,0,?,?)", 
                                       (f"[Routine] {name}", next_date, next_deadline))
        
        self.task_name_entry.delete("1.0", END)
        self.deadline_var.set("") 
        self.routine_var.set(0)
        self.loadTask()

    def markDone(self): self._update_state(1)
    def markUnDone(self): self._update_state(0)
    
    def _update_state(self, state):
        if not self.task_view_area.curselection(): return
        idx = self.task_view_area.curselection()[0]
        
        # [중요] 업데이트/삭제 시에도 loadTask와 똑같은 조건으로 ID를 찾아야 함
        date = self.calendar.get_date()
        query = "SELECT TASK_ID FROM TRACKER WHERE " 
        params = []

        query += "("
        if self.search_keyword:
            query += "TASK LIKE ?"
            params.append(f"%{self.search_keyword}%")
        else:
            # loadTask와 동일한 기간 조회 조건 적용
            query += "(TASK_DATE = ?) OR (DEADLINE != '' AND TASK_DATE <= ? AND DEADLINE >= ?)"
            params.append(date)
            params.append(date)
            params.append(date)
        query += ")"

        if self.current_filter == 'TODO': query += " AND STATE=0"
        elif self.current_filter == 'DONE': query += " AND STATE=1"
        query += " ORDER BY TASK_DATE ASC"
            
        rows = database.fetch_query(query, params)
        if idx < len(rows):
            database.execute_query("UPDATE TRACKER SET STATE=? WHERE TASK_ID=?", (state, rows[idx][0]))
            self.loadTask()

    def delTask(self):
        if not self.task_view_area.curselection(): return
        idx = self.task_view_area.curselection()[0]
        
        # [중요] 삭제 시에도 loadTask와 똑같은 조건으로 ID를 찾아야 함
        date = self.calendar.get_date()
        query = "SELECT TASK_ID FROM TRACKER WHERE " 
        params = []

        query += "("
        if self.search_keyword:
            query += "TASK LIKE ?"
            params.append(f"%{self.search_keyword}%")
        else:
            query += "(TASK_DATE = ?) OR (DEADLINE != '' AND TASK_DATE <= ? AND DEADLINE >= ?)"
            params.append(date)
            params.append(date)
            params.append(date)
        query += ")"

        if self.current_filter == 'TODO': query += " AND STATE=0"
        elif self.current_filter == 'DONE': query += " AND STATE=1"
        query += " ORDER BY TASK_DATE ASC"

        rows = database.fetch_query(query, params)
        if idx < len(rows):
            database.execute_query("DELETE FROM TRACKER WHERE TASK_ID=?", (rows[idx][0],))
            self.loadTask()

if __name__ == "__main__":
    app = App()
    app.mainloop()