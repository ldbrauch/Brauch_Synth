import customtkinter as ctk
import tkinter
from PIL import Image, ImageTk
from tkinter import ttk


# a function that returns a square image at path and size image_size
def load_image(path, imageSize):
    """ load rectangular image with path relative to PATH """
    return ImageTk.PhotoImage(Image.open(path).resize((image_size, imageSize)))


image_size = 40
border_width = 1
button_size = image_size + border_width * 8
LFO_button_size = int(button_size / 2)
# the image directories
sin_image = "assets/sine_icon.png"
square_image = "assets/square_icon.png"
saw_image = "assets/saw_icon.png"
triange_image = "assets/triangle_icon.png"
# the maximum attack, decay, and release.
max_adr = 10

# custom theme
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("syntheme.json")


# code modified from https://stackoverflow.com/questions/59642558/how-to-set-tkinter-scale-sliders-color
# for custom sliders.
class SlimSlider(ttk.Scale):
    def __init__(self, master=None, **kw):
        kw.setdefault("orient", "vertical")
        self.variable = kw.pop('variable', tkinter.DoubleVar(master))
        ttk.Scale.__init__(self, master, variable=self.variable, **kw)
        self._style_name = '{}.custom.{}.TScale'.format(self, kw[
            'orient'].capitalize())  # unique style name to handle the text
        self['style'] = self._style_name


# the main gui
def make_LFO_buttons(master, command):
    LFO1_button = ctk.CTkButton(master, corner_radius=0,
                                width=LFO_button_size, height=LFO_button_size,
                                command=lambda: command(0), text="1", border_width=border_width)
    LFO1_button.grid(row=0, column=0, pady=1, padx=0, sticky="n")
    LFO2_button = ctk.CTkButton(master, corner_radius=0,
                                width=LFO_button_size, height=LFO_button_size,
                                command=lambda: command(1), text="2", border_width=border_width)
    LFO2_button.grid(row=0, column=1, pady=1, padx=0, sticky="n")
    LFO3_button = ctk.CTkButton(master, corner_radius=0,
                                width=LFO_button_size, height=LFO_button_size,
                                command=lambda: command(2), text="3", border_width=border_width)
    LFO3_button.grid(row=0, column=2, pady=1, padx=0, sticky="n")


