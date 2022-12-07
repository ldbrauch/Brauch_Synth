import math
import time

import pyaudio
from Generators import *

from notes import key_frequencies
import keyboard
import threading
import App


# sample rate must be low in order to allow complicated processes to take place smoothly.
# sample_rate = 11025
# you may need a fast computer to play multiple notes at once :/
max_voices = 2
sample_rate = 44100


# def main():


# code modified from https://python.plainenglish.io/making-a-synth-with-python-oscillators-2cb8e68e9c3b
class Oscillator(VariableOscillator):
    def _post_freq_set(self):
        self._step = (2 * math.pi * self._f) / sample_rate
        self._period = sample_rate / self._f

    def _post_phase_set(self):
        self._p = (self._p / 360) * 2 * math.pi

    def _initialize_osc(self):
        self._i = 0
        self.wave_shape_to_func = [self._sine_iterator, self._square_iterator, self._saw_iterator,
                                   self._triangle_iterator]
        self.iterate = self.wave_shape_to_func[self._wave_shape]  # the default

    def __next__(self):
        return self.iterate()

    # generates a sine wave
    def _sine_iterator(self):
        val = math.sin(self._i + self._p)
        self._i = self._i + self._step
        return val * self._a

    # generates a bunch of frames all at once.
    def sine_gen(self, num_frames):
        stop = self._i + (num_frames * self._step)
        # calculate all the _i values for the next num_frames
        # indexes = np.arange(self._i, stop, self._step)
        indexes = np.linspace(self._i, stop, num=num_frames, endpoint=False)
        # update _i so that it starts where this has ended.
        self._i = stop
        vals = np.sin(indexes) * self._a
        return vals

    # generates a square wave
    def _square_iterator(self):
        val = math.sin(self._i + self._p)
        self._i = self._i + self._step
        # threshold the value to -1 or 1
        if val < 0:
            val = -1
        else:
            val = 1
        return val * self._a

    # generate a sawtooth wave
    def _saw_iterator(self):
        div = (self._i + self._p) / self._period
        val = 2 * (div - math.floor(0.5 + div))
        self._i = self._i + 1
        return val * self._a

    # generate a triangle wave
    def _triangle_iterator(self):
        div = (self._i + self._p) / self._period
        val = 2 * (div - math.floor(0.5 + div))
        val = (abs(val) - 0.5) * 2
        self._i = self._i + 1
        return val * self._a

    # whenever the wave shape is changed it changes the function that __next__ calls.
    def change_wave_shape(self, new_wave_shape):
        self.iterate = self.wave_shape_to_func[new_wave_shape]




# class WaveAdder:
#     def __init__(self, *oscillators):
#         self.oscillators = oscillators
#         self.n = len(oscillators)
#
#     def __iter__(self):
#         [iter(osc) for osc in self.oscillators]
#         return self
#
#     def __next__(self):
#         return sum(next(osc) for osc in self.oscillators) / self.n


# def Freq_mod(init_freq, val):
#     pitch = pitch_slider.get() * 0.12  # divides by 100, multiplies by 12. This is from 0 to 12
#     global pitch_shift
#     pitch_shift = pow(2, pitch / 12)  # turns it in to a factor to multiply the base frequency by.
#     print(pitch_shift)
#
#     return init_freq * val / 12


# the default frequency

default_LFO = 1

LFOs = [
    Oscillator(freq=default_LFO),  # LFO1
    Oscillator(freq=default_LFO),  # LFO2
    Oscillator(freq=default_LFO)  # LFO3
]

# a list of ints, indicating the idnex of the LFOs that are active.
current_amp_LFO = []
current_pitch_LFO = []
# current_phase_LFO = []


