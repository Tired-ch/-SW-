from tkinter import *
import os
import sqlite3
import customtkinter
from tkcalendar import Calendar  # ### <-- 캘린더 라이브러리 임포트

customtkinter.set_appearance_mode("System")
customtkinter.set_default_color_theme("blue")
rootDir = os.path.dirname(os.path.abspath(__file__))


class App(customtkinter.CTk):
    width = 900
    height = 600

    def __init__(self):
        super().__init__()

        # configure window
        self.title("PlanBlock - My Planner")  # ### <-- 타이틀 변경
        self.geometry(f"{self.width}x{self.height}")
        self.resizable(False, False)

        # configure grid layout (4x4)
        self.grid_column_configure(1, weight=1)
        self.grid_column_configure((2, 3), weight=0)
        self.grid_row_configure((0, 1, 2), weight=1)

        # ### <-- (UI 변경 1) 사이드바 프레임 재구성 (캘린더 넣을 공간 확보)

        # create sidebar1 frame (필터 버튼)
        self.filter_frame = customtkinter.CTkFrame(self)
        self.filter_frame.grid(row=0, column=0, padx=(
            20, 20), pady=(20, 20), sticky="nsew") # ### <-- pady 변경
        
        # ### <-- (로직 변경 1) 현재 필터 상태를 저장할 변수
        self.current_filter = "TODO" 
        
        # ### <-- (로직 변경 2) 버튼 커맨드를 새 함수로 변경
        self.filter_to_do = customtkinter.CTkButton(
            self.filter_frame, text='To Do', command=lambda: self.filter_tasks('TODO'))
        self.filter_to_do.grid(row=1, column=0, padx=20, pady=10, sticky="n")
        
        self.filter_done = customtkinter.CTkButton(
            self.filter_frame, text='Done', command=lambda: self.filter_tasks('DONE'))
        self.filter_done.grid(row=2, column=0, padx=20, pady=10, sticky="n")
        
        self.filter_all = customtkinter.CTkButton(
            self.filter_frame, text='All', command=lambda: self.filter_tasks('ALL'))
        self.filter_all.grid(row=3, column=0, padx=20, pady=10, sticky="n")

        # create sidebar2 frame (작업 버튼)
        self.task_frame = customtkinter.CTkFrame(self)
        self.task_frame.grid(row=1, column=0, padx=(
            20, 20), pady=(0, 20), sticky="nsew") # ### <-- pady 변경
        self.task_delete = customtkinter.CTkButton(
            self.task_frame, text='Delete Task', command=self.delTask)
        self.task_delete.grid(row=1, column=0, padx=20, pady=10)
        self.task_done = customtkinter.CTkButton(
            self.task_frame, text='Mark Done', command=self.markDone)
        self.task_done.grid(row=2, column=0, padx=20, pady=10)
        self.task_undone = customtkinter.CTkButton(
            self.task_frame, text='Mark UnDone', command=self.markUnDone)
        self.task_undone.grid(row=3, column=0, padx=20, pady=10)

        # create sidebar3 frame (새 작업 추가)
        self.task_new = customtkinter.CTkFrame(self)
        self.task_new.grid(row=2, column=0, padx=(
            20, 20), pady=(0, 20), sticky="nsew") # ### <-- pady 변경
        self.task_name_entry = customtkinter.CTkTextbox(
            self.task_new, height=100, width=150)
        self.task_name_entry.grid(row=0, column=0, padx=10, pady=10)
        self.task_name_entry.insert("1.0", text="[Tag] Task Name")
        self.task_create = customtkinter.CTkButton(
            self.task_new, text="Add New Task", fg_color="transparent", border_width=2, text_color=("gray10", "#DCE4EE"), command=self.addTask)
        self.task_create.grid(row=1, column=0, padx=20, pady=10)

        
        # ### <-- (UI 변경 2) 캘린더 프레임 생성
        self.calendar_frame = customtkinter.CTkFrame(self)
        self.calendar_frame.grid(row=0, column=1, rowspan=1, padx=(20, 20), pady=(20, 20), sticky="nsew")
        
        # ### <-- (UI 변경 3) 캘린더 위젯 생성 및 배치
        self.calendar = Calendar(self.calendar_frame, 
                                 selectmode='day', 
                                 date_pattern='y-mm-dd', # DB 저장을 위해 날짜 형식을 지정
                                 background="#242424",
                                 foreground="white",
                                 headersbackground="#242424",
                                 normalbackground="#343638",
                                 weekendbackground="#343638",
                                 othermonthbackground="#343638",
                                 othermonthwebackground="#343638",
                                 selectbackground="#3B8ED0",
                                 bordercolor="#242424")
        self.calendar.pack(fill="both", expand=True, padx=10, pady=10)
        # ### <-- (로직 변경 3) 날짜 선택 시 loadTask 함수가 호출되도록 연결
        self.calendar.bind("<<CalendarSelected>>", self.on_date_select)


        # ### <-- (UI 변경 4) Task View 프레임 위치 수정 (캘린더 아래로)
        self.task_view_frame = customtkinter.CTkFrame(self)
        self.task_view_frame.grid(row=1, column=1, rowspan=2, padx=(
            20, 20), pady=(0, 20), sticky="nsew") # ### <-- row, rowspan, pady 변경
        
        self.task_view_area = Listbox(self.task_view_frame, width=79, height=15, # ### <-- height 조절
                                      selectmode=MULTIPLE, background='#474747', font=('Times', 15))
        self.task_view_area.grid(
            row=0, column=1, rowspan=3, pady=(10, 10), padx=(10, 10), sticky="nsew") # ### <-- padding 추가

        self.log_lable = customtkinter.CTkLabel(
            self.task_view_frame, text="Logger", font=customtkinter.CTkFont(size=15))
        self.log_lable.grid(row=3, column=1, padx=20, pady=(0, 5))

        self.loadTask() # ### <-- (로직 변경 4) 시작 시 loadTask() 호출 (인자 없이)

    # ### <-- (DB 변경) connectToDb 함수: TASK_DATE 열 추가
    def connectToDb(self):
        if 'taskTracker.db' not in os.listdir(rootDir):
            conn = sqlite3.connect(os.path.join(rootDir, 'taskTracker.db'))

            conn.execute('''CREATE TABLE TRACKER
            (TASK_ID INTEGER PRIMARY KEY,
            TASK       TEXT    NOT NULL,
            STATE      INT,
            TASK_DATE  TEXT    NOT NULL);''') # ### <-- TASK_DATE 열 추가
            conn.commit()
            self.log_lable.configure(text="Created to taskTracker.db")
            return conn
        else:
            self.log_lable.configure(text="Connected to taskTracker.db")
            return sqlite3.connect(os.path.join(rootDir, 'taskTracker.db'))

    # ### <-- (로직 변경 5) 날짜 선택 시 호출될 함수
    def on_date_select(self, event):
        self.loadTask() # 리스트 새로고침

    # ### <-- (로직 변경 6) 필터 버튼 클릭 시 호출될 함수
    def filter_tasks(self, state):
        self.current_filter = state # 현재 필터 상태 저장
        self.loadTask() # 리스트 새로고침

    # ### <-- (로직 변경 7) loadTask 함수: 날짜와 필터로 DB 조회
    def loadTask(self):
        self.task_view_area.delete(0, END)
        conn = self.connectToDb()
        
        # 현재 선택된 날짜와 필터 상태를 가져옴
        state = self.current_filter
        selected_date = self.calendar.get_date()
        
        # SQL 쿼리 준비 (SQL Injection 방지를 위해 ? 사용)
        query = "SELECT * from TRACKER WHERE TASK_DATE = ?"
        params = [selected_date]

        self.task_done.configure(state="enabled")
        self.task_undone.configure(state="enabled")
        count = 0
        logText = f"{selected_date} : "
        selectedColour = '#3498DB'
        deSelectedColour = '#154360'
        colourCode = [deSelectedColour, deSelectedColour, selectedColour]

        if state == 'TODO':
            colourCode = [selectedColour, deSelectedColour, deSelectedColour]
            query += " AND STATE = 0" # 쿼리에 STATE 조건 추가
            self.task_undone.configure(state="disabled")
            logText += "To Do Task : "
        elif state == 'DONE':
            colourCode = [deSelectedColour, selectedColour, deSelectedColour]
            query += " AND STATE = 1" # 쿼리에 STATE 조건 추가
            self.task_done.configure(state="disabled")
            logText += "Completed Task : "
        else: # 'ALL'
             logText += "All Task : "

        cursor = conn.execute(query, params) # ### <-- ?에 params 값을 넣어 안전하게 실행

        for i, row in enumerate(cursor):
            count = i+1
            task = (f'{row[0]} | {row[1]}\n')
            self.task_view_area.insert(i, task)
            self.task_view_area.itemconfig(i, {'fg': 'white'})
            if row[2] == 1:
                self.task_view_area.itemconfig(
                    i, {'fg': 'black', 'bg': '#58D68D'})

        self.filter_to_do.configure(fg_color=colourCode[0])
        self.filter_done.configure(fg_color=colourCode[1])
        self.filter_all.configure(fg_color=colourCode[2])

        conn.close()
        self.log_lable.configure(text=logText+str(count))

    # ### <-- (로직 변경 8) addTask 함수: 선택된 날짜도 함께 저장
    def addTask(self):
        conn = self.connectToDb()
        task_name = self.task_name_entry.get("1.0", END).strip() # ### <-- 공백 제거
        selected_date = self.calendar.get_date() # ### <-- 현재 캘린더 날짜 가져오기

        if task_name and task_name != '[Tag] Task Name':
             # ### <-- SQL Injection 방지 및 날짜 추가
            conn.execute(
                "INSERT INTO TRACKER (TASK,STATE,TASK_DATE) VALUES (?, 0, ?)",
                (task_name, selected_date))
            conn.commit()
            self.log_lable.configure(text=f'Created >> {task_name}')
        else:
            self.log_lable.configure(text='Enter Task Name')
        conn.close()
        self.task_name_entry.delete("1.0", END)
        self.task_name_entry.insert("1.0", text="[Tag] Task Name")
        self.loadTask() # ### <-- 현재 뷰 새로고침

    # ### <-- (로직 변경 9) 모든 DB 실행 함수를 SQL Injection에 안전하게 변경
    def markDone(self):
        if len(self.task_view_area.curselection()) != 0:
            conn = self.connectToDb()
            for i in self.task_view_area.curselection():
                taskId = self.task_view_area.get(i).split(' | ')[0]
                conn.execute(
                    "UPDATE TRACKER set STATE = 1 where TASK_ID = ?", (taskId,)) # ### <-- 파라미터 방식
            conn.commit()
            conn.close()
            self.log_lable.configure(text=f'Updated as Done')
            self.loadTask() # ### <-- 필터에 맞게 새로고침
        else:
            self.log_lable.configure(text='Select Any Task')

    def markUnDone(self):
        if len(self.task_view_area.curselection()) != 0:
            conn = self.connectToDb()
            for i in self.task_view_area.curselection():
                taskId = self.task_view_area.get(i).split(' | ')[0]
                conn.execute(
                    "UPDATE TRACKER set STATE = 0 where TASK_ID = ?", (taskId,)) # ### <-- 파라미터 방식
            conn.commit()
            conn.close()
            self.log_lable.configure(text=f'Updated as Undone')
            self.loadTask() # ### <-- 필터에 맞게 새로고침
        else:
            self.log_lable.configure(text='Select Any Task')

    def delTask(self):
        if len(self.task_view_area.curselection()) != 0:
            conn = self.connectToDb()
            for i in self.task_view_area.curselection():
                taskId = self.task_view_area.get(i).split(' | ')[0]
                conn.execute(
                    "DELETE from TRACKER where TASK_ID = ?", (taskId,)) # ### <-- 파라미터 방식
            conn.commit()
            conn.close()
            self.log_lable.configure(text=f'Task Deleted')
            self.loadTask() # ### <-- 필터에 맞게 새로고침
        else:
            self.log_lable.configure(text='Select Any Task')


if __name__ == "__main__":
    app = App()
    app.mainloop()