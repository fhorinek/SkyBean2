from kivy.config import Config
Config.set('kivy', 'log_level', 'debug')
Config.set('graphics', 'resizable', 0)
Config.set('input', 'mouse', 'mouse,disable_multitouch')

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.lang.builder import Builder
from kivy.logger import Logger
from kivy.garden import iconfonts 
from port_handler import port_handler
from kivy.uix.popup import Popup
from kivy.lang import Builder

from collections import deque, OrderedDict
from graph import EditableGraph, Axis, LineData
from kivy.clock import Clock


from common import resource_path


iconfonts.register('default_font', resource_path('data', 'fa-regular-400.ttf'), resource_path('data', 'fontawesome.fontd'))
iconfonts.register('default_font', resource_path('data', 'fa-brands-400.ttf'), resource_path('data', 'fontawesome.fontd'))
iconfonts.register('default_font', resource_path('data', 'fa-solid-900.ttf'), resource_path('data', 'fontawesome.fontd'))

# default_freq = [90, 91, 93, 96, 100, 105, 111, 118, 126, 135, 145, 156, 168, 181, 195, 210, 226, 243, 261, 280, 300, 325, 360, 405, 460, 525, 600, 685, 780, 875, 960, 1025, 1070, 1105, 1130, 1150, 1165, 1180, 1195, 1210, 1225]
# default_pause = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 480, 370, 288, 233, 192, 163, 142, 128, 120, 112, 105, 98, 91, 84, 78, 72, 66, 60, 54, 48, 42]
# default_length = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 320, 265, 215, 180, 150, 125, 108, 97, 90, 83, 77, 72, 67, 62, 57, 52, 47, 42, 37, 32, 27]

Builder.load_file(resource_path('data', 'vario2.kv'))

default_freq = [0] * 41
default_pause = [0] * 41
default_length = [0] * 41

class InfoPopup(Popup):
    def set_progress(self, value):
        self.ids.progress.value = value

        
class ResetPopup(Popup):
    cb = None

