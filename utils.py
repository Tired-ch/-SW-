import pygame
import yt_dlp
import os
import threading
import winsound
import time

# ffmpeg 경로 설정을 위해 rootDir 필요
rootDir = os.path.dirname(os.path.abspath(__file__))

class MusicPlayer:
    def __init__(self):
        pygame.mixer.init()

    def play_youtube(self, url, status_callback):
        """별도 스레드에서 음악 다운로드 및 재생"""
        threading.Thread(target=self._stream_audio, args=(url, status_callback), daemon=True).start()

    def _stream_audio(self, url, status_callback):
        # 다운로드 전 기존 파일 잠금 해제
        try:
            pygame.mixer.music.stop() # 1. 재생 중지
            pygame.mixer.music.unload() # 2. 파일 unload
        except Exception:
            pass # 재생 중인 게 없으면 패스
            
        # 혹시 파일이 바로 안 풀릴 수 있으니 0.1초 대기
        time.sleep(0.1) 
        
        # 파일이 이미 있다면 삭제 - 새 노래를 받기 위함
        # 파일을 여전히 사용 중이라면 에러 메시지 띄우고 중단
        temp_path = os.path.join(rootDir, 'temp_audio.mp3')
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except PermissionError:
                status_callback("Error: File locked. Please wait or restart.")
                return

        status_callback("Loading audio...")
        
        # yt-dlp 다운로드 옵션 설정
        ydl_opts = {
            'format': 'bestaudio/best',
            'noplaylist': True,
            'quiet': True,
            'ffmpeg_location': rootDir,
            'outtmpl': os.path.join(rootDir, 'temp_audio.%(ext)s'),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            # 유튜브 차단 우회 설정
            'extractor_args': {
                'youtube': {
                    'player_client': ['android', 'web'],
                    'skip': ['hls', 'dash']
                }
            }
        }
        
        try:
            # 설정대로 다운로드
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = os.path.join(rootDir, 'temp_audio.mp3')
                
                # pygame 플레이어에 load 후 재생
                pygame.mixer.music.load(filename)
                pygame.mixer.music.play()
                status_callback(f"Playing: {info.get('title', 'Audio')}")
        except Exception as e:
            print(f"Error: {e}")
            status_callback("Error: Check ffmpeg/internet")

    def stop(self):
        pygame.mixer.music.stop()
        try:
            pygame.mixer.music.unload() # 정지 버튼 눌렀을 때도 파일 놓아주기
        except:
            pass

class TimerLogic:
    def __init__(self):
        pass
    # Second(초) 데이터를 받고 (분, 초)로 분리
    def get_minutes_seconds(self, total_seconds):
        return divmod(total_seconds, 60)

    # Beep 음을 1초동안 재생
    def play_beep(self):
        winsound.Beep(1000, 1000)