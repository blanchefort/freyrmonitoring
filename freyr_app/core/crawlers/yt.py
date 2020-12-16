from pyyoutube import Api
from vosk import Model, KaldiRecognizer
import json
import os
import subprocess
import time
import youtube_dl

class YTParser:
    """Получаем информацию из Ютуба
    """
    def __init__(self, api, audio_path, kaldi_path):
        self.api = Api(api_key=api)
        self.filename = False
        self.path = audio_path
        self.kaldi_path = kaldi_path
    
    def url2id(self, url):
        return url.split('watch?v=')[1]
    
    def id2url(self, id):
        return 'https://www.youtube.com/watch?v=' + id
    
    def get_latest_videos_by_channel_link(self, url):
        """Получаем ссылки на последние видео по именной ссылке на канал
        """
        channel_name = url.split('/user/')[1]
        channel_by_id = self.api.get_channel_info(channel_name=channel_name)
        channel_info = channel_by_id.items[0].to_dict()
        uploads_plst = channel_info['contentDetails']['relatedPlaylists']['uploads']
        items = self.api.get_playlist_items(
            playlist_id=uploads_plst,
            count=100)
        videos = []
        for item in items.items:
            if item.snippet.resourceId.kind == 'youtube#video':
                videos.append({
                    'id': item.snippet.resourceId.videoId,
                    'url': self.id2url(item.snippet.resourceId.videoId)
                })
        return videos
    
    def _catch_filename(self, d):
        if d['status'] == 'finished':
            self.filename = os.path.splitext(d['filename'])[0] + '.mp3'
    
    def _downloaded_data(self):
        """Мета-данные скачанного видео
        """
        if self.filename == False:
            return False
        self.description_file = os.path.splitext(self.filename)[0] + '.info.json'
        with open(os.path.join(self.path, self.description_file)) as fp:
            description = json.load(fp)
        return {
            'id': description['id'],
            'uploader_url': description['uploader_url'],
            'channel_id': description['channel_id'],
            'channel_url': description['channel_url'],
            'upload_date': description['upload_date'],
            'title': description['title'],
            'description': description['description'],
            'webpage_url': description['webpage_url'],
            'view_count': description['view_count'],
            'like_count': description['like_count'],
            'dislike_count': description['dislike_count'],
            'average_rating': description['average_rating'],
        }
    
    def video2data(self, url):
        """Получаем распознанный текст ролика по его url
        """
        current_dir = os.getcwd()
        os.chdir(self.path)
        ydl_opts = {
            'format': 'bestaudio/best',
            'writeinfojson': 'info',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'progress_hooks': [self._catch_filename],
        }
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    
        time.sleep(20)
        video_description = self._downloaded_data()
    
        model = Model(self.kaldi_path)
        rec = KaldiRecognizer(model, 16000)

        process = subprocess.Popen([
            'ffmpeg',
            '-loglevel',
            'quiet', '-i',
            os.path.join(self.path, self.filename),
            '-ar', str(16_000),
            '-ac', '1',
            '-f', 's16le', '-'], stdout=subprocess.PIPE)

        full_text = ''
        while True:
            data = process.stdout.read(4000)
            if len(data) == 0:
                break
            if rec.AcceptWaveform(data):
                res = json.loads(rec.Result())
                full_text += ' ' + res['text']
        full_text += ' ' + json.loads(rec.FinalResult())['text']
        
        os.remove(os.path.join(self.path, self.description_file))
        os.remove(os.path.join(self.path, self.filename))

        os.chdir(current_dir)
        return full_text, video_description