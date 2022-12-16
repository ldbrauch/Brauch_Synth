import math
import time

import pyaudio
from Generators import *

from notes import key_frequencies
import keyboard
import threading
import App

# the number of notes you can play at a time
max_voices = 12
# the quality of the sound
sample_rate = 44100
# how many samples are played at a time
buffer_size = 256
# the defualt LFO frequency
default_LFO_freq = 1
# the maximum amplitude for the LFOs. If above 1, may cause clipping.
max_lfo_amp = 5


# code modified from https://python.plainenglish.io/making-a-synth-with-python-oscillators-2cb8e68e9c3b
# has a generator for basic waveshapes, and the used generator can be changed
class Oscillator(VariableOscillator):

    def _post_freq_set(self):
        # this can be a number or an array
        self._step = (2 * math.pi * self._f * self.detune) / sample_rate
        self._period = sample_rate / (self._f * self.detune)

    def _post_phase_set(self):
        self._p = (self._p / 360) * 2 * math.pi

    def __next__(self):
        return self.rend()

    # generates a bunch of frames all at once for a sine wave.
    def _sine_iterator(self):
        return np.sin(self.next_indexes) * self._a

    # generates a square wave
    def _square_iterator(self):
        vals = np.sin(self.next_indexes)
        # threshold the value to -1 or 1
        vals = np.where(vals > 0, 1.0, -1.0)
        return vals * self._a

    # generate a sawtooth wave
    def _saw_iterator(self):
        end = self._i + self.buffer_size
        indexes = np.linspace(self._i, end, num=self.buffer_size, endpoint=False)
        divs = indexes / self._period
        floor = np.floor(0.5 + divs)
        vals = 2 * (divs - floor)
        self._i = end
        return vals * self._a

    # generate a triangle wave
    def _triangle_iterator(self):
        end = self._i + self.buffer_size
        indexes = np.linspace(self._i, end, num=self.buffer_size, endpoint=False)
        vals = indexes / self._period
        divs = 2 * (vals - np.floor(0.5 + vals))
        divs = (np.abs(divs) - 0.5) * 2
        self._i = end
        return divs * self._a

    # whenever the wave shape is changed it changes the function that __next__ calls.
    def change_wave_shape(self, new_wave_shape):
        self.wave_shape
        self.rend = self.wave_shape_to_func[new_wave_shape]


# the three starting LFOs. They will be modified via user input
LFOs = [
    Oscillator(freq=default_LFO_freq, buffer_size=buffer_size),  # LFO1
    Oscillator(freq=default_LFO_freq, buffer_size=buffer_size),  # LFO2
    Oscillator(freq=default_LFO_freq, buffer_size=buffer_size)  # LFO3
]

# a list of ints, indicating the index of the LFOs that are active.
current_amp_LFO = []
current_pitch_LFO = []


