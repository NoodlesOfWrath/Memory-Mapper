import copy
import random

import keyboard
from kivy.app import App
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.stencilview import StencilView
from kivy.animation import Animation
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.button import Button
from kivy.uix.image import Image as KivyImage
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.graphics import Ellipse
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.config import Config
import math
import os
import kivy
from kivy.core.image import Image as CoreImage
from PIL import Image
from io import BytesIO


def get_widget_position(widget):
    # Get the center position of the widget within the layout
    widget_pos = widget.to_parent(widget.center_x, widget.center_y)
    return widget_pos


def image_to_texture(img):
    data = BytesIO()
    img.save(data, format='png')
    data.seek(0)  # yes you actually need this
    im = CoreImage(BytesIO(data.read()), ext='png')
    return im.texture


def generate_image_previews():
    thumbnail_size = (128, 128)
    thumbnail_folder = os.path.dirname(os.path.abspath(__file__)) + "//Memory_Thumbnails"
    full_res_images_dir = os.path.dirname(os.path.abspath(__file__)) + "//Full_Res_Memories"

    for image_name in os.listdir(full_res_images_dir):
        thumbnail_file_dir = thumbnail_folder + "//" + image_name
        # Check if the image already has a cached thumbnail
        if not os.path.isfile(thumbnail_file_dir):
            image = Image.open(full_res_images_dir + "//" + image_name)
            image.thumbnail(thumbnail_size, Image.Resampling.LANCZOS)
            image.save(thumbnail_file_dir, "JPEG")


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


class SpacerWidget(Widget):
    pass


class TheLabApp(App):

    def build(self):
        self.fullscreen = False

        # Disables esc exiting the program
        Config.set('kivy', 'exit_on_escape', '0')
        # Create the main layout
        self.main_layout = RelativeLayout()
        cols = 20
        rows = 12
        spacing = 10
        self.grid_layer_one = GridLayout(cols=cols, rows=rows, spacing=spacing)
        self.main_layout.add_widget(self.grid_layer_one)
        self.grid_layer_two = GridLayout(cols=cols, rows=rows, spacing=spacing)
        self.main_layout.add_widget(self.grid_layer_two)
        self.transparent_button_layout = GridLayout(cols=cols, rows=rows, spacing=spacing)
        self.main_layout.add_widget(self.transparent_button_layout)

        self.mos_pos = ()
        self.memory_count = 240

        # Generate previews for all memories and cache them (if not done already)
        generate_image_previews()
        self.draw_circles()

        Clock.schedule_interval(self.update, 0.016666)

        return self.main_layout

    def update(self, *args):
        if not self.fullscreen:
            self.update_mouse_pos()
            self.set_circle_scale(self.grid_layer_one)
        if keyboard.is_pressed('esc') & self.fullscreen:
            self.escape_full_screen_image()

    def update_mouse_pos(self, *args):
        if Window.focus:
            # Get the mouse position using Kivy's Window module
            self.mos_pos = Window.mouse_pos
            # Adjust for pixel density
            self.mos_pos = (self.mos_pos[0] * kivy.metrics.dp(1), self.mos_pos[1] * kivy.metrics.dp(1))

    def draw_circles(self):
        self.grid_layer_one.clear_widgets()

        memory_thumbnail_folder = os.path.dirname(os.path.abspath(__file__)) + "//Memory_Thumbnails"

        for i in range(self.memory_count):
            if len(os.listdir(memory_thumbnail_folder)) > i:
                image_dir = memory_thumbnail_folder + "//" + os.listdir(memory_thumbnail_folder)[i]
                image = Image.open(image_dir)
                image = image_to_texture(image)
            else:
                print("no images found...")
                image = None
                return

            circle_widget = CircleWidget(circle_size=0.05, circle_image=image)
            with self.grid_layer_one.canvas.after:
                self.grid_layer_one.add_widget(circle_widget, i)
            image_name = os.listdir(memory_thumbnail_folder)[i]
            new_var = image_name
            circle_button = Button(background_color=(1, 0, 0, 0), on_press=lambda x, y=new_var: self.make_circle_full_screen(y))
            self.transparent_button_layout.add_widget(circle_button, i)

    def set_circle_scale(self, layout):
        biggest_circle = None
        biggest_radius = 0

        for circle in layout.children:
            widget_pos = get_widget_position(circle)

            distance_to_circle = math.dist(widget_pos, self.mos_pos)

            window_scaling_factor = min(Window.height, Window.width)*2
            if window_scaling_factor == 0:
                window_scaling_factor = 1

            # Ensure the input value is within the specified range
            distance_to_circle = max(window_scaling_factor / 50, min(distance_to_circle, window_scaling_factor / 2))
            distance_to_circle /= window_scaling_factor
            radius = 1 / distance_to_circle
            radius *= 0.04
            circle.update_circle_size(radius)
            if radius > biggest_radius:
                biggest_radius = radius
                biggest_circle = circle
        self.move_circle_above(biggest_circle)

    def move_circle_above(self, circle):
        index = circle.parent.children.index(circle)
        new_circle = CircleWidget(circle_size=circle.circle_size, circle_image=circle.circle.texture)
        for child in self.grid_layer_two.children:
            if isinstance(child, CircleWidget):
                self.grid_layer_two.remove_widget(child)
        if len(self.grid_layer_two.children) == 0:
            for i in range((self.grid_layer_one.cols * self.grid_layer_one.rows) - 1):
                self.grid_layer_two.add_widget(SpacerWidget())
        self.grid_layer_two.add_widget(new_circle, index=index)

    def make_circle_full_screen(self, image_name):
        if not self.fullscreen:
            self.escape_full_screen_image()
            self.fullscreen = True
            full_res_images_dir = os.path.dirname(os.path.abspath(__file__)) + "//Full_Res_Memories"
            image_dir = full_res_images_dir + "//" + image_name
            image_widget = KivyImage(source=image_dir, fit_mode="contain")
            self.main_layout.add_widget(image_widget)

    def escape_full_screen_image(self):
        self.fullscreen = False
        for widget in self.main_layout.children:
            if isinstance(widget, KivyImage):
                self.main_layout.remove_widget(widget)


if __name__ == '__main__':
    TheLabApp().run()
