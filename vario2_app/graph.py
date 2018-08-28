from kivy.uix.widget import Widget
from kivy.graphics import Color, Line, Rectangle, Ellipse, SmoothLine
from kivy.properties import NumericProperty, ListProperty
from kivy.graphics.instructions import InstructionGroup
from kivy.uix.bubble import Bubble
from kivy.uix.textinput import TextInput
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout

import math
from math import sqrt
from kivy.core.window import Window
from kivy.clock import Clock
from random import random



from kivy.factory import Factory
from kivy.lang import Builder

Builder.load_string("""
<LabelB>:
  bcolor: 1, 1, 1, 1
  size: 60, 20
  text_size: self.size
  halign: "center"
  valign: "middle"


            
""")
      
#     PushMatrix
#     Rotate:
#         angle: self.angle
#         axis: 0,0,1
#         origin: self.center
#   canvas.after:
#     PopMatrix      
#       

class LabelB(Label):
    bcolor = ListProperty([1,1,1,1])
    angle = NumericProperty(0)

Factory.register('KivyB', module='LabelB')

class Axis(object):
    min = 0 
    max = 100
    step = 10
    auto_min = True
    auto_max = True
    format = "%1.0f"
    left = True
    
    def __init__(self, parent, **kwargs):
        self.lines = []
        self.parent = parent
        self.parent.add_axis(self)
        
        self.ruler_lines = []
        self.ruler_labels = []
        self.ruler_draw_group = InstructionGroup()
        self.parent.canvas.add(self.ruler_draw_group)
        
        if "min" in kwargs:
            self.min = kwargs["min"]
        if "max" in kwargs:
            self.max = kwargs["max"]
        if "step" in kwargs:
            self.step = kwargs["step"]
        if "auto_min" in kwargs:
            self.auto_min = kwargs["auto_min"]
        if "auto_max" in kwargs:
            self.auto_max = kwargs["auto_max"]
        if "left" in kwargs:
            self.left = kwargs["left"]
        if "format" in kwargs:
            self.format = kwargs["format"]            
        
        self.delta = self.max - self.min
    
    def add_line(self, line):
        self.lines.append(line)
    
    def redraw_ruler(self):
        x1, y1, x2, y2 = self.parent.rect
        h = y2 - y1        
        
        if len(self.ruler_lines) != int(self.delta / self.step) - 1:
            self.ruler_draw_group.clear()
            self.ruler_lines = []
            for label in self.ruler_labels:
                self.parent.remove_widget(label)
            
            self.ruler_labels = []
            for __ in range(int(self.delta / self.step) - 1):
                if self.left:
                    line = Line(dash_offset = 5)
                else:
                    line = Line()
                    
                self.ruler_lines.append(line)
                self.ruler_draw_group.add(line)
                label = LabelB()
                if self.left:
                    label.halign = "right"
                else:
                    label.halign = "left"
                    
                self.parent.add_widget(label)
                self.ruler_labels.append(label)
                
                
        for i in range(int(self.delta / self.step) - 1):
            y = y1 + (h / ((self.delta / self.step) - 1)) * (i + 1)
            if self.left:
                self.ruler_lines[i].points = [x1, y, x2, y]
            else:
                self.ruler_lines[i].points = [x2 - 5 , y, x2 + 5, y]
            
            val = self.min + (self.delta / (int(self.delta / self.step) - 1)) * (i + 1)
            
            label = self.ruler_labels[i]
            label.center_y = y
            label.text = self.format % val
            
            if self.left:
                label.x = x1 - label.width - 5
            else:
                label.x = x2 + 5
    
    def redraw(self):
        self.redraw_ruler()
        
        for line in self.lines:
            line.redraw() 
   
    def update(self):
        """Update min/max for axis
        
        Note:r = ListProperty([1,1,1,1])
            It will redraw the lines and axis if update was performed
            otherwise you will need handle the update yourself 
        
        Returns:
            True - if there was change in min/max, False otherwise
        """
        
        if not self.auto_min and not self.auto_max:
            return
        
        local_min = +math.inf
        local_max = -math.inf
        
        for line in self.lines:
            if len(line.data):
                local_min = min(local_min, min(line.data))
                local_max = max(local_max, max(line.data))
        
        #adjust to step    
        m = math.ceil(local_min / self.step) - 1
        local_min = self.step * m
                
        m = math.floor(local_max / self.step) + 1
        local_max = self.step * m
        
        if self.min != local_min or self.max != local_max:
            if self.auto_min:
                self.min = local_min
            if self.auto_max:
                self.max = local_max
                
            self.delta = self.max - self.min
            
            self.redraw()
            return True
        
        return False

    def find_point(self, x, y):
        min_distance = math.inf
        min_point = None
        min_line = None
        
        for line in self.lines:
            point, distance = line.find_point(x, y)
            if distance < min_distance:
                min_point = point
                min_line = line
                min_distance = distance     
                
        return min_point, min_line, min_distance   
        
