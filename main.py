from Memory import CircleWidget, ExpandableBarLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.core.image import Image as CoreImage
from kivy.uix.image import Image as KivyImage
from kivy.uix.gridlayout import GridLayout
from kivy.core.window import Window
from kivy.uix.widget import Widget
from kivy.uix.button import Button
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
        self.memory_count = 10

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

        for i in range(self.grid_layer_one.cols * self.grid_layer_one.rows):
            self.grid_layer_one.add_widget(ExpandableBarLayout())
            self.transparent_button_layout.add_widget(ExpandableBarLayout())

        for i in range(self.memory_count):
            if len(os.listdir(memory_thumbnail_folder)) > i:
                image_dir = memory_thumbnail_folder + "//" + os.listdir(memory_thumbnail_folder)[i]
                image = Image.open(image_dir)
                image = image_to_texture(image)
            else:
                print("no more images found...")
                return

            # Tags to sort the images by
            tags = ['Happiness', 'Sadness', 'Fear', 'Disgust', 'Anger', 'Surprise']
            tag_indices_to_use = (0, 1)
            tags_to_use = (tags[tag_indices_to_use[0]], tags[tag_indices_to_use[1]])
            tags.pop(tag_indices_to_use[0])
            tags.pop(tag_indices_to_use[1] - 1)

            # Accessing the full_res variant of the image for the NN
            image_name = os.listdir(memory_thumbnail_folder)[i]
            full_res_image = Image.open(
                os.path.dirname(os.path.abspath(__file__)) + "//Full_Res_Memories" + "//" + image_name)

            image_pos = list(
                plot_image(image_name=image_name, image=full_res_image, xy_params=tags_to_use, additional_tags=tags))
            image_pos = (1 - image_pos[0], 1 - image_pos[1])  # Reverses direction
            index = self.index_by_pos(image_pos)

            circle_widget = CircleWidget(circle_size=0.05, circle_image=image)
            with self.grid_layer_one.canvas.after:
                print(f"index:{index}, and amount of children:{len(self.grid_layer_one.children)}")
                self.grid_layer_one.children[index].add_widget(circle_widget)

            circle_button = Button(background_color=(1, 0, 0, 0),
                                   on_press=lambda x, y=image_name: self.make_circle_full_screen(y))
            self.transparent_button_layout.children[index].add_widget(circle_button)

    def index_by_pos(self, pos):
        cols = self.grid_layer_one.cols
        rows = self.grid_layer_one.rows
        print(rows, cols)
        x, y = pos
        current_row_count = math.floor(x * cols)
        index = (max((math.floor(y * rows)) - 1, 0) * cols) + current_row_count  # Cover the area not in current row
        print(index)
        return int(index)

    def set_circle_scale(self, layout):
        biggest_circle = None
        biggest_radius = 0

        for bar in layout.children:
            for circle in bar.children:
                if not isinstance(circle, CircleWidget):
                    continue

                widget_pos = get_widget_position(circle)

                distance_to_circle = math.dist(widget_pos, self.mos_pos)

                window_scaling_factor = min(Window.height, Window.width) * 2
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
        bar_child_count = len(circle.parent.children)
        bar_index = circle.parent.children.index(circle)
        overall_index = circle.parent.parent.children.index(circle.parent)
        new_circle = CircleWidget(circle_size=circle.circle_size, circle_image=circle.circle.texture)

        for layout in self.grid_layer_two.children:
            layout.clear_widgets()

        if len(self.grid_layer_two.children) == 0:
            print('adding empties')
            for i in range(self.grid_layer_one.cols * self.grid_layer_one.rows):
                self.grid_layer_two.add_widget(ExpandableBarLayout())

        target_bar = self.grid_layer_two.children[overall_index]
        for i in range(bar_child_count - 1):
            target_bar.add_widget(SpacerWidget())
        target_bar.add_widget(new_circle, index=bar_index)

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


def plot_image(image_name, image, xy_params, additional_tags):
    params = list(xy_params)
    params.extend(list(additional_tags))

    loaded_probs = load_memory_probabilities(name=image_name, tags=params)
    if loaded_probs is not None:
        return loaded_probs[:2]

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model, preprocess = clip.load("ViT-L/14@336px", device=device)

    image = preprocess(image).unsqueeze(0).to(device)
    text = clip.tokenize(params).to(device)

    with torch.no_grad():
        '''
        image_features = model.encode_image(image)
        text_features = model.encode_text(text)
        '''

        logits_per_image, logits_per_text = model(image, text)
        probs = logits_per_image.softmax(dim=-1).cpu().numpy()

    save_memory_probabilities(name=image_name, tags=params, probabilities=probs[0])
    return probs[0, :2]


def load_memory_probabilities(name, tags):
    tags = tuple(tags)
    file_name = 'cache//' + name + '.pickle'

    if not os.path.isfile(file_name) or os.path.getsize(file_name) <= 0:
        return

    with open(file_name, 'rb') as f:
        memory_dict = pickle.load(f)
        if tags in memory_dict:
            print('successfully loaded...')
            return memory_dict[tags]


def save_memory_probabilities(name, tags, probabilities):
    file_name = 'cache//' + name + '.pickle'
    memory_dict = {tuple(tags): tuple(probabilities)}

    if not os.path.isfile(file_name):
        open(file_name, 'x')

    with open(file_name, 'wb') as f:
        pickle.dump(memory_dict, f, pickle.HIGHEST_PROTOCOL)


if __name__ == '__main__':
    TheLabApp().run()
