# Code from https://python.plainenglish.io/making-a-synth-with-python-oscillators-2cb8e68e9c3b
# and from https://python.plainenglish.io/build-your-own-python-synthesizer-part-2-66396f6dad81

from abc import ABC, abstractmethod
import itertools
import numpy as np


# a simple oscillator that can change wave shape while a note is playing
class VariableOscillator(ABC):
    def __init__(self, freq=440, phase=0, amp=1, wave_range=(-1, 1), wave_shape=0):
        # the initial conditions, so that it remembers what it started at
        self._freq = freq
        self._amp = amp
        self._phase = phase
        self._wave_range = wave_range
        self._wave_shape = wave_shape

        # Properties that will be changed
        self._f = freq
        self._a = amp
        self._p = phase

        self.freq = self._freq
        self.phase = self._phase
        self.amp = self._amp
        self._initialize_osc()

    # the initial properties
    @property
    def init_freq(self):
        return self._freq

    @property
    def init_amp(self):
        return self._amp

    @property
    def init_phase(self):
        return self._phase

    # get the current frequency
    @property
    def freq(self):
        return self._f

    # changes the frequency
    @freq.setter
    def freq(self, value):
        self._f = value
        self._post_freq_set()

    # same for amp and phase
    @property
    def amp(self):
        return self._a

    @amp.setter
    def amp(self, value):
        self._a = value
        self._post_amp_set()

    @property
    def phase(self):
        return self._p

    @phase.setter
    def phase(self, value):
        self._p = value
        self._post_phase_set()

    def _post_freq_set(self):
        pass

    def _post_amp_set(self):
        pass

    def change_wave_shape(self, value):
        pass

    def _post_phase_set(self):
        pass

    @abstractmethod
    def _initialize_osc(self):
        pass

    @staticmethod
    def squish_val(val, min_val=0, max_val=1):
        return (((val + 1) / 2) * (max_val - min_val)) + min_val

    @abstractmethod
    def __next__(self):
        return None

    def sine_gen(self, num_frames):
        pass

# a class that will modulate the oscillator via the modulators inputted.
class ModulatedOscillator:
    def __init__(self, oscillator, amp_modulators=None, freq_modulators=None, freq_scale=0):
        self.oscillator = oscillator
        self.amp_mods = amp_modulators  # a list of modulators
        self.freq_mods = freq_modulators  # list
        # self.phase_mods = phase_modulators  # list
        self.freqScale = freq_scale
        # a list of all the modulators in one place
        # self.modulators = amp_modulators.append(freq_mods).append(phase_mods)

        # self._modulators_count = len(self.modulators)

    def __iter__(self):
        iter(self.oscillator)
        # [iter(modulator) for modulator in self.modulators]
        # iterate through all the modulators if applicable
        [iter(amp_modulator) for amp_modulator in self.amp_mods]
        [iter(amp_modulator) for amp_modulator in self.freq_mods]
        # [iter(amp_modulator) for amp_modulator in self.phase_mods]
        return self

    def _modulate(self):
        # if any amplitude modulators are passed through, modulate the sound.
        # amp_mod is the amplitude of all the modulators multiplied for that frame.
        if self.amp_mods:
            amp_mod = np.ndarray.prod(np.array([next(amp_mod) for amp_mod in self.amp_mods]))
            # amp_mod = next(self.amp_mods[0])

            # amp_mod = np.ndarray.prod(mod_vals)
            self.oscillator.amp = self.oscillator.init_amp * amp_mod
            # print(new_amp)
        if self.freq_mods:
            # freq_factor = pow(2, np.sum([next(freq_mod) * self.freqScale for freq_mod in self.freq_mods]))
            freq_factor = pow(2, next(self.freq_mods[0]) * self.freqScale)
            new_freq = freq_factor * self.oscillator.init_freq
            self.oscillator.freq = new_freq

        # if self.phase_mods is not None:
        #     phase_mod = np.prod([next(phase_mod) for phase_mod in self.phase_mods]) * 360
        #     new_phase = self.oscillator.init_phase + phase_mod
        #     self.oscillator.phase = new_phase
        #     # TODO: Dont include phase?

        #     if self._modulators_count == 3:
        #         mod_val = mod_vals[2]
        #     else:
        #         mod_val = mod_vals[-1]
        #     new_phase = self.phase_mod(self.oscillator.init_phase, mod_val)
        #     self.oscillator.phase = new_phase

    def change_wave_shape(self, shape_index):
        self.oscillator.change_wave_shape(shape_index)

    def change_freq(self, factor):
        self.oscillator.freq = self.oscillator.init_freq * factor

    # @property
    # def freqScale(self):
    #     return self._freqScale
    #
    # @freqScale.setter
    # def freqScale(self, value):
    #     self._freqScale = value

    def trigger_release(self):
        tr = "trigger_release"
        for modulator in self.amp_mods:  # only amp_mods since ADSR will do amplitude only.
            if hasattr(modulator, tr):
                modulator.trigger_release()
        if hasattr(self.oscillator, tr):
            self.oscillator.trigger_release()

    @property
    def ended(self):
        e = "ended"
        ended = []
        for modulator in self.amp_mods:  # and self.phase_mods and self.freq_mods:
            if hasattr(modulator, e):
                ended.append(modulator.ended)
        if hasattr(self.oscillator, e):
            ended.append(self.oscillator.ended)
        return all(ended)

    def __next__(self):
        # mod_vals = np.array([next(modulator) for modulator in self.amp_mods])
        self._modulate()
        return next(self.oscillator)

    # renders an array of the next num_frames frames. to replace __next__ but vectorized.
    def rend(self, num_frames):
        return self.oscillator.sine_gen(num_frames)



