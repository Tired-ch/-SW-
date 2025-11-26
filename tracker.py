from tkinter import *
import os
import sqlite3
import threading
import customtkinter
from tkcalendar import Calendar
import pygame
import yt_dlp
import winsound  # 윈도우용 비프음 라이브러리

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

        # 제목 입력
        self.label_name = customtkinter.CTkLabel(self, text="Title:")
        self.label_name.grid(row=0, column=0, padx=20, pady=20, sticky="e")
        self.entry_name = customtkinter.CTkEntry(self, placeholder_text="ex) Lofi Music")
        self.entry_name.grid(row=0, column=1, padx=20, pady=20, sticky="ew")

        # URL 입력
        self.label_url = customtkinter.CTkLabel(self, text="URL:")
        self.label_url.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="e")
        self.entry_url = customtkinter.CTkEntry(self, placeholder_text="Paste YouTube Link Here")
        self.entry_url.grid(row=1, column=1, padx=20, pady=(0, 20), sticky="ew")

        # 저장 버튼
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
            self.parent.update_music_list() # 메인 창의 목록 새로고침
            self.destroy() # 창 닫기

# --- 유튜브 링크 삭제 팝업창 클래스 (신규 추가) ---
class DeleteLinkWindow(customtkinter.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("Delete Music")
        self.geometry("400x300")
        self.resizable(False, False)

        self.label = customtkinter.CTkLabel(self, text="Select music to delete:")
        self.label.pack(pady=10)

        # 음악 목록 리스트박스 (tkinter 기본 위젯 사용)
        self.listbox = Listbox(self, width=40, height=10, font=("Arial", 12))
        self.listbox.pack(pady=10, padx=20)

        # 목록 채우기
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
            self.refresh_list() # 팝업창 목록 갱신
            self.parent.update_music_list() # 메인창 콤보박스 갱신

# --- 메인 애플리케이션 클래스 ---
class App(customtkinter.CTk):
    width = 1100
    height = 850 # ### 높이를 조금 늘렸습니다 (UI 공간 확보)

    def __init__(self):
        super().__init__()

        # ### 초기화
        pygame.mixer.init() # 오디오 믹서 초기화
        self.pomodoro_time_left = 0
        self.pomodoro_running = False
        self.pomodoro_timer_id = None
        self.current_filter = "TODO" 

        # configure window
        self.title("PlanBlock - My Planner")
        self.geometry(f"{self.width}x{self.height}")
        self.resizable(False, False)

        # Grid 설정 (1:2 비율)
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
        
        self.filter_to_do = customtkinter.CTkButton(
            self.filter_frame, text='To Do', command=lambda: self.filter_tasks('TODO'))
        self.filter_to_do.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        
        self.filter_done = customtkinter.CTkButton(
            self.filter_frame, text='Done', command=lambda: self.filter_tasks('DONE'))
        self.filter_done.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        
        self.filter_all = customtkinter.CTkButton(
            self.filter_frame, text='All', command=lambda: self.filter_tasks('ALL'))
        self.filter_all.grid(row=3, column=0, padx=20, pady=10, sticky="ew")

        # 2. 작업/타이머 프레임
        self.task_frame = customtkinter.CTkFrame(self)
        self.task_frame.grid(row=1, column=0, padx=(20, 20), pady=(0, 20), sticky="nsew")
        
        self.task_frame.columnconfigure(0, weight=1) # 내부 꽉 차게

        self.task_delete = customtkinter.CTkButton(
            self.task_frame, text='Delete Task', command=self.delTask)
        self.task_delete.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        
        self.task_done = customtkinter.CTkButton(
            self.task_frame, text='Mark Done', command=self.markDone)
        self.task_done.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        
        self.task_undone = customtkinter.CTkButton(
            self.task_frame, text='Mark UnDone', command=self.markUnDone)
        self.task_undone.grid(row=3, column=0, padx=20, pady=10, sticky="ew")

        # --- 뽀모도로 타이머 UI ---
        self.pomodoro_label = customtkinter.CTkLabel(self.task_frame, text="00:00",
                                                     font=customtkinter.CTkFont(size=30, weight="bold"))
        self.pomodoro_label.grid(row=4, column=0, padx=20, pady=(15, 5), sticky="ew")

        # 시간 설정 입력창
        self.pomodoro_minutes_entry = customtkinter.CTkEntry(self.task_frame, justify="center", placeholder_text="min")
        self.pomodoro_minutes_entry.grid(row=5, column=0, padx=40, pady=(0, 10), sticky="ew")
        self.pomodoro_minutes_entry.insert(0, "25") # 기본값

        # 타이머 시작/정지 버튼 프레임
        self.pomo_button_frame = customtkinter.CTkFrame(self.task_frame, fg_color="transparent")
        self.pomo_button_frame.grid(row=6, column=0, padx=20, pady=(0, 10), sticky="ew")
        self.pomo_button_frame.columnconfigure(0, weight=1)
        self.pomo_button_frame.columnconfigure(1, weight=1)

        self.pomodoro_start_button = customtkinter.CTkButton(self.pomo_button_frame, text="Start Timer", 
                                                             command=self.start_pomodoro)
        self.pomodoro_start_button.grid(row=0, column=0, padx=5, sticky="ew")
        
        self.pomodoro_stop_button = customtkinter.CTkButton(self.pomo_button_frame, text="Stop Timer", 
                                                            command=self.stop_pomodoro, state="disabled")
        self.pomodoro_stop_button.grid(row=0, column=1, padx=5, sticky="ew")

        # --- 독립적인 음악 재생 UI (타이머와 분리됨) ---
        self.music_label = customtkinter.CTkLabel(self.task_frame, text="Background Music", font=("Arial", 12, "bold"))
        self.music_label.grid(row=7, column=0, pady=(20, 5), sticky="w", padx=20)

        # 음악 선택 프레임
        self.music_select_frame = customtkinter.CTkFrame(self.task_frame, fg_color="transparent")
        self.music_select_frame.grid(row=8, column=0, padx=20, pady=(0, 5), sticky="ew")
        self.music_select_frame.columnconfigure(0, weight=1)

        # 열 비율 설정
        self.music_select_frame.columnconfigure(0, weight=1)
        self.music_select_frame.columnconfigure(0, weight=1)
        self.music_select_frame.columnconfigure(0, weight=1)

        self.music_option = customtkinter.CTkComboBox(self.music_select_frame, values=["Select Music..."])
        self.music_option.grid(row=0, column=0, padx=(0, 5), sticky="ew")
        self.music_option.set("Select Music...")

        # 음악 추가 버튼
        self.btn_add_link = customtkinter.CTkButton(self.music_select_frame, text="+", width=30, command=self.open_add_link_window)
        self.btn_add_link.grid(row=0, column=1, padx=(0,2), sticky="e")

        # 음악 제거 버튼
        self.btn_del_link = customtkinter.CTkButton(self.music_select_frame, text="-", width=30, fg_color="#C92C2C", hover_color="#992222", command=self.open_delete_link_window)
        self.btn_del_link.grid(row=0, column=2, sticky="e")

        # 음악 재생/정지 버튼 프레임
        self.music_control_frame = customtkinter.CTkFrame(self.task_frame, fg_color="transparent")
        self.music_control_frame.grid(row=9, column=0, padx=20, pady=(0, 20), sticky="ew")
        self.music_control_frame.columnconfigure(0, weight=1)
        self.music_control_frame.columnconfigure(1, weight=1)

        self.btn_play_music = customtkinter.CTkButton(self.music_control_frame, text="▶ Play Music", fg_color="#2CC985", hover_color="#229966", command=self.play_music)
        self.btn_play_music.grid(row=0, column=0, padx=5, sticky="ew")

        self.btn_stop_music = customtkinter.CTkButton(self.music_control_frame, text="■ Stop Music", fg_color="#C92C2C", hover_color="#992222", command=self.stop_music, state="disabled")
        self.btn_stop_music.grid(row=0, column=1, padx=5, sticky="ew")


        # 3. 새 작업 추가 프레임
        self.task_new = customtkinter.CTkFrame(self)
        self.task_new.grid(row=2, column=0, padx=(20, 20), pady=(0, 20), sticky="nsew")
        
        self.task_new.columnconfigure(0, weight=1)
        self.task_new.rowconfigure(0, weight=1)

        self.task_name_entry = customtkinter.CTkTextbox(self.task_new, height=100)
        self.task_name_entry.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.task_name_entry.insert("1.0", text="[Tag] Task Name")
        
        self.task_create = customtkinter.CTkButton(
            self.task_new, text="Add New Task", fg_color="transparent", border_width=2, text_color=("gray10", "#DCE4EE"), command=self.addTask)
        self.task_create.grid(row=1, column=0, padx=20, pady=10, sticky="ew")


        # =================================================
        # [오른쪽 메인 영역]
        # =================================================
        
        # 캘린더 프레임
        self.calendar_frame = customtkinter.CTkFrame(self)
        self.calendar_frame.grid(row=0, column=1, rowspan=1, padx=(20, 20), pady=(20, 20), sticky="nsew")
        
        self.calendar = Calendar(self.calendar_frame, selectmode='day', date_pattern='y-mm-dd', 
                                 background="#242424", foreground="white", headersbackground="#242424",
                                 normalbackground="#343638", weekendbackground="#343638",
                                 othermonthbackground="#343638", othermonthwebackground="#343638",
                                 selectbackground="#3B8ED0", bordercolor="#242424")
        self.calendar.pack(fill="both", expand=True, padx=10, pady=10)
        self.calendar.bind("<<CalendarSelected>>", self.on_date_select)

        # 할 일 목록 프레임
        self.task_view_frame = customtkinter.CTkFrame(self)
        self.task_view_frame.grid(row=1, column=1, rowspan=2, padx=(20, 20), pady=(0, 20), sticky="nsew")
        
        self.task_view_frame.columnconfigure(0, weight=1)
        self.task_view_frame.rowconfigure(0, weight=1)

        self.task_view_area = Listbox(self.task_view_frame, height=15, 
                                      selectmode=MULTIPLE, background='#474747', font=('Times', 15))
        self.task_view_area.grid(row=0, column=0, rowspan=1, pady=(10, 10), padx=(10, 10), sticky="nsew")

        self.log_lable = customtkinter.CTkLabel(self.task_view_frame, text="Logger", font=customtkinter.CTkFont(size=15))
        self.log_lable.grid(row=1, column=0, padx=20, pady=(0, 5), sticky="w")

        # 초기 실행
        self.connectToDb() # DB 테이블 생성 확인
        self.update_music_list() # 음악 목록 불러오기
        self.loadTask() # 오늘 날짜 할 일 불러오기

    # -----------------------------------------------------
    # [DB 및 로직]
    # -----------------------------------------------------
    
    def connectToDb(self):
        db_path = os.path.join(rootDir, 'taskTracker.db')
        conn = sqlite3.connect(db_path)
        # 할 일 테이블 생성
        conn.execute('''CREATE TABLE IF NOT EXISTS TRACKER
                    (TASK_ID INTEGER PRIMARY KEY,
                    TASK       TEXT    NOT NULL,
                    STATE      INT,
                    TASK_DATE  TEXT    NOT NULL);''')
        # 유튜브 링크 테이블 생성
        conn.execute('''CREATE TABLE IF NOT EXISTS YOUTUBE
                    (ID INTEGER PRIMARY KEY,
                    NAME TEXT NOT NULL,
                    URL  TEXT NOT NULL);''')
        conn.commit()
        return conn

    def open_add_link_window(self):
        """유튜브 링크 추가 팝업창 열기"""
        if not any(isinstance(x, AddLinkWindow) for x in self.winfo_children()):
            AddLinkWindow(self)
    
    def open_delete_link_window(self):
        """유튜브 링크 삭제 팝업창 열기"""
        if not any(isinstance(x, DeleteLinkWindow) for x in self.winfo_children()):
            DeleteLinkWindow(self)

    def update_music_list(self):
        """DB에서 유튜브 링크 목록을 가져와 콤보박스 업데이트"""
        conn = self.connectToDb()
        cursor = conn.execute("SELECT NAME FROM YOUTUBE")
        links = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        options = ["Select Music..."] + links
        self.music_option.configure(values=options)

    # -----------------------------------------------------
    # [음악 재생 기능 (타이머와 독립적)]
    # -----------------------------------------------------
    def play_music(self):
        selected_music = self.music_option.get()
        
        if selected_music == "Select Music...":
            self.log_lable.configure(text="Please select music first!")
            return

        # 버튼 상태 변경
        self.btn_play_music.configure(state="disabled")
        self.btn_stop_music.configure(state="normal")
        
        # DB에서 URL 찾기
        conn = self.connectToDb()
        cursor = conn.execute("SELECT URL FROM YOUTUBE WHERE NAME=?", (selected_music,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            url = result[0]
            # UI가 멈추지 않도록 스레드에서 다운로드 및 재생
            threading.Thread(target=self.stream_youtube_audio, args=(url,), daemon=True).start()

    def stop_music(self):
        pygame.mixer.music.stop()
        self.btn_play_music.configure(state="normal")
        self.btn_stop_music.configure(state="disabled")
        self.log_lable.configure(text="Music Stopped")

    def stream_youtube_audio(self, url):
        """yt-dlp로 오디오 URL을 추출하여 재생"""
        self.log_lable.configure(text="Loading audio... please wait")
        ydl_opts = {
            'format': 'bestaudio/best',
            'noplaylist': True,
            'quiet': True,
            'ffmpeg_location': rootDir,
            'outtmpl': os.path.join(rootDir, 'temp_audio.%(ext)s'), # 임시 파일로 저장
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info).rsplit('.', 1)[0] + '.mp3'
                
                pygame.mixer.music.load(filename)
                pygame.mixer.music.play()
                self.log_lable.configure(text=f"Playing: {info.get('title', 'Audio')}")
        except Exception as e:
            print(f"Error playing audio: {e}")
            self.log_lable.configure(text="Error: Check internet or ffmpeg")
            self.btn_play_music.configure(state="normal")
            self.btn_stop_music.configure(state="disabled")

    # -----------------------------------------------------
    # [뽀모도로 타이머 기능]
    # -----------------------------------------------------

    def start_pomodoro(self):
        if self.pomodoro_running:
            return
        
        try:
            minutes = int(self.pomodoro_minutes_entry.get())
        except ValueError:
            minutes = 25
            self.pomodoro_minutes_entry.delete(0, END)
            self.pomodoro_minutes_entry.insert(0, "25")

        self.pomodoro_time_left = minutes * 60
        self.pomodoro_running = True
        
        self.pomodoro_start_button.configure(state="disabled")
        self.pomodoro_stop_button.configure(state="normal")
        self.pomodoro_minutes_entry.configure(state="disabled")
        
        self.countdown()

    def stop_pomodoro(self):
        if not self.pomodoro_running and self.pomodoro_timer_id is None:
            return
        
        self.pomodoro_running = False
        if self.pomodoro_timer_id:
            self.after_cancel(self.pomodoro_timer_id)
            self.pomodoro_timer_id = None
        
        try:
            minutes = int(self.pomodoro_minutes_entry.get())
        except ValueError:
            minutes = 25

        self.pomodoro_label.configure(text=f"{minutes:02d}:00")
        self.pomodoro_start_button.configure(state="normal")
        self.pomodoro_stop_button.configure(state="disabled")
        self.pomodoro_minutes_entry.configure(state="normal")

    def countdown(self):
        if not self.pomodoro_running:
            return

        if self.pomodoro_time_left > 0:
            minutes, seconds = divmod(self.pomodoro_time_left, 60)
            self.pomodoro_label.configure(text=f"{minutes:02d}:{seconds:02d}")
            self.pomodoro_time_left -= 1
            self.pomodoro_timer_id = self.after(1000, self.countdown)
        else:
            # ### 타이머 종료 시 비프음 발생 (노래 X) ###
            self.pomodoro_label.configure(text="Time's Up!")
            winsound.Beep(1000, 1000) # 1000Hz 소리를 1초간 재생
            
            self.pomodoro_running = False
            self.pomodoro_start_button.configure(state="normal")
            self.pomodoro_stop_button.configure(state="disabled")
            self.pomodoro_minutes_entry.configure(state="normal")


    # -----------------------------------------------------
    # [기본 할 일 관리 로직 (이전과 동일)]
    # -----------------------------------------------------
    
    def on_date_select(self, event):
        self.loadTask()

    def filter_tasks(self, state):
        self.current_filter = state
        self.loadTask()

    def loadTask(self):
        self.task_view_area.delete(0, END)
        conn = self.connectToDb()
        state = self.current_filter
        selected_date = self.calendar.get_date()
        
        query = "SELECT * from TRACKER WHERE TASK_DATE = ?"
        params = [selected_date]

        self.task_done.configure(state="enabled")
        self.task_undone.configure(state="enabled")
        count = 0
        
        if state == 'TODO':
            query += " AND STATE = 0"
            self.task_undone.configure(state="disabled")
        elif state == 'DONE':
            query += " AND STATE = 1"
            self.task_done.configure(state="disabled")

        cursor = conn.execute(query, params)

        for i, row in enumerate(cursor):
            count = i+1
            task = (f'{row[0]} | {row[1]}\n')
            self.task_view_area.insert(i, task)
            self.task_view_area.itemconfig(i, {'fg': 'white'})
            if row[2] == 1:
                self.task_view_area.itemconfig(i, {'fg': 'black', 'bg': '#58D68D'})

        conn.close()
        self.log_lable.configure(text=f"{selected_date} : Tasks ({count})")

    def addTask(self):
        conn = self.connectToDb()
        task_name = self.task_name_entry.get("1.0", END).strip()
        selected_date = self.calendar.get_date()

        if task_name and task_name != '[Tag] Task Name':
            conn.execute("INSERT INTO TRACKER (TASK,STATE,TASK_DATE) VALUES (?, 0, ?)", (task_name, selected_date))
            conn.commit()
            self.log_lable.configure(text=f'Created >> {task_name}')
        else:
            self.log_lable.configure(text='Enter Task Name')
        conn.close()
        self.task_name_entry.delete("1.0", END)
        self.task_name_entry.insert("1.0", text="[Tag] Task Name")
        self.loadTask()

    def markDone(self):
        self.update_task_state(1)

    def markUnDone(self):
        self.update_task_state(0)

    def delTask(self):
        if len(self.task_view_area.curselection()) != 0:
            conn = self.connectToDb()
            for i in self.task_view_area.curselection():
                taskId = self.task_view_area.get(i).split(' | ')[0]
                conn.execute("DELETE from TRACKER where TASK_ID = ?", (taskId,))
            conn.commit()
            conn.close()
            self.log_lable.configure(text=f'Task Deleted')
            self.loadTask()
        else:
            self.log_lable.configure(text='Select Any Task')

    def update_task_state(self, state):
        if len(self.task_view_area.curselection()) != 0:
            conn = self.connectToDb()
            for i in self.task_view_area.curselection():
                taskId = self.task_view_area.get(i).split(' | ')[0]
                conn.execute("UPDATE TRACKER set STATE = ? where TASK_ID = ?", (state, taskId))
            conn.commit()
            conn.close()
            self.loadTask()
        else:
            self.log_lable.configure(text='Select Any Task')

if __name__ == "__main__":
    app = App()
    app.mainloop()