from django.test import TestCase
from core.crawlers import YTParser
from django.conf import settings
import configparser

class YTTestClass(TestCase):
    @classmethod
    def setUpTestData(cls):
        config = configparser.ConfigParser()
        config.read(settings.CONFIG_INI_PATH)
        cls.yt = YTParser(
            api=config['YOUTUBE']['KEY'],
            audio_path=settings.AUDIO_PATH,
            kaldi_path=settings.KALDI
        )
    
    def test_latest_video_list(self):
        url = 'https://www.youtube.com/user/SetiNNstation'
        result = self.yt.get_latest_videos_by_channel_link(url=url)
        self.assertTrue(len(result)>0)
    
    def test_videodata(self):
        text, description = self.yt.video2data('TKcuTkZ-Qqg')
        self.assertTrue([len(text)>0, len(description)>0], [True, True])