class AppLayout(BoxLayout):
    def __init__(self):
        BoxLayout.__init__(self)
        
        self.to_get = deque()
        self.to_set = OrderedDict()
        
        self.block_set = False

        self.popup = InfoPopup()
        self.reset_popup = ResetPopup()
        self.reset_popup.cb = self.reset_eeprom
        
        self.ph = port_handler(self.sh_cb)
        self.screens = {
            "cfg": Builder.load_file(resource_path('data', 'cfg.kv')),
            "profile": Builder.load_file(resource_path('data', 'profile.kv'))
            }    
        
        eg = self.screens["profile"].ids.eg
        self.profile_graph = eg.graph
        self.profile_graph.demo_cb = self.play_demo
        freq_axis = Axis(self.profile_graph, min = 0, max = 2000, step = 100, auto_max = True, auto_min = False, format = "%d Hz")
        time_axis = Axis(self.profile_graph, min = 0, max = 2000, step = 100, auto_max = True, auto_min = False, left = False, format = "%d ms")
       
        self.profile_frequency = LineData(default_freq, freq_axis, name = "Frequency", units = "Hz", color=(0.59, 0.73, 0.80), min = 0, max = 2000)
        self.profile_pause = LineData(default_pause, time_axis, name = "Pause", units = "ms", color=(0.97, 0.27, 0.29), min = 0, max = 2000)
        self.profile_length = LineData(default_length, time_axis, name = "Length", units = "ms", color=(0.86, 0.86, 0.86), min = 0, max = 2000)
        
        self.profile_frequency.on_change = lambda point, value: self.set_value("freq_%d" % point, value)
        self.profile_pause.on_change = lambda point, value: self.set_value("pause_%d" % point, value)
        self.profile_length.on_change = lambda point, value: self.set_value("length_%d" % point, value)

        self.screens["profile"].ids.profile_1.bind(on_press = lambda __: self.profile_set(1))
        self.screens["profile"].ids.profile_2.bind(on_press = lambda __: self.profile_set(2))
        self.screens["profile"].ids.profile_3.bind(on_press = lambda __: self.profile_set(3))
        
        self.screens["profile"].ids["lift_index_1"].bind(on_press = lambda __: self.index_lift_set(1))
        self.screens["profile"].ids["lift_index_2"].bind(on_press = lambda __: self.index_lift_set(2))
        self.screens["profile"].ids["lift_index_3"].bind(on_press = lambda __: self.index_lift_set(3))
        self.screens["profile"].ids["lift_index_4"].bind(on_press = lambda __: self.index_lift_set(4))
        self.screens["profile"].ids["lift_index_5"].bind(on_press = lambda __: self.index_lift_set(5))

        self.screens["profile"].ids["sink_index_1"].bind(on_press = lambda __: self.index_sink_set(1))
        self.screens["profile"].ids["sink_index_2"].bind(on_press = lambda __: self.index_sink_set(2))
        self.screens["profile"].ids["sink_index_3"].bind(on_press = lambda __: self.index_sink_set(3))
        self.screens["profile"].ids["sink_index_4"].bind(on_press = lambda __: self.index_sink_set(4))
        self.screens["profile"].ids["sink_index_5"].bind(on_press = lambda __: self.index_sink_set(5))
        
        #cfg callbacks
        self.screens["cfg"].ids.volume.ids.slider.bind(value = lambda __, value: self.set_value("volume", value))
        self.screens["cfg"].ids.auto_power_off.ids.slider.bind(value = lambda __, value: self.set_value("auto_power_off", value * 60))
        self.screens["cfg"].ids.auto_power_off_switch.bind(active = self.auto_power_off_switch)
        self.screens["cfg"].ids.silent_start.bind(active = lambda __, value: self.set_value("silent_start", value))
        self.screens["cfg"].ids.fluid_audio.bind(active = lambda __, value: self.set_value("fluid_audio", value))
        
        self.screens["cfg"].ids.profile_1.bind(on_press = lambda __: self.profile_set(1))
        self.screens["cfg"].ids.profile_2.bind(on_press = lambda __: self.profile_set(2))
        self.screens["cfg"].ids.profile_3.bind(on_press = lambda __: self.profile_set(3))
        
        self.screens["cfg"].ids.lift_1.bind(value = lambda __, value: self.set_value("lift_1", value * 100))
        self.screens["cfg"].ids.lift_2.bind(value = lambda __, value: self.set_value("lift_2", value * 100))
        self.screens["cfg"].ids.lift_3.bind(value = lambda __, value: self.set_value("lift_3", value * 100))
        self.screens["cfg"].ids.lift_4.bind(value = lambda __, value: self.set_value("lift_4", value * 100))
        self.screens["cfg"].ids.lift_5.bind(value = lambda __, value: self.set_value("lift_5", value * 100))
        
        self.screens["cfg"].ids.sink_1.bind(value = lambda __, value: self.set_value("sink_1", value * 100))
        self.screens["cfg"].ids.sink_2.bind(value = lambda __, value: self.set_value("sink_2", value * 100))
        self.screens["cfg"].ids.sink_3.bind(value = lambda __, value: self.set_value("sink_3", value * 100))
        self.screens["cfg"].ids.sink_4.bind(value = lambda __, value: self.set_value("sink_4", value * 100))
        self.screens["cfg"].ids.sink_5.bind(value = lambda __, value: self.set_value("sink_5", value * 100))
        
        
        
        self.screen = None
        self.set_screen("cfg")
        
        self.ph.start()

    def profile_set(self, profile):
        self.profile = profile
        self.screens["cfg"].ids.profile_1.disabled = profile == 1
        self.screens["cfg"].ids.profile_2.disabled = profile == 2
        self.screens["cfg"].ids.profile_3.disabled = profile == 3

        self.screens["profile"].ids.profile_1.disabled = profile == 1
        self.screens["profile"].ids.profile_2.disabled = profile == 2
        self.screens["profile"].ids.profile_3.disabled = profile == 3
        
        self.set_value("active_profile", profile - 1)
        
        self.block_set = True
        
        self.get_value("index_lift")
        self.get_value("index_sink")
        
        for i in range(41):
            self.get_value("freq_%d" % i)
            self.get_value("pause_%d" % i)
            self.get_value("length_%d" % i)        
             
        self.get_value("END")
            
        self.values_to_get = len(self.to_get)
        self.popup.open()
        self.popup.set_progress(0)       
        
    def index_lift_set(self, index):
        self.screens["profile"].ids["lift_index_1"].disabled = index == 1
        self.screens["profile"].ids["lift_index_2"].disabled = index == 2
        self.screens["profile"].ids["lift_index_3"].disabled = index == 3
        self.screens["profile"].ids["lift_index_4"].disabled = index == 4
        self.screens["profile"].ids["lift_index_5"].disabled = index == 5
            
        self.set_value("index_lift", index - 1)

    def index_sink_set(self, index):
        self.screens["profile"].ids["sink_index_1"].disabled = index == 1
        self.screens["profile"].ids["sink_index_2"].disabled = index == 2
        self.screens["profile"].ids["sink_index_3"].disabled = index == 3
        self.screens["profile"].ids["sink_index_4"].disabled = index == 4
        self.screens["profile"].ids["sink_index_5"].disabled = index == 5
        
        self.set_value("index_sink", index - 1)

        
    def button(self):
        value = 0xAA
        for point in range(41):
            self.set_value("freq_%d" % point, value)
            self.set_value("pause_%d" % point, value)
            self.set_value("length_%d" % point, value)
            

    def auto_power_off_switch(self, __, value):
        if value:
            self.screens["cfg"].ids.auto_power_off.ids.slider.disabled = False
            self.screens["cfg"].ids.auto_power_off.ids.slider.value = 5
        else:
            self.screens["cfg"].ids.auto_power_off.ids.slider.disabled = True
            self.screens["cfg"].ids.auto_power_off.ids.slider.value = 0

    def get_value(self, name):
        if not name in self.to_get:
            self.to_get.append(name)
        
    def play_demo(self, value):
        if value is not False:
            self.screens["profile"].ids.demo_label.text = "Playing %0.1f m/s" % (value / 100)
        else:
            self.screens["profile"].ids.demo_label.text = "Drag over graph for demo"
        self.ph.play_demo(value)
        
    def get_next_value(self):
        if len(self.to_get) > 0:
            name = self.to_get.popleft()
            self.ph.get_value(name)
            Logger.info("get_next_value %s" % name)
            return True
        return False

    def set_value(self, name, value):
        if self.block_set:
            return
        
        if name.find("lift_") != -1 or name.find("sink_") != -1:
            ident, index = name.split("_")   
            
            self.screens["profile"].ids[ident + "_index_" + index].text = "%0.1f m/s" % (value / 100.0)             
        
        Logger.info("set %s = %s" % (name, str(value)))
        self.to_set[name] = value

    def set_next_value(self):
        if len(self.to_set) > 0:
            keys = self.to_set.keys()
            name = list(keys)[0]
            data = self.to_set[name]
            del self.to_set[name]
            self.ph.set_value(name, data)
            Logger.info("set_next_value %s = %s" % (name, str(data)))
            return True
        return False

    def reset_eeprom(self):
        Logger.info("RESET EEPROM")
        self.ph.resetEEPROM()

    def update_gui(self, name, data):
        if name == "volume":
            self.screens["cfg"].ids.volume.ids.slider.value = data
            
        if name == "auto_power_off":
            if data > 0:
                self.screens["cfg"].ids.auto_power_off_switch.active = True
                self.screens["cfg"].ids.auto_power_off.ids.slider.value = data / 60
            else:
                self.screens["cfg"].ids.auto_power_off_switch.active = False
                
        if name == "active_profile":
            self.profile_set(data + 1)
                
        if name == "silent_start":
            self.screens["cfg"].ids.silent_start.active = data
            
        if name == "fluid_audio":
            self.screens["cfg"].ids.fluid_audio.active = data

        if name == "index_lift":
            self.index_lift_set(data + 1)

        if name == "index_sink":
            self.index_sink_set(data + 1)
            
        if name.find("lift_") != -1 or name.find("sink_") != -1:
            name, index = name.split("_")   
            
            self.screens["cfg"].ids[name + "_" + index].value = data / 100.0
            self.screens["profile"].ids[name + "_index_" + index].text = "%0.1f m/s" % (data / 100.0)                

        if name.find("freq_") != -1 or name.find("pause_") != -1 or name.find("length_") != -1:
            line, index = name.split("_")
            index = int(index)
            
            if line == "freq":
                self.profile_frequency.set_point_value(index, data)
            if line == "pause":
                self.profile_pause.set_point_value(index, data)
            if line == "length":
                self.profile_length.set_point_value(index, data)

    def sh_cb(self, cmd, data = None):
        #Logger.info("%s %s" % (cmd, str(data)))
        if cmd == "connected":
            Logger.info("connected")
            self.popup.title = "Getting values from SkyBean"
            self.popup.set_progress(0)
            
            self.block_set = True
            
