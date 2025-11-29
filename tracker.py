from tkinter import *
import os
import sqlite3
import threading
from datetime import datetime, timedelta # 날짜 계산을 위해 추가
import customtkinter
from tkcalendar import Calendar, DateEntry # DateEntry 추가
import pygame
import yt_dlp
import winsound

# --- 설정 ---
customtkinter.set_appearance_mode("System")
customtkinter.set_default_color_theme("blue")
rootDir = os.path.dirname(os.path.abspath(__file__))

# --- 유튜브 링크 추가 팝업창 클래스 ---
class AddLinkWindow(customtkinter.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("Add YouTube Link")
        self.geometry("400x200")
        self.resizable(False, False)
        
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=3)

        self.label_name = customtkinter.CTkLabel(self, text="Title:")
        self.label_name.grid(row=0, column=0, padx=20, pady=20, sticky="e")
        self.entry_name = customtkinter.CTkEntry(self, placeholder_text="ex) Lofi Music")
        self.entry_name.grid(row=0, column=1, padx=20, pady=20, sticky="ew")

        self.label_url = customtkinter.CTkLabel(self, text="URL:")
        self.label_url.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="e")
        self.entry_url = customtkinter.CTkEntry(self, placeholder_text="Paste YouTube Link Here")
        self.entry_url.grid(row=1, column=1, padx=20, pady=(0, 20), sticky="ew")

        self.btn_save = customtkinter.CTkButton(self, text="Save", command=self.save_link)
        self.btn_save.grid(row=2, column=0, columnspan=2, padx=20, pady=10)

    def save_link(self):
        name = self.entry_name.get()
        url = self.entry_url.get()
        if name and url:
            conn = self.parent.connectToDb()
            conn.execute("INSERT INTO YOUTUBE (NAME, URL) VALUES (?, ?)", (name, url))
            conn.commit()
            conn.close()
            self.parent.update_music_list()
            self.destroy()

