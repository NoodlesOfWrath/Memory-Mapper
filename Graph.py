from kivy.graphics import PushMatrix, PopMatrix, Rotate
from kivy.uix.textinput import TextInput
from kivy.core.window import Window
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button


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


class EditablePopup(Popup):
    def __init__(self, apply_callback, initial_text, title, **kwargs):
        super().__init__(**kwargs)

        self.size_hint = 0.6, 0.6
        self.title = title
        self.apply_callback = apply_callback

        layout = BoxLayout(orientation='vertical', spacing=10)

        self.text_input = TextInput(hint_text='Enter text here', multiline=True, text=initial_text)
        layout.add_widget(self.text_input)

        button_layout = BoxLayout(orientation='horizontal', spacing=10)

        apply_button = Button(text='Apply')
        apply_button.bind(on_release=self.apply_changes)
        button_layout.add_widget(apply_button)

        cancel_button = Button(text='Cancel')
        cancel_button.bind(on_release=self.dismiss)
        button_layout.add_widget(cancel_button)

        layout.add_widget(button_layout)

        self.content = layout

    def apply_changes(self, instance):
        new_text = self.text_input.text
        self.apply_callback(new_text)
        self.dismiss()