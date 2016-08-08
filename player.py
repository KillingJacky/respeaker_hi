"""
Play a wav file or a raw audio buffer
The default parameter of this player is 1 channel, 16kHz, 16bit samples.
"""
import pyaudio
import wave
import io
import time
import threading
import Queue

CHUNK_SIZE = 4096

class Player():
    def __init__(self, pa, ):
        self.pa = pa
        self.stream = self.pa.open(format=pyaudio.paInt16,
                                   channels=1,
                                   rate=16000,
                                   output=True,
                                   start=False,
                                #    output_device_index=1,
                                   frames_per_buffer=CHUNK_SIZE,
                                   stream_callback=self.callback)
        self.buffer = b''
        self.lock_buffer = threading.RLock()
        self.lock_thread = threading.RLock()
        self.event = threading.Event()
        self.event.set()

    @property
    def idle_state(self):
        return self.event.is_set()

    def play(self, wav_file, block=True):
        self.wav = wave.open(wav_file, 'rb')
        n = self.wav.getnframes()
        with self.lock_buffer:
            self.buffer += self.wav.readframes(n)
            self.buffer += '\x00' * CHUNK_SIZE  # this is a bad fix for sound cutting off in the end.
        self.wav.close()

        try:
            if not self.stream.is_active():
                self.stream.stop_stream()
                self.event.clear()
                self.stream.start_stream()
                if block:
                    self.event.wait()
            else:
                return
        except:
            pass
            self.event.wait()

    def play_buffer(self, buffer, block=True):
        with self.lock_buffer:
            self.buffer += buffer

        try:
            if not self.stream.is_active():
                self.stream.stop_stream()
                self.event.clear()
                self.stream.start_stream()
                if block:
                    self.event.wait()
            else:
                return
        except:
            pass


    def wait_done(self):
        self.event.wait()

    def callback(self, in_data, frame_count, time_info, status):
        length = frame_count * 2 * 1
        with self.lock_buffer:
            data = self.buffer[:length]
            drain_len = len(data)
            self.buffer = self.buffer[drain_len:]
            if len(self.buffer) == 0:
                self.event.set()
        return data, pyaudio.paContinue

    def close(self):
        self.event.set()
        self.stream.stop_stream()
        self.stream.close()