class LineData(object):
    point_size = 6
    on_change = None
    min = None
    max = None
    
    def __init__(self, data, axis, color = (1, 0, 0), name = "Line", units = "Hz", **kwargs):
        self.axis = axis
        self.axis.add_line(self)
        self.color = color
        self.name = name
        self.units = units
        
        if "min" in kwargs:
            self.min = kwargs["min"]
        if "max" in kwargs:
            self.max = kwargs["max"]        
        
        with self.axis.parent.canvas:
            Color(*self.color)
            self.line = Line(width = 1.2)
            
        self.circles = []
        self.circles_draw_group = InstructionGroup()
        
        self.axis.parent.canvas.add(self.circles_draw_group)
            
        self.data_update(data)
        
    def data_update(self, data = None):
        if data:
            self.data = data
            
        if not self.axis.update():
            self.redraw()
        
    def redraw(self):
        x1, y1, x2, y2 = self.axis.parent.rect
        w, h = x2 - x1, y2 - y1
        
        #add offset
        x1 += (w / len(self.data)) / 2
        
        x = 0
        points = []
        
        if len(self.circles) != len(self.data):
            self.circles_draw_group.clear()
            self.circles = []
            for __ in range(len(self.data)):
                circle = Ellipse(size = (self.point_size, self.point_size))
                self.circles.append(circle)
                self.circles_draw_group.add(circle)
        
        for y in self.data:
            point_y = (((y - self.axis.min) / self.axis.delta) * h) + y1 
            point_x = ((x / len(self.data)) * w) + x1 
            
            points.append([point_x, point_y])
            self.circles[x].pos = point_x - self.point_size / 2, point_y - self.point_size / 2
            x += 1
            
        self.line.points = points
            
    def find_point(self, x, y):
        def distance(x1, y1, x2, y2):
            return sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
        
        tx, ty = x - self.point_size / 2, y - self.point_size / 2

        min_point = None
        min_distance = math.inf     
          
        for i in range(len(self.circles)):
            dist = distance(tx, ty, *self.circles[i].pos)
            if dist < min_distance:
                min_distance = dist
                min_point = i
                
        return min_point, min_distance    
        
    def edit_point_data(self, point, y):
        __, y1, __, y2 = self.axis.parent.rect
        h = y2 - y1
        
        rpos = max(y - y1, 0) / h

        self.set_point_value(point, rpos * self.axis.delta + self.axis.min)
        
    def get_point_xy(self, point):
        x, y = self.circles[point].pos
        
        return x + self.point_size / 2, y + self.point_size / 2
    
    def get_name_format(self):
        return self.name, self.format
        
    def get_point_value(self, point):
        return self.data[point]
    
    def set_point_value(self, point, value):
        if not self.axis.auto_max:
            if value > self.axis.max:
                value = self.axis.max
            
        if not self.axis.auto_min:
            if value < self.axis.min:
                value = self.axes.min

        if self.max is not None:
            if value > self.max:
                value = self.max

        if self.min is not None:
            if value < self.min:
                value = self.min

            
        self.data[point] = value
        if self.on_change:
            self.on_change(point, value)
        self.data_update()