class Window(ctk.CTk):
    def __init__(self, wave_shape=0):
        super().__init__()
        self.wave_shape = wave_shape
        self.pitch = 1
        self.amp = 0
        # create the gui
        panel_size = 300
        self.geometry("600x600")
        self.configure(bg="#270126")
        self.resizable(0, 0)
        self.title("SilverSynth v1")
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        # load the icons
        self.sin_image = load_image(sin_image, image_size)
        self.square_image = load_image(square_image, image_size)
        self.saw_image = load_image(saw_image, image_size)
        self.triange_image = load_image(triange_image, image_size)

        self.img_slider = tkinter.PhotoImage(master=self, file="assets/slider_knob2.png")
        self.img_trough = tkinter.PhotoImage(master=self, file="assets/slider_Trough.png")
        # custom slider
        self.style = ttk.Style(self)
        self.style.configure('TScale', background="#270126")
        self.style.element_create('custom.Scale.slider', 'image', self.img_slider)
        self.style.element_create('custom.Scale.trough', 'image', self.img_trough)
        # create custom layout for slider
        self.style.layout('custom.Vertical.TScale',
                          [('custom.Scale.trough', {'sticky': 'ns'}),
                           ('custom.Scale.slider',
                            {'side': 'top', 'sticky': ''
                             })])

        self.grid_columnconfigure(2, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # the top left frame, where the ASDR knobs are
        self.left_frame = ctk.CTkFrame(self, width=panel_size)
        self.left_frame.grid(column=0, row=0, sticky="NW")
        self.attack_label = ctk.CTkLabel(self.left_frame, text="Attack")
        self.attack_label.grid(column=0, row=1)
        self.attack_slider = ctk.CTkSlider(self.left_frame, from_=0, to=1, number_of_steps=100, width=100)
        self.attack_slider.grid(column=0, row=2)
        self.decay_label = ctk.CTkLabel(self.left_frame, text="Decay")
        self.decay_label.grid(column=0, row=3)
        self.decay_slider = ctk.CTkSlider(self.left_frame, from_=0.001, to=1, number_of_steps=100, width=100)
        self.decay_slider.grid(column=0, row=4)
        self.sustain_label = ctk.CTkLabel(self.left_frame, text="Sustain")
        self.sustain_label.grid(column=0, row=5)
        self.sustain_slider = ctk.CTkSlider(self.left_frame, from_=0, to=1, number_of_steps=100, width=100)
        self.sustain_slider.grid(column=0, row=6)
        self.release_label = ctk.CTkLabel(self.left_frame, text="Release")
        self.release_label.grid(column=0, row=7)
        self.release_slider = ctk.CTkSlider(self.left_frame, from_=0, to=1, number_of_steps=100, width=100)
        self.release_slider.grid(column=0, row=8)

        # the middle top frame - empty?
        self.mid_frame = ctk.CTkFrame(self)
        self.mid_frame.grid(column=1, row=0, sticky="nswe")

        # the top right frame, which houses the wave shape buttons and amp/pitch sldiers.
        self.right_frame = ctk.CTkFrame(self, width=panel_size)
        self.right_frame.grid(column=2, row=0, sticky="ne")
        # 1st frame: the label
        self.waveshape_label = ctk.CTkLabel(self.right_frame, text="Waveshape")
        self.waveshape_label.grid(row=0, columnspan=1, padx=1, pady=10, sticky="")
        # 2nd frame: the wave shape buttons
        self.wave_frame = ctk.CTkFrame(self.right_frame)
        self.wave_frame.grid(row=1, column=0, padx=10, pady=10)
        self.sin_button = ctk.CTkButton(self.wave_frame, image=self.sin_image, corner_radius=0,
                                        width=button_size, height=button_size,
                                        command=lambda: self.shape_changed(0), text="", border_width=border_width)
        self.sin_button.grid(row=0, column=0, pady=1, padx=0, sticky="n")
        self.square_button = ctk.CTkButton(self.wave_frame, image=self.square_image, corner_radius=0,
                                           width=button_size, height=button_size,
                                           command=lambda: self.shape_changed(1), text="", border_width=border_width)
        self.square_button.grid(row=0, column=1, pady=1, padx=0, sticky="n")
        self.saw_button = ctk.CTkButton(self.wave_frame, image=self.saw_image, corner_radius=0,
                                        width=button_size, height=button_size,
                                        command=lambda: self.shape_changed(2), text="", border_width=border_width)
        self.saw_button.grid(row=0, column=2, pady=1, padx=0, sticky="n")
        self.triangle_button = ctk.CTkButton(self.wave_frame, image=self.triange_image, corner_radius=0,
                                             width=button_size, height=button_size,
                                             command=lambda: self.shape_changed(3), text="", border_width=border_width)
        self.triangle_button.grid(row=0, column=3, pady=1, padx=0, sticky="n")
        # 3rd frame: the labels and the sliders
        self.slider_frame = ctk.CTkFrame(self.right_frame, border_width=0, width=300)
        self.slider_frame.grid(row=3, padx=10, pady=1)
        self.label_amplitude = ctk.CTkLabel(self.slider_frame, text="Amplitude", width=5)
        self.label_amplitude.grid(row=0, column=0, padx=10)
        self.label_pitch = ctk.CTkLabel(self.slider_frame, text="Pitch", width=5)
        self.label_pitch.grid(row=0, column=1, padx=10)
        # the amp slider
        self.amp_slider = SlimSlider(self.slider_frame, from_=100, to=0, length=25)  # upside down for some reason
        self.amp_slider.grid(column=0, row=1)
        self.amp_slider.variable.trace_add("write", self.onAmpChanged)
        self.amp_LFO_frame = ctk.CTkFrame(self.slider_frame)
        self.amp_LFO_frame.grid(column=0, row=2)
        make_LFO_buttons(self.amp_LFO_frame, self.amp_LFO_changed)
        # the pitch slider
        self.pitch_slider = SlimSlider(self.slider_frame, from_=100, to=0)
        self.pitch_slider.grid(column=1, row=1)
        self.pitch_slider.variable.trace_add("write", self.onPitchChanged)
        self.pitch_LFO_frame = ctk.CTkFrame(self.slider_frame)
        self.pitch_LFO_frame.grid(column=1, row=2)
        make_LFO_buttons(self.pitch_LFO_frame, self.pitch_LFO_changed)

        # the bottom left frame
        self.bl_frame = ctk.CTkFrame(self)
        self.bl_frame.grid(column=0, row=2, sticky="SE")
        self.LFO1_frame = ctk.CTkFrame(self.bl_frame)
        self.LFO1_frame.grid(column=0, row=0)
        self.lfo1_label = ctk.CTkLabel(self.LFO1_frame, text="LFO 1")
        self.lfo1_label.grid(column=0, row=0)
        # the period box
        self.period1_frame = ctk.CTkFrame(self.LFO1_frame)
        self.period1_frame.grid(column=0, row=1)
        self.period1_label = ctk.CTkLabel(self.period1_frame, text="period", width=90)
        self.period1_label.grid()
        self.period1 = self.new_period(0)
        self.period1_entry = ctk.CTkEntry(self.period1_frame, width=100, textvariable=self.period1)
        self.period1_entry.grid(column=0, row=1)  # stick defines which side of the grid it will be at

    # logarithmically calculate these so that you can be more precise with values near 0.
    @property
    def attack(self):
        attack = pow(max_adr + 1, self.attack_slider.get()) - 1
        return attack

    @property
    def decay(self):
        decay = pow(max_adr + 1, self.decay_slider.get()) - 1
        return decay

    @property
    def sustain(self):
        # from zero to one already.
        return self.sustain_slider.get()

    @property
    def release(self):
        release = pow(max_adr + 1, self.release_slider.get()) - 1
        return release

    # gets the amplitude from the amplitude slider
    # @property
    # def get_amplitude(self):
    #     return self.amp_slider.get() / 100

    def onPitchChanged(self, *_):
        pass

    def onAmpChanged(self, *_):
        pass


    def shape_changed(self, index):
        pass

    def amp_LFO_changed(self, lfo_index):
        pass

    def pitch_LFO_changed(self, lfo_index):
        pass


    def LFO_changed(self, lfo_index, value_type):
        pass

    def onPeriodChanged(self, periodVal, lfo_index):
        pass

    def new_period(self, lfo_index):
        string_var = tkinter.StringVar(value="1.0")
        string_var.trace('w',
                         lambda name, index, mode, string_var=string_var: self.onPeriodChanged(string_var, lfo_index))
        return string_var

# creates the [1][2][3] buttons to change which LFO is affecting some value determined by command.
# doesnt put it in the right place for some reason.
# class LFOButtons(ctk.CTkFrame):
#     def __init__(self, master2=None, command=None):
#         super().__init__()
#         self.master = master2
#         self.LFO1_button = ctk.CTkButton(self, corner_radius=0,
#                                          width=LFO_button_size, height=LFO_button_size,
#                                          command=lambda: command(0), text="1", border_width=border_width)
#         self.LFO1_button.grid(row=0, column=0, pady=1, padx=0, sticky="n")
#         self.LFO2_button = ctk.CTkButton(self, corner_radius=0,
#                                          width=LFO_button_size, height=LFO_button_size,
#                                          command=lambda: command(1), text="2", border_width=border_width)
#         self.LFO2_button.grid(row=0, column=1, pady=1, padx=0, sticky="n")
#         self.LFO3_button = ctk.CTkButton(self, corner_radius=0,
#                                          width=LFO_button_size, height=LFO_button_size,
#                                          command=lambda: command(2), text="3", border_width=border_width)
#         self.LFO3_button.grid(row=0, column=2, pady=1, padx=0, sticky="n")
