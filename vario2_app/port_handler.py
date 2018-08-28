from serial.tools.list_ports import comports
from kivy.logger import Logger
from enum import Enum
from time import sleep, time

from pc_parser import pc_parser
from glue import MyThread
from struct import unpack, pack


class mode(Enum):
    IDLE = 0
    TRYING = 1
    CONNECTED = 2
    
VID = 0x0403
PID = 0x6015

CMD_HELLO       = 0x00
CMD_PING        = 0x01
CMD_GET_VERSION = 0x02
CMD_GET_VALUE   = 0x03
CMD_SET_VALUE   = 0x04
CMD_RESET       = 0x05
CMD_DEMO        = 0x06

RES_DROP2_HELLO = [0x00, 98, 101, 97, 110, 50, 0]

VALUE_DICT = {
    "volume":           [0x00, "uint8"],
    "auto_power_off":   [0x01, "uint16"],
    "active_profile":   [0x02, "uint8"],
    "silent_start":     [0x03, "bool"],
    "fluid_audio":      [0x04, "bool"],

    "lift_1":           [0x05, "int16"],
    "lift_2":           [0x06, "int16"],
    "lift_3":           [0x07, "int16"],
    "lift_4":           [0x08, "int16"],
    "lift_5":           [0x09, "int16"],
    
    "sink_1":           [0x0A, "int16"],
    "sink_2":           [0x0B, "int16"],
    "sink_3":           [0x0C, "int16"],
    "sink_4":           [0x0D, "int16"],
    "sink_5":           [0x0E, "int16"],

    
    "index_lift":       [0x0F, "uint8"],
    "index_sink":       [0x10, "uint8"],

    "freq_0":           [0x84, "uint16"],
    "freq_1":           [0x85, "uint16"],
    "freq_2":           [0x86, "uint16"],
    "freq_3":           [0x87, "uint16"],
    "freq_4":           [0x88, "uint16"],
    "freq_5":           [0x89, "uint16"],
    "freq_6":           [0x8A, "uint16"],
    "freq_7":           [0x8B, "uint16"],
    "freq_8":           [0x8C, "uint16"],
    "freq_9":           [0x8D, "uint16"],
    "freq_10":          [0x8E, "uint16"],
    "freq_11":          [0x8F, "uint16"],
    "freq_12":          [0x90, "uint16"],
    "freq_13":          [0x91, "uint16"],
    "freq_14":          [0x92, "uint16"],
    "freq_15":          [0x93, "uint16"],
    "freq_16":          [0x94, "uint16"],
    "freq_17":          [0x95, "uint16"],
    "freq_18":          [0x96, "uint16"],
    "freq_19":          [0x97, "uint16"],
    "freq_20":          [0x98, "uint16"],
    "freq_21":          [0x99, "uint16"],
    "freq_22":          [0x9A, "uint16"],
    "freq_23":          [0x9B, "uint16"],
    "freq_24":          [0x9C, "uint16"],
    "freq_25":          [0x9D, "uint16"],
    "freq_26":          [0x9E, "uint16"],
    "freq_27":          [0x9F, "uint16"],
    "freq_28":          [0xA0, "uint16"],
    "freq_29":          [0xA1, "uint16"],
    "freq_30":          [0xA2, "uint16"],
    "freq_31":          [0xA3, "uint16"],
    "freq_32":          [0xA4, "uint16"],
    "freq_33":          [0xA5, "uint16"],
    "freq_34":          [0xA6, "uint16"],
    "freq_35":          [0xA7, "uint16"],
    "freq_36":          [0xA8, "uint16"],
    "freq_37":          [0xA9, "uint16"],
    "freq_38":          [0xAA, "uint16"],
    "freq_39":          [0xAB, "uint16"],
    "freq_40":          [0xAC, "uint16"],
    
    "pause_0":          [0xAD, "uint16"],
    "pause_1":          [0xAE, "uint16"],
    "pause_2":          [0xAF, "uint16"],
    "pause_3":          [0xB0, "uint16"],
    "pause_4":          [0xB1, "uint16"],
    "pause_5":          [0xB2, "uint16"],
    "pause_6":          [0xB3, "uint16"],
    "pause_7":          [0xB4, "uint16"],
    "pause_8":          [0xB5, "uint16"],
    "pause_9":          [0xB6, "uint16"],
    "pause_10":          [0xB7, "uint16"],
    "pause_11":          [0xB8, "uint16"],
    "pause_12":          [0xB9, "uint16"],
    "pause_13":          [0xBA, "uint16"],
    "pause_14":          [0xBB, "uint16"],
    "pause_15":          [0xBC, "uint16"],
    "pause_16":          [0xBD, "uint16"],
    "pause_17":          [0xBE, "uint16"],
    "pause_18":          [0xBF, "uint16"],
    "pause_19":          [0xC0, "uint16"],
    "pause_20":          [0xC1, "uint16"],
    "pause_21":          [0xC2, "uint16"],
    "pause_22":          [0xC3, "uint16"],
    "pause_23":          [0xC4, "uint16"],
    "pause_24":          [0xC5, "uint16"],
    "pause_25":          [0xC6, "uint16"],
    "pause_26":          [0xC7, "uint16"],
    "pause_27":          [0xC8, "uint16"],
    "pause_28":          [0xC9, "uint16"],
    "pause_29":          [0xCA, "uint16"],
    "pause_30":          [0xCB, "uint16"],
    "pause_31":          [0xCC, "uint16"],
    "pause_32":          [0xCD, "uint16"],
    "pause_33":          [0xCE, "uint16"],
    "pause_34":          [0xCF, "uint16"],
    "pause_35":          [0xD0, "uint16"],
    "pause_36":          [0xD1, "uint16"],
    "pause_37":          [0xD2, "uint16"],
    "pause_38":          [0xD3, "uint16"],
    "pause_39":          [0xD4, "uint16"],
    "pause_40":          [0xD5, "uint16"],

    "length_0":          [0xD6, "uint16"],
    "length_1":          [0xD7, "uint16"],
    "length_2":          [0xD8, "uint16"],
    "length_3":          [0xD9, "uint16"],
    "length_4":          [0xDA, "uint16"],
    "length_5":          [0xDB, "uint16"],
    "length_6":          [0xDC, "uint16"],
    "length_7":          [0xDD, "uint16"],
    "length_8":          [0xDE, "uint16"],
    "length_9":          [0xDF, "uint16"],
    "length_10":          [0xE0, "uint16"],
    "length_11":          [0xE1, "uint16"],
    "length_12":          [0xE2, "uint16"],
    "length_13":          [0xE3, "uint16"],
    "length_14":          [0xE4, "uint16"],
    "length_15":          [0xE5, "uint16"],
    "length_16":          [0xE6, "uint16"],
    "length_17":          [0xE7, "uint16"],
    "length_18":          [0xE8, "uint16"],
    "length_19":          [0xE9, "uint16"],
    "length_20":          [0xEA, "uint16"],
    "length_21":          [0xEB, "uint16"],
    "length_22":          [0xEC, "uint16"],
    "length_23":          [0xED, "uint16"],
    "length_24":          [0xEE, "uint16"],
    "length_25":          [0xEF, "uint16"],
    "length_26":          [0xF0, "uint16"],
    "length_27":          [0xF1, "uint16"],
    "length_28":          [0xF2, "uint16"],
    "length_29":          [0xF3, "uint16"],
    "length_30":          [0xF4, "uint16"],
    "length_31":          [0xF5, "uint16"],
    "length_32":          [0xF6, "uint16"],
    "length_33":          [0xF7, "uint16"],
    "length_34":          [0xF8, "uint16"],
    "length_35":          [0xF9, "uint16"],
    "length_36":          [0xFA, "uint16"],
    "length_37":          [0xFB, "uint16"],
    "length_38":          [0xFC, "uint16"],
    "length_39":          [0xFD, "uint16"],
    "length_40":          [0xFE, "uint16"],
}