class GraphCanvas(Widget):
    border_line_width = NumericProperty(1)
    padding = ListProperty([70, 40, 70, 20])
    demo_cb = None
    max_touch_distance = NumericProperty(15)
    
    def __init__(self, **kwargs):
        super(GraphCanvas, self).__init__(**kwargs)

        self.axes = []

        self.redraw()
        self.size_update()
        
        self.hold = False
        self.bubble = None

        self.bind(size = self.size_update)

    def add_axis(self, axis):
        self.axes.append(axis)

    def redraw(self):
        self.canvas.clear()
        
        #grid an axis
        with self.canvas.before:
            Color(0, 0, 0)
            self.background = Rectangle(pos = (0, 0), size = self.size)
            Color(1, 1, 1)
            self.border = Line(close = True, width = self.border_line_width)
            
        with self.canvas.after:
            Color(0.8, 0.8, 0.8)
            self.demo = Line()
            
        self.labels = []
        for i in range(21):
            val = (i - 10) 
            label = LabelB(text = "%d" % val)
            self.labels.append(label)
            self.add_widget(label)


    def size_update(self, *args):
        w, h = self.size
        x1, y1 = self.pos
        x2, y2 = x1 + w, y1 + h      
        
        #padding
        x1 += self.padding[0]
        y1 += self.padding[1]
        x2 -= self.padding[2]
        y2 -= self.padding[3]
        self.border.points = [x1, y1, x2, y1, x2, y2, x1, y2]
        self.background.size = self.size
        self.rect = (x1, y1, x2, y2)
        
        w = x2 - x1
        for i in range(21):
            label = self.labels[i]
            label.y = y1 - label.height
            label.center_x = x1 + (w / 20) * i  
        
        for axis in self.axes:
            axis.redraw()

    def find_point(self, x, y):
        min_distance = math.inf
        min_point = None
        min_line = None
        
        for axis in self.axes:
            point, line, distance = axis.find_point(x, y)
            if distance < min_distance:
                min_point = point
                min_line = line
                min_distance = distance     
                
        return min_point, min_line, min_distance   

    def on_touch_down(self, touch):
        x, y = map(int, touch.pos)
        
        if self.bubble:
            if self.bubble.collide_point(x,y):
                Clock.schedule_once(self.bubble.set_focus)
                print("collide")
                return
            
    
        point, line, distance = self.find_point(x, y)
        
        if distance < self.max_touch_distance:
            self.hold = True
            self.hold_point = point
            self.hold_line = line
            
            if self.bubble:
                self.bubble.set_point(line, point)
                x, y = self.hold_line.get_point_xy(self.hold_point)
                x, y = self.to_parent(x, y)
                
                self.bubble.set_pos(x, y)
                self.bubble.show()
        else:
            if self.bubble:
                self.bubble.hide()
      
    def on_touch_move(self, touch):
        x, y = map(int, touch.pos)
        
        if self.hold:
            self.demo.points = []
            self.hold_line.edit_point_data(self.hold_point, y)
            if self.bubble:
                x, y = self.hold_line.get_point_xy(self.hold_point)
                x, y = self.to_parent(x, y)                
                self.bubble.set_pos(x, y)
        else:
            if self.demo_cb:
                #demo line
                
                x1, y1, x2, y2 = self.rect
                w = x2 - x1
                x = max(x1, x)
                x = min(x2, x)
                
                if y > y2 or y < y1:
                    return
                
                self.demo.points = [x, y1, x, y2]
                
                val = (x - x1 - w / 2) / (w / 20)
                val = int(val * 100)            
    
                self.demo_cb(val)
        
    def on_touch_up(self, __):        
        self.hold = False
        if self.demo_cb:
            self.demo.points = []
            self.demo_cb(False)
            
        if self.bubble:
            Clock.schedule_once(self.bubble.set_focus)        

