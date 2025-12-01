# 파이썬 내장 DB 사용, os의 파일 경로 처리
import sqlite3
import os

rootDir = os.path.dirname(os.path.abspath(__file__))  # 실행중인 이 파일이 위치한 폴더의 절대 경로
DB_PATH = os.path.join(rootDir, 'taskTracker.db')     # rootDir 와 db 파일을 join

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute('''CREATE TABLE IF NOT EXISTS TRACKER
                (TASK_ID INTEGER PRIMARY KEY,
                TASK     TEXT    NOT NULL,
                STATE    INT,
                TASK_DATE TEXT   NOT NULL,
                DEADLINE  TEXT);''')
    conn.execute('''CREATE TABLE IF NOT EXISTS YOUTUBE
                (ID    INTEGER     PRIMARY KEY,
                NAME   TEXT    NOT NULL,
                URL    TEXT    NOT NULL);''')
    conn.commit()
    conn.close()

# param
# query: 실행할 SQL 명령어  / params: 명령어의 ? 부분에 채워 넣을 데이터들
def execute_query(query, params=()):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(query, params)
    conn.commit()
    conn.close()

# param
# query: 실행할 SQL 명령어 / params: 명령어의 ? 부분에 채워 넣을 데이터
def fetch_query(query, params=()):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return rows