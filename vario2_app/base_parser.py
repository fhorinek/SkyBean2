from kivy.logger import Logger
from enum import Enum
from time import time


def calc_crc(csum, key, data):
    for __ in range(0, 8):
        if ((data & 0x01)^(csum & 0x01)):
            csum = (csum >> 1) % 0x100 
            csum = (csum ^ key) % 0x100
        else:
            csum = (csum >> 1) % 0x100
        data = (data >> 1) % 0x100
        
    #Logger.debug("crc -> %02X" % csum)
    return csum

class step(Enum):
    IDLE = 0
    LEN = 1
    DATA = 2
    CRC = 3
    
START_BYTE = 0xAA
MAX_LEN = 16
MAX_TIME = 0.200

CRC_KEY = 0xD5

class base_parser(object):
    def __init__(self):
        self.reset()
        
    def reset(self):
        self.step = step.IDLE
        self.last_byte = 0
     
    def open(self):
        raise NameError('Base parser can\'t open port')
    
    def read(self):
        return []
     
    def write(self, data):
        pass

    def encode(self, data):
        to_send = []
        to_send.append(START_BYTE)
        to_send.append(len(data))
        
        crc = calc_crc(0x00, CRC_KEY, len(data))
        for c in data:
            crc = calc_crc(crc, CRC_KEY, c)
            to_send.append(c)
            
        to_send.append(crc)
        
#         print(to_send)
        self.write(to_send)
        
        
    def decode(self, c):
        if time() - self.last_byte > MAX_TIME:
            self.step = step.IDLE
        self.last_byte = time()
        
        if self.step == step.IDLE:
            if c == START_BYTE:
                self.step = step.LEN
            return False

        if self.step == step.LEN:
            if c > MAX_LEN or c == 0:
                self.step = step.IDLE
                return False
            
            self.step = step.DATA
            self.len = c
            self.data = []
            self.crc = calc_crc(0x00, CRC_KEY, self.len)
            return False
        
        if self.step == step.DATA:
            self.crc = calc_crc(self.crc, CRC_KEY, c)
            self.data.append(c)
            
            if len(self.data) == self.len:
                self.step = step.CRC
            return False
                
        if self.step == step.CRC:
            self.step = step.IDLE
            if c == self.crc:
                return self.data
            else:
                Logger.error("crc fail %02X %02X" % (self.crc, c))
        return False
     
    def idle(self):
        return self.step == step.IDLE
            
    def loop(self):
        msg = []
        for c in self.read():
            m = self.decode(c)
            if m:
                msg.append(m)
        return msg
            
