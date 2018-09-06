from serial import Serial
from base_parser import base_parser
from kivy.logger import Logger
from time import sleep, time

MSG_PERIOD = 0.1

class pc_parser(base_parser):
    def __init__(self):
        self.h = False
        base_parser.__init__(self)
        self.last_write = 0
        
    def open(self, port):
        print("opening")
        self.h = Serial(port, 115200)
        
    def close(self):
        if self.h:
            print("closing")
            self.h.close()
        
    def read(self):
        data = []
        while self.h.inWaiting():
            data.append(ord(self.h.read()))

        if len(data):
            msg = ""
            for c in data:
                msg += "%c" % chr(c)
#            print("Read: " + msg)
#                 
#             msg = ""
#             for c in data:
#                 msg += "%02X " % c
#             Logger.debug("Read: " + msg)
    

        return data
    
    def write(self, data):
#         if time() - self.last_write < MSG_PERIOD:
#             sleep(MSG_PERIOD)
#         msg = ""
#         for c in data:
#             msg += "%c" % chr(c)
#         Logger.debug("Write: " + msg)
            
        msg = ""
        for c in data:
            msg += "%02X " % c
        #Logger.debug("Write: " + msg)
            
        self.h.write(bytearray(data))
        
    def reset(self):
        base_parser.reset(self)
        self.close()

