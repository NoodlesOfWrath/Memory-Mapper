from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.graphics import Ellipse
from kivy.uix.boxlayout import BoxLayout


class ExpandableBarLayout(BoxLayout):
    
    def __init__(self, widgets=[], **kwargs):
        super(ExpandableBarLayout, self).__init__(**kwargs)
        self.widgets = widgets
        self.redraw_widgets()

    def on_touch_move(self, touch):
        if self.collide_point(*touch.pos):
            x, y = self.center
            distance = ((touch.x - x) ** 2 + (touch.y - y) ** 2) ** 0.5
            if distance <= self.width / 2:
                self.on_hover_enter()
            else:
                self.on_hover_exit()

    def redraw_widgets(self):
        with self.canvas:
            self.expandable_bar = BoxLayout(orientation='horizontal')
            if len(self.widgets) > 0:
                self.expandable_bar.add_widget(self.widgets[0])

    # def add_widget(self, widget, *args, **kwargs):
    #    self.widgets.append(widget)

    def on_hover_enter(self):
        for widget in self.widgets[1:]:
            self.expandable_bar.add_widget(widget)
        print(f'children count:{self.children}')

    def on_hover_exit(self):
        if self.expandable_bar.children > 1:
            for widget in self.expandable_bar.children[1:]:
                self.expandable_bar.remove_widget(widget)


class CircleWidget(Widget):

    def __init__(self, text='', label_color=(0, 0, 0, 1), circle_color=(0, 0, 0, 0), circle_size=1, circle_image=None,
                 **kwargs):
        super(CircleWidget, self).__init__(**kwargs)

        # Define circle_size as an instance variable
        self.circle_size = circle_size

        with self.canvas:
            if circle_image is None:
                # Set the position and size of the circle here
                self.circle = Ellipse(pos=self.pos, size=(50 * circle_size, 50 * circle_size), color=circle_color)
            else:
                self.circle = Ellipse(pos=self.pos, size=(50 * circle_size, 50 * circle_size), color=circle_color,
                                      texture=circle_image)

        self.label = Label(text=text, halign='center', valign='middle', font_size=40, color=label_color)
        self.add_widget(self.label)

    def on_size(self, *args):
        circle_size = min(self.width, self.height)
        circle_size = float(circle_size) * float(self.circle_size)
        self.circle.pos = (self.center_x - circle_size / 2, self.center_y - circle_size / 2)
        self.circle.size = (circle_size, circle_size)

        self.label.size = self.size
        self.label.text_size = self.size
        self.label.pos = self.pos

    def update_circle_size(self, new_size):
        self.circle_size = new_size
        self.on_size()
