"""
This is the worker thread which handles the input (string).
"""

import threading
import Queue
import time
import re
import random

class Worker(threading.Thread):
    def __init__(self, queue_len = 10):
        threading.Thread.__init__(self)
        self.q = Queue.Queue(queue_len)
        self.thread_stop = False

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

    def hook(self):
        """
        do stuff in the thread loop
        """
        chance = random.randint(0, 100)
        if chance < 10:
            print 'the plants need water.'
            self.play_text("Hi, my soil humidity is now less than %d%%, I think it's time for you to water the plants." % (chance,))

    def run(self):
        while not self.thread_stop:
            self.hook()
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
            print 'they are good'
            self.play_text('they are good.')
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