class Synthesizer(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.stopping = False
        self.wave_shape = 0  # default waveshape of sine.
        self.notes_dict = {}
        # the total volume basically
        self.amp = 0
        self.setup_stream()

    def run(self):
        self.play()

    def get_samples(self, dictionary, num_samples=256, amp_scale=0.2, max_amp=0.8):
        ## TODO: VECTORIZE THE BELOW LOOP.
        # samples = []
        # for _ in range(num_samples):
        #     samples.append(
        #         [next(osc[0]) * self.amp for _, osc in dictionary.items()]
        #     )
        samples = [osc[0].rend(num_samples) * self.amp for _, osc in dictionary.items()]
        # sums up all the different sounds and reduces the volume
        # samples = np.array(samples).sum(axis=1) * amp_scale
        samples = sum(samples) * amp_scale
        # clips the sound so that it doesn't burst your eardrums
        samples = np.int16(samples.clip(-max_amp, max_amp) * 32767)
        return samples # samples.reshape(num_samples, -1)

    def change_shape(self, shape_index):
        oscillators = [o[0] for k, o in self.notes_dict.items()]
        for osc in oscillators:
            osc.change_wave_shape(shape_index)
        self.wave_shape = shape_index

    def update_pitch(self, factor):
        oscillators = [o[0] for k, o in self.notes_dict.items()]
        for osc in oscillators:
            # osc.change_freq(factor)
            osc.freqScale = factor

    def setup_stream(self):
        self.stream = pyaudio.PyAudio().open(
            rate=sample_rate,
            channels=1,
            format=pyaudio.paInt16,
            output=True,
            frames_per_buffer=256
        )

    def play(self):
        # gets the input and plays the notes
        # these functions prevent add_key from continuously firing when the key is held down. DeBounce.
        def remove_key(e):
            key = str.lower(e.name)
            keyboard.on_press_key(key, add_key)
            if key in self.notes_dict:
                self.notes_dict[key][0].trigger_release()
                self.notes_dict[key][1] = True

        def add_key(e):
            key = str.lower(e.name)
            # only adds it if it isn't there before.
            if not (key in self.notes_dict) or self.notes_dict[key][1]:
                osc = Oscillator(freq=key_frequencies[key],
                                 amp=0.2,
                                 wave_shape=self.wave_shape
                                 )
                # a list of all the modulators for amplitude. Always contains ADSR, can contain additional ones.
                amp_modulators = [ADSREnvelope(attack_duration=app.attack,
                                               decay_duration=app.decay,
                                               sustain_level=app.sustain,
                                               release_duration=app.release,
                                               sample_rate=sample_rate)]

                pitch_modulators = []
                # put in the selected LFOs
                for lfo_index in current_amp_LFO:
                    amp_modulators.append(LFOs[lfo_index])

                for lfo_index in current_pitch_LFO:
                    pitch_modulators.append(LFOs[lfo_index])

                # for lfo_index in current_phase_LFO:
                #     phase_modulators.append(LFOs[lfo_index])

                # sets the frequency incase the pitch slider is not at 1.
                # osc.freq = osc.init_freq * app.pitch

                self.notes_dict[key] = [ModulatedOscillator(osc,
                                                            amp_modulators=amp_modulators,
                                                            freq_modulators=pitch_modulators,
                                                            # phase_modulators=phase_modulators,
                                                            freq_scale=app.pitch
                                                            ),
                                        False]

        # bind all the keys:
        for note in key_frequencies:
            keyboard.on_release_key(note, remove_key)
            keyboard.on_press_key(note, add_key)

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

            if self.stopping:
                print("Stopping!")
                del self.notes_dict
                break

    def stop(self):
        self.stopping = True


# # the main gui
# root = CTk()

class SynthesizerGui(App.Window):
    def onAmpChanged(self, *_):
        self.amp = self.amp_slider.get() / 100
        synth.amp = self.amp

    def onPitchChanged(self, *_):
        # pitch_factor = pow(2, self.pitch_slider.get() / 100)  # turns it in to a factor to multiply the base frequency by.
        pitch_factor = self.pitch_slider.get() / 100
        synth.update_pitch(pitch_factor)  # thread kinda needs to be defined before this is created, *shrug*
        self.pitch = pitch_factor

    # def onPhaseChanged(self, *_):
    #     pass
        # do something

    # closing function which terminates the processes
    def on_closing(self):
        self.destroy()
        synth.stop()
        exit()

    def shape_changed(self, index):
        # doesn't fire twice if index is the same
        if self.wave_shape == index:
            return
        # changes the sound to whatever index it is
        synth.change_shape(shape_index=index)
        self.wave_shape = index

    def amp_LFO_changed(self, lfo_index):
        global current_amp_LFO
        # if it is already set and clicked again, remove it.
        if lfo_index in current_amp_LFO:
            list.remove(current_amp_LFO, lfo_index)
        else:
            current_amp_LFO.append(lfo_index)

    def pitch_LFO_changed(self, lfo_index):
        global current_pitch_LFO
        # if it is already set and clicked again, remove it.
        if lfo_index in current_pitch_LFO:
            list.remove(current_pitch_LFO, lfo_index)
        else:
            current_pitch_LFO.append(lfo_index)

    # def phase_LFO_changed(self, lfo_index):
    #     global current_phase_LFO
    #     # if it is already set and clicked again, remove it.
    #     if lfo_index in current_phase_LFO:
    #         list.remove(current_phase_LFO, lfo_index)
    #     else:
    #         current_phase_LFO.append(lfo_index)
    #     print("LFO for pitch changed to ")
    #     print(current_phase_LFO)

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


if __name__ == '__main__':
    # the keyboard inputs and playing sounds
    synth = Synthesizer()
    # start the gui
    app = SynthesizerGui()
    # start the synthesizer
    synth.start()
    # mainloop required for the gui
    app.mainloop()