#             self.set_status("Connected (%s)" % data)
            self.get_value("volume")
            self.get_value("auto_power_off")
            self.get_value("active_profile")
            self.get_value("silent_start")
            self.get_value("fluid_audio")
            
            self.get_value("lift_1")
            self.get_value("lift_2")
            self.get_value("lift_3")
            self.get_value("lift_4")
            self.get_value("lift_5")
            
            self.get_value("sink_1")
            self.get_value("sink_2")
            self.get_value("sink_3")
            self.get_value("sink_4")
            self.get_value("sink_5")
            
            self.get_value("index_lift")
            self.get_value("index_sink")
            
            
            for i in range(41):
                self.get_value("freq_%d" % i)
                self.get_value("pause_%d" % i)
                self.get_value("length_%d" % i)

            self.get_value("END")
            
            self.values_to_get = len(self.to_get)

        if cmd == "all_done":
            self.block_set = False
            self.popup.dismiss()

        if cmd == "get_value":
            p = 1 - (len(self.to_get) / self.values_to_get)
            self.popup.set_progress(p * 100)
                       
            value_name, value_data = data
            Logger.info("get_value %s = %s" % (value_name, str(value_data)))
            self.update_gui(value_name, value_data)
            
        if cmd == "set_value":
            Logger.info("set_value")

        if cmd == "idle":
            if self.set_next_value():
                return
            if self.get_next_value():
                return
        
        if cmd == "disconnected":
            Logger.info("disconnected")
            Clock.schedule_once(self.popup.open)
            self.popup.title = "Please connect SkyBean"
            self.popup.set_progress(0)
#             self.set_status("Please connect SkyBean")


    def stop(self):
        Logger.info("Layout stop")
        self.ph.write("quit")

    def set_screen(self, name):
        if self.screen == name:
            return
        
        if name == "profile":
            self.ids.sm.transition.direction = 'left'

        if name == "cfg":
            self.ids.sm.transition.direction = 'right'
        
        self.screen = name
        screen = self.screens[name]
        self.ids.sm.switch_to(screen)

    def set_status(self, text):
        self.ids.status.text = text


class Vario2App(App):
    
    def build(self):
        self.icon = resource_path("data", "icon.png")
        self.layout = AppLayout()
        return self.layout
            
    def on_stop(self):
        self.layout.stop()
        Logger.info("App stop")
    

if __name__ == '__main__':
    Vario2App().run()
    