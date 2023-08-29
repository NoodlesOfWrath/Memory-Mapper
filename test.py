from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.core.window import Window
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.graphics import PushMatrix, PopMatrix, Rotate

from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.graphics import PushMatrix, PopMatrix, Rotate


class RotatedLabelWidget(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.label = Label(text='Left Label', width=50, height=Window.height,
                           text_size=(100, None))
        self.label.bind(size=self.update_label_size)

        with self.canvas.before:
            self.push_matrix = PushMatrix()
            self.rotate = Rotate(angle=-90, origin=self.label.center)

        with self.canvas.after:
            self.pop_matrix = PopMatrix()

        self.add_widget(self.label)

    def update_label_size(self, instance, size):
        self.rotate.origin = self.label.center

    def on_size(self, *args):
        self.label.height = Window.height
        # self.label.texture_size *= int(Window.height)


class GraphApp(App):
    def build(self):
        # Create a RelativeLayout to hold the labels and graph content
        layout = RelativeLayout()
        # Top label
        top_label = Label(text='Top Label', size_hint=(None, None), height=50,
                          pos_hint={'top': 1, 'center_x': 0.5})
        layout.add_widget(top_label)
        graph_layout = AnchorLayout(anchor_x='left', anchor_y='center')
        left_label = RotatedLabelWidget()
        graph_layout.add_widget(left_label)
        layout.add_widget(graph_layout)

        return layout


if __name__ == '__main__':
    GraphApp().run()
