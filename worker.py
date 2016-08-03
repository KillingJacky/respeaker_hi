"""
This is the worker thread which handles the input (string).
"""

import threading
import Queue
import time
import re
import random
import json
from monotonic import monotonic
from urllib import urlencode
from urllib2 import Request, urlopen, URLError, HTTPError

WIO_TOKEN = "1e9f7584c27264ab5bf55f3975b67870"

class Worker(threading.Thread):
    def __init__(self, queue_len = 10):
        threading.Thread.__init__(self)
        self.q = Queue.Queue(queue_len)
        self.thread_stop = False

        self.last_time_broadcast = 0
        self.human_around = False
        self.humidity = 0

    def set_tts(self, tts):
        self.tts = tts

    def set_player(self, ply):
        self.player = ply

    def push_cmd(self, cmd):
        self.q.put(cmd)

    def wait_done(self):
        self.q.join()

    def play_text(self, text):
        try:
            self.player.play_buffer(self.tts.speak(text))
        except Exception as e:
            print e

    def loop(self):
        """
        do stuff in the thread loop
        """
        now = monotonic()
        if now - self.last_time_broadcast > 60 and self.human_around:
            self.last_time_broadcast = now

            if self.humidity < 20.0:
                print 'the plants need water.'
                self.play_text("Hi, my soil humidity is now less than 20%, I think it's time for you to water the plants.")

        # read from wio
        self.humidity = 19.0  # this is faked for better expression of the demo
        url = "https://cn.wio.seeed.io/v1/node/GroveMoistureA0/moisture?access_token=%s" % (WIO_TOKEN,)
        request = Request(url)
        try:
            response = urlopen(request)
            data = response.read()
            result = json.loads(data)
            if result['moisture']:
                #self.humidity = result['moisture']
                print 'moisture raw:', result['moisture']
        except Exception as e:
            print e
            pass

        # read from wio
        url = "https://cn.wio.seeed.io/v1/node/GrovePIRMotionD0/approach?access_token=%s" % (WIO_TOKEN,)
        request = Request(url)
        try:
            response = urlopen(request)
            data = response.read()
            result = json.loads(data)
            if result['approach']:
                self.human_around = True
                print 'human around'
            else:
                self.human_around = False
        except Exception as e:
            print e
            pass

        # chance = random.randint(0, 100)
        # if chance < 10:
        #     print 'the plants need water.'
        #     self.play_text("Hi, my soil humidity is now less than %d%%, I think it's time for you to water the plants." % (chance,))

    def run(self):
        while not self.thread_stop:
            self.loop()
            cmd = ''
            try:
                cmd = self.q.get(timeout=1)
            except:
                continue
            print("worker thread get cmd: %s" %(cmd, ))
            self._parse_cmd(cmd)
            self.q.task_done()
            len = self.q.qsize()
            if len > 0:
                print("still got %d commands to execute." % (len,))

    def _parse_cmd(self, cmd):
        if re.search(r'how.*(plant|plants|plans).*(going|doing)?', cmd) or re.search(r'check.*(plant|plants|plans).*', cmd):
            resp = 'they are good, the soil humidity is now %.1f percent' % self.humidity
            self.play_text(resp)
        elif re.search(r'thank you', cmd):
            self.play_text("you're welcome!")
        elif re.search(r'how(\'re)?.*(are)?.*you', cmd):
            self.play_text("good, thank you.")
        elif re.search(r'bye bye', cmd):
            self.play_text("bye!")
        else:
            print 'unknown command, ignore.'
            self.play_text("I don't know your command.")

    def stop(self):
        self.thread_stop = True
        self.q.join()
