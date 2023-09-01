from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.core.image import Image as CoreImage
from kivy.uix.image import Image as KivyImage
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.textinput import TextInput
from Graph import RotatedLabelWidget, EditablePopup
from kivy.core.window import Window
from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.uix.label import Label
from Memory import CircleWidget
from kivy.config import Config
from kivy.clock import Clock
from kivy.app import App
from io import BytesIO
from PIL import Image
import keyboard
import pickle
import torch
import kivy
import clip
import math
import os


def get_widget_position(widget):
    # Get the center position of the widget within the layout
    widget_pos = widget.parent.parent.to_parent(widget.center_x, widget.center_y)
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


class SpacerWidget(Widget):
    pass


class MemoryMapper(App):

    def build(self):
        self.image_fullscreen = False

        # Disables esc exiting the program
        Config.set('kivy', 'exit_on_escape', '0')
        self.main_layout = RelativeLayout()
        self.main_grid_layout = RelativeLayout(size_hint=(0.8, 0.8))  # Make room for Labels

        self.grid_layer_one = FloatLayout()
        self.grid_layer_one.pos_hint = {'center_x': 0.1, 'center_y': 0.1}  # Center
        self.main_grid_layout.add_widget(self.grid_layer_one)
        self.transparent_button_layout = FloatLayout()
        self.transparent_button_layout.pos_hint = {'center_x': 0.59, 'center_y': 0.59}  # Center
        self.main_grid_layout.add_widget(self.transparent_button_layout)

        self.main_layout.add_widget(self.main_grid_layout)

        # Add labels to the graph
        self.x_label = Label(text='Happiness', size_hint=(None, None), height=50, pos_hint={'bottom': 0, 'center_x': 0.5})
        self.additional_tags_label = Label(text='happiness, sadness, fear, disgust, anger, surprise', size_hint=(None, None), height=50, pos_hint={'top': 1, 'center_x': 0.5})
        self.main_layout.add_widget(self.x_label)
        self.main_layout.add_widget(self.additional_tags_label)

        y_label_layout = AnchorLayout(anchor_x='left', anchor_y='center')
        self.y_label = RotatedLabelWidget()
        self.y_label.label.text = 'Sadness'
        y_label_layout.add_widget(self.y_label)

        # Add buttons to open a popup to edit the labels
        label_button_layout = RelativeLayout()
        self.x_label_button = Button(background_color=(0, 0, 0, 0), on_press=lambda x: EditablePopup(title='x label',
                                    apply_callback=lambda new_text: self.x_label.setter('text')(self.x_label, new_text),
                                    initial_text=self.x_label.text).open(), size_hint=(None, None),
                                    size=(Window.width/2, 40), pos_hint={'y': 0, 'center_x': 0.5})
        self.y_label_button = Button(background_color=(0, 0, 0, 0), on_press=lambda x: EditablePopup(title='y label',
                                    apply_callback=lambda new_text:
                                    self.y_label.label.setter('text')(self.y_label.label, new_text),
                                    initial_text=self.y_label.label.text).open(), size_hint=(None, None),
                                    size=(40, Window.width/2), pos_hint={'center_y': 0.5, 'x': 0})
        # Add one for the additional tags at the top
        self.additional_tags_button = Button(background_color=(0, 0, 0, 0), on_press=lambda x: EditablePopup(title='additional tags',
                                            apply_callback=lambda new_text: self.additional_tags_label.setter('text')(self.additional_tags_label, new_text),
                                            initial_text=self.additional_tags_label.text).open(), size_hint=(None, None), size=(Window.width/2, 40),
                                            pos_hint={'top': 1, 'center_x': 0.5})

        # Add buttons to layout
        label_button_layout.add_widget(self.x_label_button)
        label_button_layout.add_widget(self.y_label_button)
        label_button_layout.add_widget(self.additional_tags_button)

        self.main_layout.add_widget(label_button_layout)
        self.main_layout.add_widget(y_label_layout)

        self.mos_pos = ()
        self.memory_count = 100
        memories_available = len(os.listdir(os.path.dirname(os.path.abspath(__file__)) + '//Full_Res_Memories'))
        if memories_available < self.memory_count:
            self.memory_count = memories_available

        # Generate previews for all memories and cache them (if not done already)
        generate_image_previews()
        self.draw_circles()

        Clock.schedule_interval(self.update, 0.016666)

        return self.main_layout

    def update(self, *args):
        if not self.image_fullscreen:
            self.update_mouse_pos()
            self.set_circle_scale(self.grid_layer_one)

        # When ctrl + r is pressed, redraw the circles
        if keyboard.is_pressed('ctrl+r'):
            self.draw_circles()

        if keyboard.is_pressed('esc') & self.image_fullscreen:
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
                print("no more images found...")
                return

            # Tags to sort the images by
            self.additional_tags = self.additional_tags_label.text.lower().split(',')
            self.additional_tags = [tag.strip() for tag in self.additional_tags]

            tags_to_use = self.x_label.text.lower().strip(), self.y_label.label.text.lower().strip()

            # Remove the tags that are being used from the list of tags if they are in it
            for tag in tags_to_use:
                if tag in self.additional_tags:
                    self.additional_tags.remove(tag)

            # Accessing the full_res variant of the image for the NN
            image_name = os.listdir(memory_thumbnail_folder)[i]
            full_res_image = Image.open(
                os.path.dirname(os.path.abspath(__file__)) + "//Full_Res_Memories" + "//" + image_name)

            image_pos = list(
                plot_image(image_name=image_name, image=full_res_image, xy_params=tags_to_use, additional_tags=self.additional_tags))
            image_pos = [float(image_pos[0]), float(image_pos[1])]

            circle_widget = CircleWidget(circle_size=0.05, circle_image=image)
            with self.grid_layer_one.canvas.after:
                self.grid_layer_one.add_widget(circle_widget)
                circle_widget.pos_hint = {'x': image_pos[0], 'y': image_pos[1]}

            circle_button = Button(background_color=(1, 0, 0, 0),
                                   on_press=lambda x, y=image_name: self.make_circle_full_screen(y))
            circle_button.size_hint = 0.03, 0.03
            self.transparent_button_layout.add_widget(circle_button)
            circle_button.pos_hint = {'x': image_pos[0], 'y': image_pos[1]}

    def set_circle_scale(self, layout):
        biggest_circle = None
        biggest_radius = 0

        for circle in layout.children:
            widget_pos = get_widget_position(circle)

            distance_to_circle = math.dist(widget_pos, self.mos_pos)

            window_scaling_factor = min(Window.height, Window.width) * 2
            if window_scaling_factor == 0:
                window_scaling_factor = 1

            falloff_factor = 1.5
            distance_to_circle **= falloff_factor

            # Ensure the input value is within the specified range
            minimum_radius, maximum_radius = 5, 50
            distance_to_circle = max(window_scaling_factor / maximum_radius,
                                     min(distance_to_circle, window_scaling_factor / minimum_radius))
            distance_to_circle /= window_scaling_factor

            radius = 1 / distance_to_circle
            radius *= 0.003

            circle.update_circle_size(radius)
            if radius > biggest_radius:
                biggest_radius = radius
                biggest_circle = circle
        self.move_circle_above(biggest_circle)

    def move_circle_above(self, circle):
        index = circle.parent.children.index(circle)
        if index != 0:
            self.grid_layer_one.remove_widget(circle)
            self.grid_layer_one.add_widget(circle)

    def make_circle_full_screen(self, image_name):
        if not self.image_fullscreen:
            self.escape_full_screen_image()
            self.image_fullscreen = True
            full_res_images_dir = os.path.dirname(os.path.abspath(__file__)) + "//Full_Res_Memories"
            image_dir = full_res_images_dir + "//" + image_name
            image_widget = KivyImage(source=image_dir, fit_mode="contain")
            self.main_layout.add_widget(image_widget)

    def escape_full_screen_image(self):
        self.image_fullscreen = False
        for widget in self.main_layout.children:
            if isinstance(widget, KivyImage):
                self.main_layout.remove_widget(widget)


