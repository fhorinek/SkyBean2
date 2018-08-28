
import threading
import os

from multiprocessing import Queue

def resource_path(relative):
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative)
    return os.path.join(relative)

class MyThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.q_in = Queue()
        self.q_out = Queue()
            
    def read(self):
        msgs = []
        try:
            while True:
                msgs.append(self.q_out.get(False))
        finally:
            return msgs
            
        return msgs

    def write(self, cmd, data = None):
        self.q_in.put([cmd, data])
    
    def internal_read(self):
        msgs = []
        try:
            while True:
                msgs.append(self.q_in.get(False))
        finally:
            return msgs

    def internal_write(self, cmd, data = None):
        self.q_out.put([cmd, data])