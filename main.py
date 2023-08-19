from kivy.app import App
from kivy.uix.gridlayout import GridLayout
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.graphics import Ellipse
from kivy.core.window import Window
from kivy.clock import Clock
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

    def move_above(self):
        # Move widget above the other widgets in a parent. WIP function

        # Increase the index of above_button to move it above the circles
        self.circle.index += 1


class TheLabApp(App):

    def build(self):
        self.main_layout = GridLayout(cols=20, rows=12, spacing=10)
        self.mos_pos = ()
        self.memory_count = 240

        # Generate previews for all memories and cache them (if not done already)
        generate_image_previews()
        self.update_circles()

        Clock.schedule_interval(self.update(), 0.1)

        return self.main_layout

    def update(self):
        self.update_mouse_pos()
        self.set_circle_scale(self.main_layout)

    def update_mouse_pos(self, *args):
        if Window.focus:
            # Get the mouse position using Kivy's Window module
            self.mos_pos = Window.mouse_pos
            # Adjust for pixel density
            self.mos_pos = (self.mos_pos[0] * kivy.metrics.dp(1), self.mos_pos[1] * kivy.metrics.dp(1))

    def update_circles(self):
        self.main_layout.clear_widgets()

        memory_thumbnail_folder = os.path.dirname(os.path.abspath(__file__)) + "//Memory_Thumbnails"

        for i in range(self.memory_count):
            if len(os.listdir(memory_thumbnail_folder)) > i:
                image = Image.open(memory_thumbnail_folder + "//" + os.listdir(memory_thumbnail_folder)[i])
                image = image_to_texture(image)
            else:
                print("no images found...")
                image = None

            circle_widget = CircleWidget(circle_size=0.05, circle_image=image)
            self.main_layout.add_widget(circle_widget)

    def set_circle_scale(self, layout):
        i = 0
        biggest_circle = None
        closest_distance = math.inf

        for circle in layout.children:
            widget_pos = get_widget_position(circle)

            distance_to_circle = math.dist(widget_pos, self.mos_pos)
            if distance_to_circle < closest_distance:
                biggest_circle = circle

            window_scaling_factor = Window.height + Window.width

            # Ensure the input value is within the specified range
            distance_to_circle = max(window_scaling_factor / 100, min(distance_to_circle, window_scaling_factor / 2))
            distance_to_circle /= window_scaling_factor
            radius = 1 / distance_to_circle
            radius *= 0.02
            circle.update_circle_size(radius)
            i += 1


if __name__ == '__main__':
    TheLabApp().run()
