'''
Bing Text To Speech (TTS)
'''

import json
import uuid
import wave
import io
import hashlib
from monotonic import monotonic
from urllib import urlencode
from urllib2 import Request, urlopen, URLError, HTTPError
from bing_base import *

CACHE_SIZE = 2*1024*1024  #2M

class BingTTS():
    def __init__(self, bing_base):
        self.bing_base = bing_base

        self.locales = {
            "ar-eg": {"Female": "Microsoft Server Speech Text to Speech Voice (ar-EG, Hoda)"},
            "de-DE": {"Female": "Microsoft Server Speech Text to Speech Voice (de-DE, Hedda)", "Male": "Microsoft Server Speech Text to Speech Voice (de-DE, Stefan, Apollo)"},
            "en-AU": {"Female": "Microsoft Server Speech Text to Speech Voice (en-AU, Catherine)"},
            "en-CA": {"Female": "Microsoft Server Speech Text to Speech Voice (en-CA, Linda)"},
            "en-GB": {"Female": "Microsoft Server Speech Text to Speech Voice (en-GB, Susan, Apollo)", "Male": "Microsoft Server Speech Text to Speech Voice (en-GB, George, Apollo)"},
            "en-IN": {"Male": "Microsoft Server Speech Text to Speech Voice (en-IN, Ravi, Apollo)"},
            "en-US":{"Female": "Microsoft Server Speech Text to Speech Voice (en-US, ZiraRUS)","Male": "Microsoft Server Speech Text to Speech Voice (en-US, BenjaminRUS)"},
            "es-ES":{"Female": "Microsoft Server Speech Text to Speech Voice (es-ES, Laura, Apollo)","Male": "Microsoft Server Speech Text to Speech Voice (es-ES, Pablo, Apollo)"},
            "es-MX":{"Male": "Microsoft Server Speech Text to Speech Voice (es-MX, Raul, Apollo)"},
            "fr-CA":{"Female": "Microsoft Server Speech Text to Speech Voice (fr-CA, Caroline)"},
            "fr-FR":{"Female": "Microsoft Server Speech Text to Speech Voice (fr-FR, Julie, Apollo)","Male": "Microsoft Server Speech Text to Speech Voice (fr-FR, Paul, Apollo)"},
            "it-IT":{"Male": "Microsoft Server Speech Text to Speech Voice (it-IT, Cosimo, Apollo)"},
            "ja-JP":{"Female": "Microsoft Server Speech Text to Speech Voice (ja-JP, Ayumi, Apollo)","Male": "Microsoft Server Speech Text to Speech Voice (ja-JP, Ichiro, Apollo)"},
            "pt-BR":{"Male": "Microsoft Server Speech Text to Speech Voice (pt-BR, Daniel, Apollo)"},
            "ru-RU":{"Female": "Microsoft Server Speech Text to Speech Voice (pt-BR, Daniel, Apollo)","Male": "Microsoft Server Speech Text to Speech Voice (ru-RU, Pavel, Apollo)"},
            "zh-CN":{"Female": "Microsoft Server Speech Text to Speech Voice (zh-CN, HuihuiRUS)","Female2": "Microsoft Server Speech Text to Speech Voice (zh-CN, Yaoyao, Apollo)", "Male": "Microsoft Server Speech Text to Speech Voice (zh-CN, Kangkang, Apollo)"},
            "zh-HK":{"Female": "Microsoft Server Speech Text to Speech Voice (zh-HK, Tracy, Apollo)","Male": "Microsoft Server Speech Text to Speech Voice (zh-HK, Danny, Apollo)"},
            "zh-TW":{"Female": "Microsoft Server Speech Text to Speech Voice (zh-TW, Yating, Apollo)","Male": "Microsoft Server Speech Text to Speech Voice (zh-TW, Zhiwei, Apollo)"}
        }

        self.cache = {}

    def speak(self, text, language="en-US", gender="Female"):
        access_token = self.bing_base.token()

        if language not in self.locales.keys():
            raise LocaleError("language locale not supported.")

        lang = self.locales.get(language)

        if gender not in ["Female", "Male", "Female2"]:
            gender = "Female"

        if len(lang) == 1:
            gender = lang.keys()[0]

        service_name = lang[gender]

        hasher = hashlib.sha1()
        hasher.update(text+language+gender)
        sha1 = hasher.hexdigest()

        if sha1 in self.cache:
            print '[TTS wave from cache]'
            # [size, data, ref_cnt]
            self.cache[sha1][2] += 1
            return self.cache[sha1][1]

        body = "<speak version='1.0' xml:lang='en-us'>\
                <voice xml:lang='%s' xml:gender='%s' name='%s'>%s</voice>\
                </speak>" % (language, gender, service_name, text)

        headers = {"Content-type": "application/ssml+xml",
        			"X-Microsoft-OutputFormat": "raw-16khz-16bit-mono-pcm",
        			"Authorization": "Bearer " + access_token,
        			"X-Search-AppId": "07D3234E49CE426DAA29772419F436CA",
        			"X-Search-ClientID": str(uuid.uuid1()).replace('-',''),
        			"User-Agent": "TTSForPython"}

        url = "https://speech.platform.bing.com/synthesize"
        request = Request(url, data=body, headers=headers)
        try:
            response = urlopen(request)
        except HTTPError as e:
            raise RequestError("tts request failed: {0}".format(
                getattr(e, "reason", "status {0}".format(e.code))))  # use getattr to be compatible with Python 2.6
        except URLError as e:
            raise RequestError("tts connection failed: {0}".format(e.reason))

        data = response.read()
        size = len(data)
        print "[TTS wave length: %dkB]" %(size/1024),

        self.cache_wave(sha1, data, size)

        return data

    def _sum_cache(self):
        sum = 0
        for k,v in self.cache.items():
            sum += v[0]
        return sum

    def cache_wave(self, sha, data, size):
        overflow = self._sum_cache() + size - CACHE_SIZE
        to_be_del = []
        if overflow > 0:
            lst = sorted(self.cache.items(), key=lambda t: t[1][2])
            while overflow > 0 and len(lst) > 0:
                garbage = lst.pop(0)
                to_be_del.append(garbage[0])
                overflow -= garbage[1][0]
            for d in to_be_del:
                del self.cache[d]

        #print self.cache.keys()
        # [size, data, ref_cnt]
        self.cache[sha] = [size, data, 0]


if __name__ == '__main__':
    import sys
    try:
        from creds import BING_KEY
    except ImportError:
        print('Get a key from https://www.microsoft.com/cognitive-services/en-us/speech-api and create creds.py with the key')
        sys.exit(-1)

    from bing_base import *
    from player import Player
    import pyaudio
    import time

    pa = pyaudio.PyAudio()
    player = Player(pa)


    if len(sys.argv) != 2:
        print('Usage: %s "text"' % sys.argv[0])
        sys.exit(-1)

    bing = BingBase(BING_KEY)

    tts = BingTTS(bing)

    # recognize speech using Microsoft Bing Voice Recognition
    try:
        data = tts.speak(sys.argv[1], language='en-US')
        player.play_buffer(data)
    except LocaleError as e:
        print e
    except RequestError as e:
        print("Could not request results from Microsoft Bing Voice Recognition service; {0}".format(e))

    time.sleep(10)
    player.close()
    pa.terminate()