class ADSREnvelope:
    def __init__(self, attack_duration=0.05, decay_duration=0.2, sustain_level=0.7, \
                 release_duration=0.3, sample_rate=44100):
        self.attack_duration = attack_duration
        self.decay_duration = decay_duration
        self.sustain_level = sustain_level
        self.release_duration = release_duration
        self._sample_rate = sample_rate
        # test
        self.val = 0
        self.ended = False
        self.stepper = self.get_ads_stepper()

    # gets the attack, decay, and sustain when the note is initially created
    def get_ads_stepper(self):
        steppers = []
        # if there is any attack, create an iterator
        if self.attack_duration > 0:
            steppers.append(itertools.count(start=0, \
                                            step=1 / (self.attack_duration * self._sample_rate)))
        # if the decay is not zero, create an iterator for it
        if self.decay_duration > 0:
            steppers.append(itertools.count(start=1, \
                                            step=-(1 - self.sustain_level) / (self.decay_duration * self._sample_rate)))

        while True:
            l = len(steppers)
            if l > 0:
                val = next(steppers[0])
                if l == 2 and val > 1:
                    steppers.pop(0)
                    val = next(steppers[0])
                elif l == 1 and val < self.sustain_level:
                    steppers.pop(0)
                    val = self.sustain_level
            else:
                val = self.sustain_level
            yield val

    # when trigger_release is called, it changes the stepper to the release stepper, which starts at the current val
    # and goes to zero.
    def get_r_stepper(self):
        val = 1
        if self.release_duration > 0:
            release_step = - self.val / (self.release_duration * self._sample_rate)
            stepper = itertools.count(self.val, step=release_step)
        else:
            val = -1
        while True:
            if val <= 0:
                self.ended = True
                val = 0
            else:
                val = next(stepper)
            yield val

    # def __iter__(self):
    #     self.val = 0
    #     self.ended = False
    #     self.stepper = self.get_ads_stepper()
    #     return self

    def __next__(self):
        self.val = next(self.stepper)
        return self.val

    def trigger_release(self):
        self.stepper = self.get_r_stepper()