# this is the class that plays the sounds. It has to be in another thread so that the user can still interact with the  GUI.
class Synthesizer(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.stopping = False
        self.wave_shape = 0  # default waveshape of sine.
        self.notes_dict = {}  # all the notes that are being held down
        # the total volume basically
        self.amp = 0
        # the frequency slider default detune of 1 = none. 2 = one octave.
        self.detune = 1
        self.setup_stream()

    def run(self):
        self.play()

    # gets and returns all the necessary samples to be played
    def get_samples(self, dictionary, amp_scale=0.2, max_amp=0.9):
        # gets an array of arrays of all the samples by calling rend() on each ModulatedOscillator that is active
        samples = [osc[0].rend() * self.amp for _, osc in list(dictionary.items())]
        # sums up all the different sounds and reduces the volume
        samples = sum(samples) * amp_scale
        # clips the sound so that it doesn't burst your eardrums
        samples = np.int16(samples.clip(-max_amp, max_amp) * 32767)
        return samples

        # this function changes the wave shape for all the oscillators that are being held down.

    def change_shape(self, shape_index):
        oscillators = [o[0] for k, o in self.notes_dict.items()]
        for osc in oscillators:
            osc.change_wave_shape(shape_index)
        self.wave_shape = shape_index

    # changes the pitch for all the oscillators when the slider is changed.
    def update_pitch(self, factor):
        oscillators = [o[0] for k, o in self.notes_dict.items()]
        for osc in oscillators:
            osc.detune(factor)
        self.detune = factor

    # the stream is what plays the sound to your speakers.
    def setup_stream(self):
        self.stream = pyaudio.PyAudio().open(
            rate=sample_rate,
            channels=1,
            format=pyaudio.paInt16,
            output=True,
            frames_per_buffer=buffer_size
        )

    def play(self):
        # gets the input and plays the notes
        # these functions prevent add_key from continuously firing when the key is held down. AKA a debounce method.
        def remove_key(e):
            key = str.lower(e.name)
            keyboard.on_press_key(key, add_key)
            if key in self.notes_dict:
                self.notes_dict[key][0].trigger_release()
                self.notes_dict[key][1] = True

        def add_key(e):
            key = str.lower(e.name)
            # only adds it if it isn't there before.
            if (not (key in self.notes_dict) or self.notes_dict[key][1]) and len(self.notes_dict) < max_voices:
                osc = Oscillator(freq=key_frequencies[key],
                                 amp=0.2,
                                 wave_shape=self.wave_shape,
                                 detune=self.detune
                                 )
                ADSR = ADSREnvelope(attack_duration=app.attack,
                                    decay_duration=app.decay,
                                    sustain_level=app.sustain,
                                    release_duration=app.release,
                                    sample_rate=sample_rate,
                                    buffer_size=buffer_size)

                # a list of all the modulators for amplitude. Always contains ADSR, can contain additional ones.
                amp_modulators = [ADSR]

                pitch_modulators = []
                # if there are any LFOs, create the oscillators for them
                for i in range(3):
                    if i in current_amp_LFO:
                        lfo = Oscillator(LFOs[i].freq, amp=LFOs[i].amp, wave_shape=LFOs[i].wave_shape,
                                         buffer_size=buffer_size)
                        amp_modulators.append(lfo)
                    if i in current_pitch_LFO:
                        lfo = Oscillator(LFOs[i].freq, amp=LFOs[i].amp, wave_shape=LFOs[i].wave_shape,
                                         buffer_size=buffer_size)
                        pitch_modulators.append(lfo)

                self.notes_dict[key] = [ModulatedOscillator(osc,
                                                            amp_modulators=amp_modulators,
                                                            freq_modulators=pitch_modulators,
                                                            freq_scale=app.pitch
                                                            ),
                                        False]

        # bind all the keys:
        for note in key_frequencies:
            keyboard.on_release_key(note, remove_key)
            keyboard.on_press_key(note, add_key)

        # the while loop that detects if keys are held down and plays sounds if so.
        while True:
            if self.notes_dict:
                # Play the notes
                samples = self.get_samples(self.notes_dict)
                self.stream.write(samples.tobytes())
            else:
                # I have to yield it a bit or else it will be very glitchy.
                time.sleep(0.01)

            # checks if any of the notes have been released AND have finished their release envelope.
            ended_notes = [k for k, o in self.notes_dict.items() if o[0].ended and o[1]]
            for note in ended_notes:
                del self.notes_dict[note]
            # terminates the while loop if it is stopped
            if self.stopping:
                del self.notes_dict
                break

    # this may be necessary to stop the while loop incase it does not terminate.
    def stop(self):
        self.stopping = True


# the main gui
class SynthesizerGui(App.Window):
    def onAmpChanged(self, *_):
        self.amp = self.amp_slider.get() / 100
        synth.amp = self.amp
        # for the entry
        self.oldAmp = 1

    def onPitchChanged(self, *_):
        pitch_factor = pow(2,
                           self.pitch_slider.get() / 100)  # turns it in to a factor to multiply the base frequency by.
        synth.update_pitch(pitch_factor)  # thread kinda needs to be defined before this is created, *shrug*
        self.pitch = pitch_factor

    # closing function which terminates the processes when the window is closed
    def on_closing(self):
        self.destroy()
        synth.stop()
        exit()

    def shape_changed(self, index, lfo):
        # changed the total sound waveshape
        if lfo is None:
            # doesn't fire twice if index is the same
            if self.wave_shape == index:
                return
            # change the color of the button
            self.buttons[index].fg_color = self.active_color
            self.buttons[self.wave_shape].fg_color = self.passive_color
            # have to fire this or else it wont update until i hover over it
            self.buttons[self.wave_shape].draw()
            # changes the sound to whatever index it is
            synth.change_shape(shape_index=index)
            self.wave_shape = index
        else:
            # changes the waveshape of an LFO
            # don't do anything if its already there
            if LFOs[lfo].wave_shape == index:
                return

            # change the color of the button
            self.lfo_buttons[lfo][index].fg_color = self.active_color
            self.lfo_buttons[lfo][LFOs[lfo].wave_shape].fg_color = self.passive_color
            self.lfo_buttons[lfo][LFOs[lfo].wave_shape].draw()
            # changes the sound to whatever index it is
            LFOs[lfo].wave_shape = index
            # self.wave_shape = index

    def amp_LFO_changed(self, lfo_index):
        global current_amp_LFO
        # if it is already set and clicked again, remove it.
        if lfo_index in current_amp_LFO:
            self.amp_lfo_buttons[lfo_index].fg_color = self.passive_color
            list.remove(current_amp_LFO, lfo_index)
        else:
            # add the lfo to amplitude
            self.amp_lfo_buttons[lfo_index].fg_color = self.active_color
            current_amp_LFO.append(lfo_index)

    def pitch_LFO_changed(self, lfo_index):
        global current_pitch_LFO
        # if it is already set and clicked again, remove it.
        if lfo_index in current_pitch_LFO:
            self.pitch_lfo_buttons[lfo_index].fg_color = self.passive_color
            list.remove(current_pitch_LFO, lfo_index)
        else:
            self.pitch_lfo_buttons[lfo_index].fg_color = self.active_color
            current_pitch_LFO.append(lfo_index)

    def onPeriodChanged(self, periodVal, lfo_index):
        global LFOs
        # change the period/frequency for the amplitude
        try:
            newFreq = 1 / float(periodVal.get())
        except:
            # don't change it if it is invalid
            return
            # period.set(oldFreq)
        # change the frequency
        LFOs[lfo_index].freq = newFreq

    def onLFOAmpChanged(self, ampVal, LFO_index):
        global LFOs

        # change the period/frequency for the amplitude
        try:
            newAmp = float(ampVal.get())
            # do nothing if its invalid

            if newAmp > max_lfo_amp or newAmp < 0:
                ampVal.set(self.oldAmp)
                return
        except:
            # don't change it if it is invalid
            return
        # change the amplitude
        LFOs[LFO_index].amp = newAmp


# start the program
if __name__ == '__main__':
    # the keyboard inputs and playing sounds
    synth = Synthesizer()
    # start the gui
    app = SynthesizerGui()
    # start the synthesizer
    synth.start()
    # mainloop required for the gui
    app.mainloop()
