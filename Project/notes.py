# the dictionary with the note to be played (str) being the key and the frequency being the value
key_frequencies = {'z': 130.8127826502993,
                   's': 138.59131548843604,
                   'x': 146.8323839587038,
                   'd': 155.56349186104046,
                   'c': 164.813778456435,
                   'v': 174.61411571650197,
                   'g': 184.99721135581723,
                   'b': 195.9977179908747,
                   'h': 207.65234878997262,
                   'n': 220.00000000000006,
                   'j': 233.08188075904502,
                   'm': 246.94165062806212,
                   'q': 261.62556530059874, ',': 261.62556530059874, '<': 261.62556530059874,
                   '2': 277.1826309768722, 'l': 277.1826309768722,
                   '@': 277.1826309768722, # have to modify to include special characters if shift is held
                   'w': 293.6647679174077, '.': 293.6647679174077, '>': 293.6647679174077,
                   '3': 311.12698372208104,
                   '#': 311.12698372208104,
                   'e': 329.6275569128701,
                   'r': 349.22823143300405,
                   '5': 369.99442271163457, '%': 369.99442271163457,
                   't': 391.9954359817495,
                   '6': 415.30469757994535, '^': 415.30469757994535,
                   'y': 440.0000000000002,
                   '7': 466.16376151809015, '&': 466.16376151809015,
                   'u': 493.8833012561244,
                   'i': 523.2511306011976,
                   '9': 554.3652619537446, '(': 554.3652619537446,
                   'o': 587.3295358348156,
                   '0': 622.2539674441624, ')': 622.2539674441624,
                   'p': 659.2551138257405,
                   '[': 698.4564628660085, '{': 698.4564628660085
                   }

# below is the code to generate the above table.

# notes = [
#     # lower bottom of keyboard, from C3 (z) to B3 (m)
#     'z', 's', 'x', 'd', 'c', 'v', 'g', 'b', 'h', 'n', 'j', 'm',
#     # upper half of keyboard, from C4 (q) to F5 (the '[' key)
#     'q', '2', 'w', '3', 'e', 'r', '5', 't', '6', 'y', '7', 'u', 'i', '9', 'o', '0', 'p', '['
# ]
#
# A4 = 440.0 # Hz. It is what the rest of the frequencies are based off of.
#
# # multiply this by your base note to go up number_of_notes semitones.
# def factor(number_of_notes = 1):
#     return pow(2, number_of_notes/12)
#
# multiple = factor(1)
# # goes down 2 octaves, then up 3 notes.
# # this is the frequency that the keyboard will start at (z).
# C3 = (A4/4.0) * factor(3)
#
# # generates the dictionary
# current_frequency = C3
# for note in notes:
#     key_frequencies[note] = current_frequency
#     current_frequency *= multiple