# --- 유튜브 링크 삭제 팝업창 클래스 ---
class DeleteLinkWindow(customtkinter.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("Delete Music")
        self.geometry("400x300")
        self.resizable(False, False)

        self.label = customtkinter.CTkLabel(self, text="Select music to delete:")
        self.label.pack(pady=10)

        self.listbox = Listbox(self, width=40, height=10, font=("Arial", 12))
        self.listbox.pack(pady=10, padx=20)
        self.refresh_list()

        self.btn_delete = customtkinter.CTkButton(self, text="Delete Selected", fg_color="#C92C2C", hover_color="#992222", command=self.delete_link)
        self.btn_delete.pack(pady=10)

    def refresh_list(self):
        self.listbox.delete(0, END)
        conn = self.parent.connectToDb()
        cursor = conn.execute("SELECT NAME FROM YOUTUBE")
        for row in cursor.fetchall():
            self.listbox.insert(END, row[0])
        conn.close()

    def delete_link(self):
        selection = self.listbox.curselection()
        if selection:
            name = self.listbox.get(selection[0])
            conn = self.parent.connectToDb()
            conn.execute("DELETE FROM YOUTUBE WHERE NAME=?", (name,))
            conn.commit()
            conn.close()
            self.refresh_list()
            self.parent.update_music_list()

# --- 메인 애플리케이션 클래스 ---
class App(customtkinter.CTk):
    width = 1100
    height = 850

    def __init__(self):
        super().__init__()

        pygame.mixer.init()
        self.pomodoro_time_left = 0
        self.pomodoro_running = False
        self.pomodoro_timer_id = None
        self.current_filter = "TODO" 

        self.title("PlanBlock - My Planner")
        self.geometry(f"{self.width}x{self.height}")
        self.resizable(False, False)

        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=2)
        self.rowconfigure(0, weight=0)
        self.rowconfigure(1, weight=1)
        self.rowconfigure(2, weight=0)

        # =================================================
        # [왼쪽 사이드바]
        # =================================================
        
        # 1. 필터 프레임
        self.filter_frame = customtkinter.CTkFrame(self)
        self.filter_frame.grid(row=0, column=0, padx=(20, 20), pady=(20, 20), sticky="nsew")
        
        self.filter_to_do = customtkinter.CTkButton(self.filter_frame, text='To Do', command=lambda: self.filter_tasks('TODO'))
        self.filter_to_do.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        self.filter_done = customtkinter.CTkButton(self.filter_frame, text='Done', command=lambda: self.filter_tasks('DONE'))
        self.filter_done.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        self.filter_all = customtkinter.CTkButton(self.filter_frame, text='All', command=lambda: self.filter_tasks('ALL'))
        self.filter_all.grid(row=3, column=0, padx=20, pady=10, sticky="ew")

        # 2. 작업/타이머 프레임
        self.task_frame = customtkinter.CTkFrame(self)
        self.task_frame.grid(row=1, column=0, padx=(20, 20), pady=(0, 20), sticky="nsew")
        self.task_frame.columnconfigure(0, weight=1)

        self.task_delete = customtkinter.CTkButton(self.task_frame, text='Delete Task', command=self.delTask)
        self.task_delete.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        self.task_done = customtkinter.CTkButton(self.task_frame, text='Mark Done', command=self.markDone)
        self.task_done.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        self.task_undone = customtkinter.CTkButton(self.task_frame, text='Mark UnDone', command=self.markUnDone)
        self.task_undone.grid(row=3, column=0, padx=20, pady=10, sticky="ew")

        self.pomodoro_label = customtkinter.CTkLabel(self.task_frame, text="00:00", font=customtkinter.CTkFont(size=30, weight="bold"))
        self.pomodoro_label.grid(row=4, column=0, padx=20, pady=(15, 5), sticky="ew")

        self.pomodoro_minutes_entry = customtkinter.CTkEntry(self.task_frame, justify="center", placeholder_text="min")
        self.pomodoro_minutes_entry.grid(row=5, column=0, padx=40, pady=(0, 10), sticky="ew")
        self.pomodoro_minutes_entry.insert(0, "25")

        self.pomo_button_frame = customtkinter.CTkFrame(self.task_frame, fg_color="transparent")
        self.pomo_button_frame.grid(row=6, column=0, padx=20, pady=(0, 10), sticky="ew")
        self.pomo_button_frame.columnconfigure(0, weight=1)
        self.pomo_button_frame.columnconfigure(1, weight=1)

        self.pomodoro_start_button = customtkinter.CTkButton(self.pomo_button_frame, text="Start Timer", command=self.start_pomodoro)
        self.pomodoro_start_button.grid(row=0, column=0, padx=5, sticky="ew")
        self.pomodoro_stop_button = customtkinter.CTkButton(self.pomo_button_frame, text="Stop Timer", command=self.stop_pomodoro, state="disabled")
        self.pomodoro_stop_button.grid(row=0, column=1, padx=5, sticky="ew")

        self.music_label = customtkinter.CTkLabel(self.task_frame, text="Background Music", font=("Arial", 12, "bold"))
        self.music_label.grid(row=7, column=0, pady=(20, 5), sticky="w", padx=20)

        self.music_select_frame = customtkinter.CTkFrame(self.task_frame, fg_color="transparent")
        self.music_select_frame.grid(row=8, column=0, padx=20, pady=(0, 5), sticky="ew")
        self.music_select_frame.columnconfigure(0, weight=1)
        self.music_select_frame.columnconfigure(1, weight=0)
        self.music_select_frame.columnconfigure(2, weight=0)

        self.music_option = customtkinter.CTkComboBox(self.music_select_frame, values=["Select Music..."])
        self.music_option.grid(row=0, column=0, padx=(0, 5), sticky="ew")
        self.music_option.set("Select Music...")

        self.btn_add_link = customtkinter.CTkButton(self.music_select_frame, text="+", width=30, command=self.open_add_link_window)
        self.btn_add_link.grid(row=0, column=1, padx=(0, 2), sticky="e")
        self.btn_del_link = customtkinter.CTkButton(self.music_select_frame, text="-", width=30, fg_color="#C92C2C", hover_color="#992222", command=self.open_delete_link_window)
        self.btn_del_link.grid(row=0, column=2, sticky="e")

        self.music_control_frame = customtkinter.CTkFrame(self.task_frame, fg_color="transparent")
        self.music_control_frame.grid(row=9, column=0, padx=20, pady=(0, 20), sticky="ew")
        self.music_control_frame.columnconfigure(0, weight=1)
        self.music_control_frame.columnconfigure(1, weight=1)

        self.btn_play_music = customtkinter.CTkButton(self.music_control_frame, text="▶ Play", fg_color="#2CC985", hover_color="#229966", command=self.play_music)
        self.btn_play_music.grid(row=0, column=0, padx=5, sticky="ew")
        self.btn_stop_music = customtkinter.CTkButton(self.music_control_frame, text="■ Stop", fg_color="#C92C2C", hover_color="#992222", command=self.stop_music, state="disabled")
        self.btn_stop_music.grid(row=0, column=1, padx=5, sticky="ew")

        # 3. 새 작업 추가 프레임 (D-day 및 루틴 기능 추가)
        self.task_new = customtkinter.CTkFrame(self)
        self.task_new.grid(row=2, column=0, padx=(20, 20), pady=(0, 20), sticky="nsew")
        self.task_new.columnconfigure(0, weight=1)
        self.task_new.columnconfigure(1, weight=1) # 2열 구조로 변경

        # [변경] 텍스트 입력창 높이 줄임
        self.task_name_entry = customtkinter.CTkTextbox(self.task_new, height=50) 
        self.task_name_entry.grid(row=0, column=0, columnspan=2, padx=10, pady=(10, 5), sticky="nsew")
        self.task_name_entry.insert("1.0", text="[Tag] Task Name")

        # [신규] D-Day 설정 라벨 및 DateEntry
        self.label_deadline = customtkinter.CTkLabel(self.task_new, text="Deadline:", font=("Arial", 11))
        self.label_deadline.grid(row=1, column=0, padx=10, sticky="w")
        
        self.deadline_entry = DateEntry(self.task_new, width=12, background='darkblue', foreground='white', borderwidth=2, date_pattern='y-mm-dd')
        self.deadline_entry.grid(row=1, column=1, padx=10, sticky="e")

        # [신규] 루틴 체크박스
        self.routine_var = customtkinter.IntVar()
        self.check_routine = customtkinter.CTkCheckBox(self.task_new, text="Weekly Routine (4 weeks)", variable=self.routine_var)
        self.check_routine.grid(row=2, column=0, columnspan=2, padx=10, pady=5, sticky="w")

        self.task_create = customtkinter.CTkButton(self.task_new, text="Add New Task", fg_color="transparent", border_width=2, text_color=("gray10", "#DCE4EE"), command=self.addTask)
        self.task_create.grid(row=3, column=0, columnspan=2, padx=20, pady=10, sticky="ew")


        # =================================================
        # [오른쪽 메인 영역]
        # =================================================
        
        self.calendar_frame = customtkinter.CTkFrame(self)
        self.calendar_frame.grid(row=0, column=1, rowspan=1, padx=(20, 20), pady=(20, 20), sticky="nsew")
        self.calendar = Calendar(self.calendar_frame, selectmode='day', date_pattern='y-mm-dd', 
                                 background="#242424", foreground="white", headersbackground="#242424",
                                 normalbackground="#343638", weekendbackground="#343638",
                                 othermonthbackground="#343638", othermonthwebackground="#343638",
                                 selectbackground="#3B8ED0", bordercolor="#242424")
        self.calendar.pack(fill="both", expand=True, padx=10, pady=10)
        self.calendar.bind("<<CalendarSelected>>", self.on_date_select)

        self.task_view_frame = customtkinter.CTkFrame(self)
        self.task_view_frame.grid(row=1, column=1, rowspan=2, padx=(20, 20), pady=(0, 20), sticky="nsew")
        self.task_view_frame.columnconfigure(0, weight=1)
        self.task_view_frame.rowconfigure(0, weight=1)

        self.task_view_area = Listbox(self.task_view_frame, height=15, selectmode=MULTIPLE, background='#474747', font=('Times', 15))
        self.task_view_area.grid(row=0, column=0, rowspan=1, pady=(10, 10), padx=(10, 10), sticky="nsew")

        self.log_lable = customtkinter.CTkLabel(self.task_view_frame, text="Logger", font=customtkinter.CTkFont(size=15))
        self.log_lable.grid(row=1, column=0, padx=20, pady=(0, 5), sticky="w")

        self.connectToDb()
        self.update_music_list()
        self.loadTask()

    # -----------------------------------------------------
    # [DB 및 로직]
    # -----------------------------------------------------
    
    def connectToDb(self):
        db_path = os.path.join(rootDir, 'taskTracker.db')
        conn = sqlite3.connect(db_path)
        # DEADLINE 열 추가
        conn.execute('''CREATE TABLE IF NOT EXISTS TRACKER
                    (TASK_ID INTEGER PRIMARY KEY,
                    TASK       TEXT    NOT NULL,
                    STATE      INT,
                    TASK_DATE  TEXT    NOT NULL,
                    DEADLINE   TEXT);''')
        conn.execute('''CREATE TABLE IF NOT EXISTS YOUTUBE
                    (ID INTEGER PRIMARY KEY,
                    NAME TEXT NOT NULL,
                    URL  TEXT NOT NULL);''')
        conn.commit()
        return conn

    def open_add_link_window(self):
        if not any(isinstance(x, AddLinkWindow) for x in self.winfo_children()):
            AddLinkWindow(self)

    def open_delete_link_window(self):
        if not any(isinstance(x, DeleteLinkWindow) for x in self.winfo_children()):
            DeleteLinkWindow(self)

    def update_music_list(self):
        conn = self.connectToDb()
        cursor = conn.execute("SELECT NAME FROM YOUTUBE")
        links = [row[0] for row in cursor.fetchall()]
        conn.close()
        options = ["Select Music..."] + links
        self.music_option.configure(values=options)

    # --- 음악 재생 ---
    def play_music(self):
        selected_music = self.music_option.get()
        if selected_music == "Select Music...":
            self.log_lable.configure(text="Please select music first!")
            return
        self.btn_play_music.configure(state="disabled")
        self.btn_stop_music.configure(state="normal")
        conn = self.connectToDb()
        cursor = conn.execute("SELECT URL FROM YOUTUBE WHERE NAME=?", (selected_music,))
        result = cursor.fetchone()
        conn.close()
        if result:
            threading.Thread(target=self.stream_youtube_audio, args=(result[0],), daemon=True).start()

    def stop_music(self):
        pygame.mixer.music.stop()
        self.btn_play_music.configure(state="normal")
        self.btn_stop_music.configure(state="disabled")
        self.log_lable.configure(text="Music Stopped")

    def stream_youtube_audio(self, url):
        self.log_lable.configure(text="Loading audio... please wait")
        ydl_opts = {
            'format': 'bestaudio/best',
            'noplaylist': True,
            'quiet': True,
            'ffmpeg_location': rootDir,
            'outtmpl': os.path.join(rootDir, 'temp_audio.%(ext)s'),
            'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}],
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info).rsplit('.', 1)[0] + '.mp3'
                pygame.mixer.music.load(filename)
                pygame.mixer.music.play()
                self.log_lable.configure(text=f"Playing: {info.get('title', 'Audio')}")
        except Exception as e:
            print(f"Error: {e}")
            self.log_lable.configure(text="Error: ffmpeg not found?")
            self.btn_play_music.configure(state="normal")
            self.btn_stop_music.configure(state="disabled")

    # --- 타이머 ---
    def start_pomodoro(self):
        if self.pomodoro_running: return
        try: minutes = int(self.pomodoro_minutes_entry.get())
        except ValueError: minutes = 25
        self.pomodoro_time_left = minutes * 60
        self.pomodoro_running = True
        self.pomodoro_start_button.configure(state="disabled")
        self.pomodoro_stop_button.configure(state="normal")
        self.pomodoro_minutes_entry.configure(state="disabled")
        self.countdown()

    def stop_pomodoro(self):
        if not self.pomodoro_running and self.pomodoro_timer_id is None: return
        self.pomodoro_running = False
        if self.pomodoro_timer_id:
            self.after_cancel(self.pomodoro_timer_id)
            self.pomodoro_timer_id = None
        try: minutes = int(self.pomodoro_minutes_entry.get())
        except ValueError: minutes = 25
        self.pomodoro_label.configure(text=f"{minutes:02d}:00")
        self.pomodoro_start_button.configure(state="normal")
        self.pomodoro_stop_button.configure(state="disabled")
        self.pomodoro_minutes_entry.configure(state="normal")

    def countdown(self):
        if not self.pomodoro_running: return
        if self.pomodoro_time_left > 0:
            minutes, seconds = divmod(self.pomodoro_time_left, 60)
            self.pomodoro_label.configure(text=f"{minutes:02d}:{seconds:02d}")
            self.pomodoro_time_left -= 1
            self.pomodoro_timer_id = self.after(1000, self.countdown)
        else:
            self.pomodoro_label.configure(text="Time's Up!")
            winsound.Beep(1000, 1000)
            self.stop_pomodoro()

    # --- 할 일 관리 (D-Day, Routine 추가됨) ---
    def on_date_select(self, event): self.loadTask()
    def filter_tasks(self, state): self.current_filter = state; self.loadTask()

    def loadTask(self):
        self.task_view_area.delete(0, END)
        conn = self.connectToDb()
        selected_date = self.calendar.get_date()
        query = "SELECT * from TRACKER WHERE TASK_DATE = ?"
        if self.current_filter == 'TODO': query += " AND STATE = 0"
        elif self.current_filter == 'DONE': query += " AND STATE = 1"
        
        cursor = conn.execute(query, [selected_date])
        for i, row in enumerate(cursor):
            task_text = row[1]
            deadline = row[4] # DEADLINE 컬럼
            
            # D-Day 계산 및 표시
            d_day_str = ""
            if deadline:
                try:
                    d_date = datetime.strptime(deadline, '%Y-%m-%d').date()
                    c_date = datetime.strptime(selected_date, '%Y-%m-%d').date()
                    delta = (d_date - c_date).days
                    
                    if delta == 0: d_day_str = "[D-Day] "
                    elif delta > 0: d_day_str = f"[D-{delta}] "
                    else: d_day_str = f"[D+{-delta}] "
                except ValueError: pass

            display_text = f"{d_day_str}{task_text}"
            self.task_view_area.insert(i, display_text)
            self.task_view_area.itemconfig(i, {'fg': 'white'})
            if row[2] == 1: self.task_view_area.itemconfig(i, {'fg': 'black', 'bg': '#58D68D'})
        conn.close()
        self.log_lable.configure(text=f"{selected_date} Tasks loaded")

    def addTask(self):
        conn = self.connectToDb()
        task_name = self.task_name_entry.get("1.0", END).strip()
        selected_date = self.calendar.get_date()
        deadline_date = self.deadline_entry.get_date().strftime('%Y-%m-%d')
        is_routine = self.routine_var.get()

        if task_name and task_name != '[Tag] Task Name':
            # 1. 현재 날짜에 작업 추가
            conn.execute("INSERT INTO TRACKER (TASK,STATE,TASK_DATE,DEADLINE) VALUES (?, 0, ?, ?)", 
                         (task_name, selected_date, deadline_date))
            
            # 2. 루틴 체크 시, 향후 4주간 같은 요일에 자동 추가
            if is_routine == 1:
                base_date = datetime.strptime(selected_date, '%Y-%m-%d')
                for i in range(1, 5): # 1주후, 2주후 ... 4주후
                    next_date = base_date + timedelta(weeks=i)
                    next_date_str = next_date.strftime('%Y-%m-%d')
                    conn.execute("INSERT INTO TRACKER (TASK,STATE,TASK_DATE,DEADLINE) VALUES (?, 0, ?, ?)", 
                                 (f"[Routine] {task_name}", next_date_str, deadline_date))
            
            conn.commit()
            self.log_lable.configure(text=f'Created: {task_name}')
        conn.close()
        self.task_name_entry.delete("1.0", END)
        self.task_name_entry.insert("1.0", text="[Tag] Task Name")
        self.loadTask()

    def markDone(self): self.update_task_state(1)
    def markUnDone(self): self.update_task_state(0)
    
    def delTask(self):
        # Task 이름으로 삭제 (표시된 텍스트에서 D-Day 태그 제거하고 검색해야 정확함. 간단히 구현을 위해 이름 매칭 사용)
        # 주의: 현재 구조상 완벽한 ID 매칭이 어려워 선택된 텍스트의 일부로 삭제하거나, 
        # 로직을 더 강화해야 하지만, 여기선 리스트 인덱스로 삭제하는 로직이 없으므로
        # 가장 간단하게 선택된 항목을 DB에서 지우는 로직으로 유지합니다.
        # (기존 코드의 로직을 그대로 유지하되, D-Day 문자열 처리가 필요할 수 있음)
        if not self.task_view_area.curselection(): return
        
        conn = self.connectToDb()
        # 화면에 보이는 텍스트 그대로 가져옴 ([D-3] Task...)
        # DB에는 "Task"로 저장되어 있으므로 매칭이 안될 수 있음.
        # 개선된 삭제 로직: 현재 날짜의 Task 중 순서대로 삭제 (ID 기반이 가장 좋음)
        # 여기서는 간단히 현재 날짜의 모든 task를 가져와 인덱스로 매칭
        idx = self.task_view_area.curselection()[0]
        
        selected_date = self.calendar.get_date()
        query = "SELECT TASK_ID FROM TRACKER WHERE TASK_DATE = ?"
        if self.current_filter == 'TODO': query += " AND STATE = 0"
        elif self.current_filter == 'DONE': query += " AND STATE = 1"
        
        cursor = conn.execute(query, [selected_date])
        rows = cursor.fetchall()
        
        if idx < len(rows):
            task_id = rows[idx][0]
            conn.execute("DELETE FROM TRACKER WHERE TASK_ID = ?", (task_id,))
            conn.commit()
            self.log_lable.configure(text='Task Deleted')
        
        conn.close()
        self.loadTask()

    def update_task_state(self, state):
        if not self.task_view_area.curselection(): return
        conn = self.connectToDb()
        idx = self.task_view_area.curselection()[0]
        
        selected_date = self.calendar.get_date()
        query = "SELECT TASK_ID FROM TRACKER WHERE TASK_DATE = ?"
        if self.current_filter == 'TODO': query += " AND STATE = 0"
        elif self.current_filter == 'DONE': query += " AND STATE = 1"
        
        cursor = conn.execute(query, [selected_date])
        rows = cursor.fetchall()
        
        if idx < len(rows):
            task_id = rows[idx][0]
            conn.execute("UPDATE TRACKER set STATE = ? where TASK_ID = ?", (state, task_id))
            conn.commit()
        conn.close()
        self.loadTask()

if __name__ == "__main__":
    app = App()
    app.mainloop()