def plot_image(image_name, image, xy_params, additional_tags):
    params = list(xy_params)
    params.extend(list(additional_tags))

    loaded_probs = load_memory_probabilities(name=image_name, tags=params)
    if loaded_probs is not None:
        print(f'{image_name} plotted at {loaded_probs[xy_params[0]], loaded_probs[xy_params[1]]}')
        return loaded_probs[xy_params[0]], loaded_probs[xy_params[1]]

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model, preprocess = clip.load("ViT-L/14@336px", device=device)

    image = preprocess(image).unsqueeze(0).to(device)
    text = clip.tokenize(params).to(device)

    with torch.no_grad():
        logits_per_image, logits_per_text = model(image, text)
        probs = logits_per_image.softmax(dim=-1).cpu().numpy()

    save_memory_probabilities(name=image_name, tags=params, probabilities=probs[0])
    print(f'{image_name} plotted at {probs[0, :2]}')
    return probs[0, :2]


def load_memory_probabilities(name, tags):
    tags = tuple(sorted(tags))  # Sort so that order doesn't matter
    file_name = 'cache//' + name + '.pickle'

    if not os.path.isfile(file_name) or os.path.getsize(file_name) <= 0:
        return

    with open(file_name, 'rb') as f:
        memory_dict = pickle.load(f)
        if tags in memory_dict:
            return dict(zip(tags, memory_dict[tags]))


def save_memory_probabilities(name, tags, probabilities):
    file_name = 'cache//' + name + '.pickle'

    # Sort so that order doesn't matter when loading it later
    tag_probabilities = dict(zip(tags, probabilities))
    tags = tuple(sorted(tags))
    tag_probabilities = {tag: tag_probabilities[tag] for tag in tags}
    probabilities = tuple(tag_probabilities.values())

    memory_dict = {tags: tuple(probabilities)}

    if not os.path.isfile(file_name):
        open(file_name, 'x')

    if os.path.isfile(file_name) and os.path.getsize(file_name) > 0:
        with open(file_name, 'rb') as f:
            old_memory_dict = pickle.load(f)
            memory_dict.update(old_memory_dict)

    with open(file_name, 'wb') as f:
        pickle.dump(memory_dict, f, pickle.HIGHEST_PROTOCOL)


if __name__ == '__main__':
    MemoryMapper().run()
