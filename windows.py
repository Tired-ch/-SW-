import customtkinter
from tkcalendar import Calendar
import database  

# param
# customtkinter.CTkToplevel - 메인 창과 별개의 보조 창(팝업 창)을 만들 때 상속받는 클래스
class AddLinkWindow(customtkinter.CTkToplevel):
    # param
    # self - 자기자신(만들어지는 창)
    # parent - 자신을 부른 부모의 창(App의 메인 화면)
    # callback - 저장 완료 시, 실행할 함수
    def __init__(self, parent, callback): 
        super().__init__(parent)
        self.callback = callback  # 콜백 함수 저장
        self.title("Add YouTube Link")
        self.geometry("400x200")
        
        # 창 내부를 Gird로 나눌 때, 세로 열의 너비 비율
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=3)
        
        customtkinter.CTkLabel(self, text="Title:").grid(row=0, column=0, padx=20, pady=20, sticky="e")
        self.entry_name = customtkinter.CTkEntry(self, placeholder_text="ex) Lofi Music")
        self.entry_name.grid(row=0, column=1, padx=20, pady=20, sticky="ew")

        customtkinter.CTkLabel(self, text="URL:").grid(row=1, column=0, padx=20, pady=(0, 20), sticky="e")
        self.entry_url = customtkinter.CTkEntry(self, placeholder_text="Paste YouTube Link Here")
        self.entry_url.grid(row=1, column=1, padx=20, pady=(0, 20), sticky="ew")

        customtkinter.CTkButton(self, text="Save", command=self.save_link).grid(row=2, column=0, columnspan=2, padx=20, pady=10)
        self.grab_set()     # 창을 모달 상태 - 팝업창이 존재하면 메인 화면 조작X
        self.focus_force    # 창이 나오면 키보드/마우스의 포커스를 팝업 창으로 가져옴

    # 팝업 창을 통해 이름, URL을 받으면 query문을 통해 databaes에 정보를 저장
    def save_link(self):
        name = self.entry_name.get()
        url = self.entry_url.get()
        if name and url:
            database.execute_query("INSERT INTO YOUTUBE (NAME, URL) VALUES (?, ?)", (name, url))
            self.callback() # 저장 후 메인 화면의 목록 갱신 함수 실행
            self.destroy()

# param
# customtkinter.CTkToplevel 상속 - 메인 창이 아닌 팝업 창을 의미
class DeleteLinkWindow(customtkinter.CTkToplevel):
    
    def __init__(self, parent, callback):
        super().__init__(parent)
        self.callback = callback
        self.title("Delete Music")
        self.geometry("400x300")
        
        customtkinter.CTkLabel(self, text="Select music to delete:").pack(pady=10)
        
        from tkinter import Listbox, END
        self.listbox = Listbox(self, width=40, height=10, font=("Arial", 12))
        self.listbox.pack(pady=10, padx=20)
        
        self.refresh_list()
        customtkinter.CTkButton(self, text="Delete Selected", fg_color="#C92C2C", hover_color="#992222", command=self.delete_link).pack(pady=10)
        self.grab_set()
        self.focus_force()

    def refresh_list(self):
        from tkinter import END
        self.listbox.delete(0, END)
        rows = database.fetch_query("SELECT NAME FROM YOUTUBE")
        for row in rows:
            self.listbox.insert(END, row[0])

    def delete_link(self):
        selection = self.listbox.curselection()
        if selection:
            name = self.listbox.get(selection[0])
            database.execute_query("DELETE FROM YOUTUBE WHERE NAME=?", (name,))
            self.refresh_list()
            self.callback() # 삭제 후 메인 화면 목록 갱신

# param
# customtkinter.CTkToplevel 상속 - 메인 창이 아닌 팝업 창을 의미
class DatePickerWindow(customtkinter.CTkToplevel):
    def __init__(self, parent, callback):
        super().__init__(parent)
        self.callback = callback
        self.title("Pick Date")
        self.geometry("300x300")
        
        self.cal = Calendar(self, selectmode='day', date_pattern='y-mm-dd')
        self.cal.pack(pady=20, padx=20, fill="both", expand=True)
        customtkinter.CTkButton(self, text="Select", command=self.select_date).pack(pady=10)

        self.grab_set()
        self.focus_force()

    def select_date(self):
        self.callback(self.cal.get_date()) # 선택된 날짜를 메인 화면으로 전달
        self.destroy()