PING_PERIOD = 1
PING_WINDOW = 0.1

IGNORE_ANSWER = 0.7

class port_handler(MyThread):
    
    def __init__(self, cb):
        MyThread.__init__(self)

        self.value_dict = VALUE_DICT
        self.id_dict = {}
        for name in self.value_dict:
            value_id, __ = self.value_dict[name]
            self.id_dict[value_id] = name

        self.cb = cb
        self.handle = pc_parser()
        self.reset()
    
    def start(self):    
        MyThread.start(self)
    
    def reset(self):
        self.handle.reset()
        self.cb("disconnected")

        self.mode = mode.IDLE
        self.type = 0
        
        self.tx_time = 0
        self.tx_data = None
        
        self.last_ping = 0
        self.ping_send = False

    def get_version(self):
        self.write("write", [CMD_GET_VERSION])

    def get_value(self, name):
        if name == "END":
            self.cb("all_done")
            return
        
        value_id = self.value_dict[name][0]
        self.write("write", [CMD_GET_VALUE, value_id])

    def resetEEPROM(self):
        self.write("write", [CMD_RESET])

    def play_demo(self, value):
        if value is not False:
            string = pack("<h", int(value))
            data = list(string)
        else:
            data = [0xFF, 0x7F]
        
        self.write("write", [CMD_DEMO] + data)        

    def set_value(self, name, value):
        value_id = self.value_dict[name][0]
        value_type = self.value_dict[name][1]

        if value_type == "bool":
            value = int(bool(value))
            data = [value]
        
        if value_type == "uint8":
            value = int(value)
            data = [value]
            
        if value_type == "uint16":
            value = int(value)
            data = [value & 0xFF, (value & 0xFF00) >> 8]

        if value_type == "int16":
            string = pack("<h", int(value))
            data = list(string)
        
        self.write("write", [CMD_SET_VALUE, value_id] + data)

    def poke(self, port):
        try:
            self.handle.reset()
            self.handle.open(port)
            sleep(0.2)
            self.handle.encode([CMD_HELLO])
            sleep(0.2)
            data = self.handle.loop()
            self.handle.close()
            for m in data:
                if m == RES_DROP2_HELLO:
                    self.type = 2
                    return True

            return False
            
        except Exception as e:
            Logger.exception(e)
            return False    
        
    def open(self, port):
        self.handle.open(port)

    def ping(self):
        if self.ping_send and time() - self.last_ping > PING_WINDOW:
            self.reset()
            return
         
        if time() - self.last_ping > PING_PERIOD:
            if self.handle.idle() and self.idle():
                self.write("ping")
            

    
    def parse_data(self, data):
        cmd = data[0]
        if cmd == CMD_PING:
            Logger.debug("PONG %0.2f" % (time() - self.last_ping))
            self.ping_send = False
            return

        if cmd == CMD_GET_VALUE:
            value_id = data[1]
            value_name = self.id_dict[value_id]
            __, value_type = self.value_dict[value_name]
            
            if value_type == "bool":
                self.cb("get_value", [value_name, bool(data[2])])

            if value_type == "uint8":
                self.cb("get_value", [value_name, data[2]])
                
            if value_type == "uint16":
                self.cb("get_value", [value_name, data[2] | (data[3] << 8)])

            if value_type == "int16":
                string = bytes(data[2:4])
                value, = unpack("<h", string)
                self.cb("get_value", [value_name, value])
        
        if cmd == CMD_SET_VALUE:
            self.cb("set_value")

    def loop(self): 