class EditBubble(Bubble):
    def __init__(self, **kwargs):
        Bubble.__init__(self, **kwargs)
        self.line = None
        self.point = None
        self.hide()
        self.background_color = 0.20, 0.71, 0.90, 0.8
        self.opacity = 0.95

        self.size_hint = [None, None]
        self.size = [160, 65]

        self.label_name = Label(text = "Frequency", size_hint_y = 0.6)
        self.label_value = Label(text = "1.5 m/s")
        self.label_units = Label(text = "Hz", size_hint_x = 0.5)

        self.input = TextInput(multiline = False, size_hint_x = 0.8)
        self.input.bind(on_text_validate = self.on_enter)
        
        Window.bind(on_key_down=self.on_key_down)        
        
        layout = BoxLayout(orientation = "vertical", padding=2)
        
        bottom = BoxLayout(size_hint_y = 0.7)
        bottom.add_widget(self.label_value)        
        bottom.add_widget(self.input)        
        bottom.add_widget(self.label_units)        
        
        layout.add_widget(self.label_name)
        layout.add_widget(bottom)
        
        self.add_widget(layout)
       
    def on_key_down(self, *args):
        if self.input.focus:
            key = args[2]
            
            delta = 0
            
            if key == 82:
                delta = +1
                
            if key == 81:
                delta = -1
                
            if delta:
                num = self.line.get_point_value(self.point)
                num += delta
                self.line.set_point_value(self.point, num)
                
                x, y = self.line.get_point_xy(self.point)
                x, y = self.to_parent(x, y)
                
                self.set_pos(x, y)
            
    
        
    def on_enter(self, __):
        if self.input.text.isdecimal():
            num = int(self.input.text)
            self.line.set_point_value(self.point, num)
            
            x, y = self.line.get_point_xy(self.point)
            x, y = self.to_parent(x, y)
                
            self.set_pos(x, y)
            
        Clock.schedule_once(self.set_focus)
        
    def set_focus(self, __):
        self.input.focus = True
        
    def set_point(self, line, point):
        self.label_name.text = line.name
        self.label_units.text = line.units
        self.label_value.text = "%0.1f m/s" % ((point / 2) - 10)
        
        self.line = line
        self.point = point
        
    def set_pos(self, x, y):
        self.input.text = str(int(self.line.get_point_value(self.point)))
        Clock.schedule_once(self.set_focus)
        
        if x - (self.width / 2) < 0:
            self.center_y = y
            self.x = x
            self.arrow_pos = 'left_mid'
            return
        
        if x + (self.width / 2) > self.parent.width:
            self.center_y = y
            self.x = x - self.width
            self.arrow_pos = 'right_mid'
            return        
        
        if y - self.height < 0:
            self.center_x = x
            self.y = y
            self.arrow_pos = 'bottom_mid'
            return               
        
        self.arrow_pos = 'top_mid'
        self.center_x = x
        self.y = y - self.height
        
    def show(self):
        pass
#         self.opacity = 0.95
        
    def hide(self):
        self.y = -self.height
        
class EditableGraph(FloatLayout):
    def __init__(self, **kwargs):
        FloatLayout.__init__(self, **kwargs)
        self.graph = GraphCanvas()
        
        bubble = EditBubble()
        self.graph.bubble = bubble
        
         
        self.add_widget(self.graph)
        self.add_widget(bubble)
        
        
if __name__ == "__main__":
    
    from kivy.app import App

    class TestApp(App):
        def build(self):
            self.eg = EditableGraph()
            self.graph = self.eg.graph
            self.axis = Axis(self.graph)
            self.axis.step = 2
            
            data = list(map(math.sin, [x * 0.1 for x in range(0, 100)]))
            self.line1 = LineData(data, self.axis, name = "Frequency", units = "Hz")
            
            data = list(map(math.cos, [x * 0.1 for x in range(0, 100)]))
            self.line2 = LineData(data, self.axis, color=(0,1,0), name = "Pause", units = "ms")

            data = list(map(math.cos, [(x + 20) * 0.1 for x in range(0, 100)]))
            self.line3 = LineData(data, self.axis, color=(0,0,1), name = "Duration", units = "ms")

            layout = BoxLayout()
            layout.add_widget(self.eg)
            return layout
        
        
    TestApp().run()
    
    
    
        