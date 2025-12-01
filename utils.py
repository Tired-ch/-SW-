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
        # ### [핵심 수정] 다운로드 전 기존 파일 잠금 해제 ###
        try:
            pygame.mixer.music.stop() # 1. 재생 중지
            pygame.mixer.music.unload() # 2. 파일 놓아주기 (중요!)
        except Exception:
            pass # 재생 중인 게 없으면 패스
            
        # 혹시 파일이 바로 안 풀릴 수 있으니 0.1초 대기
        time.sleep(0.1) 
        
        # 파일이 여전히 잠겨있는지 확인하고 삭제 시도 (청소)
        temp_path = os.path.join(rootDir, 'temp_audio.mp3')
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except PermissionError:
                status_callback("Error: File locked. Please wait or restart.")
                return

        status_callback("Loading audio...")
        
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
            'extractor_args': {
                'youtube': {
                    'player_client': ['android', 'web'],
                    'skip': ['hls', 'dash']
                }
            }
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                # 파일명이 고정값이 아니라 ID가 붙을 수도 있으므로 실제 생성된 파일명 찾기
                # 하지만 outtmpl을 고정했으므로 temp_audio.mp3가 생성됨
                filename = os.path.join(rootDir, 'temp_audio.mp3')
                
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
    
    def get_minutes_seconds(self, total_seconds):
        return divmod(total_seconds, 60)

    def play_beep(self):
        winsound.Beep(1000, 1000)