#        Logger.debug(self.mode)
        self.last_idle = 0
        
        tx_idle = True
        for cmd, data in self.internal_read():
            tx_idle = False
            
            if cmd == "quit":
                self.handle.close()
                self.running = False
                return
            
            if cmd == "write":
                if self.mode == mode.CONNECTED:
                    self.tx_time = time()
                    self.tx_data = data
                    self.handle.encode(self.tx_data)
                
            if cmd == "ping":
                if self.mode == mode.CONNECTED:
                    Logger.debug("PING")
                    self.last_ping = time()
                    self.ping_send = True
                    self.handle.encode([CMD_PING])                
                
            break
      
        if self.mode == mode.IDLE:
            self.ports = comports()
            self.port_index = 0
            if len(self.ports) > 0:
                self.mode = mode.TRYING
            else:
                sleep(1)
            
        if self.mode == mode.TRYING:
            port = self.ports[self.port_index]
            if port.vid == VID and port.pid == PID:
                if self.poke(port.device):
                    self.mode = mode.CONNECTED
                    self.open(port.device)
                    self.cb("connected", port.device)
                else:
                    self.port_index += 1
            else:
                self.port_index += 1
            
            if self.port_index >= len(self.ports):
                self.mode = mode.IDLE
                sleep(1)    
            
        if self.mode == mode.CONNECTED:
            msg = self.handle.loop()
            self.ping()
            
            if tx_idle and len(msg) == 0:
                sleep(0.01)
            
            for data in msg:
                self.tx_time = 0
                self.parse_data(data)
        
        if self.idle() and self.mode == mode.CONNECTED:
            if time() - self.last_idle > 0.5:
                self.cb("idle")
                self.last_idle = time()
        
    def idle(self):
        if not self.q_in.empty():
            return False 
        if self.ping_send:
            return False
        return time() - self.tx_time > IGNORE_ANSWER
        
    def run(self):
        self.running = True
        while self.running:
            try:
                self.loop()
            except OSError as e:
                Logger.exception(e)
                self.reset()
                sleep(2)



