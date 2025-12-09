# PlanBlock

## 시스템 아키텍처
### 계층 구조
1. Presentation Layer (View & Controller)
   
   파일: main.py, windows.py
   
   역할: 사용자 UI, 이벤트 처리, 단순 데이터 조회 기능 및 추가 팝업 창을 띄우는 기능

2. Business Layer (Logic)
   
   파일: utils.py
   
   역할: UI와 독립적인 핵심 로직 수행 (음악 파이프라인, 타이머 연산 등)

3. Data Access Layer (Data)
   
   파일: database.py
   
   역할: SQLite3 데이터베이스 연결 및 쿼리 실행

---

### 프로젝트 구조

PlanBlock/  
├── main.py             # [Entry Point] 메인 실행 파일 및 GUI 컨트롤러  
├── windows.py          # 팝업창(일정 추가, 음악 삭제 등) 클래스 정의  
├── database.py         # DB 핸들러 (SQLite 연결 및 쿼리 관리)  
├── utils.py            # 비즈니스 로직 (MusicPlayer, TimerLogic)  
├── taskTracker.db      # SQLite 데이터베이스 파일 (자동 생성됨)  
├── ffmpeg.exe          # [필수] 오디오 변환을 위한 바이너리  
├── ffprobe.exe         # [필수] 오디오 분석을 위한 바이너리  
└── README.md           # 프로젝트 일반 소개  

---

### 개발 환경 설정

1. 필수 요구 사항
   - Python 3.10이상 (3.13.x 권장)
   - FFmpeg: 프로젝트 Root 폴더에 ffmpeg.exe, ffprobe.exe 파일 필요


2. 라이브러리 설치
   - 아래 명령어를 통해 필수 의존성 설치
   ```
   pip install customtkinter tkcalendar yt-dlp pygame
   ```

3. 실행 방법
   - 터미널에서 프로젝트 root 경로로 이동 후, 아래의 명령어로 실행
   ```
   python main.py
   ```

---

### 핵심 구현 상세
1. 멀티미디어 파이프라인 (Music Player)
   - 음악 재생은 utils.py의 MusicPlayer 클래스에서 담당, 다음 파이프라인을 따릅니다
  
   Extract: yt-dlp를 사용, YouTube URL에서 오디오 트랙 정보 추출
   Convert: FFmpeg를 통해 MP3 포맷으로 실시간 변환
   Play: Pygame Mixer를 사용하여 재생  
   ** Note: GUI 프리징 방지를 위해 음악 로딩 작업은 threading 모듈을 사용, 백그라운드 데몬 스레드에서 실행됨 **

2. 타이머 (Timer)
   - tkinter의 .after() 메소드를 활용, 재귀 호출 방식을 사용하여 리소스 점유를 최소화

---

### 데이터베이스 스키마
- TRACKER: 일정 관리(Task, Date, State, Deadline)
- YOUTUBE: 음악 즐겨찾기(Name, URL)

---

### 빌드 가이드 (Build to .exe)
auto-py-to-exe 를 사용하여 실행 파일로 패키징 가능  
1. Script Location: main.py
2. Onefile: One Directory
3. Additional Files: ffmpeg.exe, ffprobe.exe를 반드시 추가  

   









