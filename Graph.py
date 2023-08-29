from kivy.graphics import PushMatrix, PopMatrix, Rotate
from kivy.core.window import Window
from kivy.uix.widget import Widget
from kivy.uix.label import Label


class RotatedLabelWidget(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.label = Label(text='Left Label', width=50, height=Window.height,
                           text_size=(100, None))
        self.label.bind(size=self.update_label_size)

        with self.canvas.before:
            self.push_matrix = PushMatrix()
            self.rotate = Rotate(angle=90, origin=self.label.center)

        with self.canvas.after:
            self.pop_matrix = PopMatrix()

        self.add_widget(self.label)

    def update_label_size(self, instance, size):
        self.rotate.origin = self.label.center

    def on_size(self, *args):
        self.label.height = Window.height
