import sys
import numpy as np

class Visualizer:
    def __init__(self):
        self._bar_green = "\033[32m█\033[0m"
        self._bar_yellow = "\033[33m█\033[0m"
        self._bar_red= "\033[31m█\033[0m"
        self.BUFFER_SIZE = 4096   # get more samples for low notes
        self.audio_buffer = np.zeros(self.BUFFER_SIZE)
        self.buffer_index = 0
        self.print_counter = 0 

        self.NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F",
              "F#", "G", "G#", "A", "A#", "B"]

        self.TARGET_FREQS = {
            "E2": 82.4069,
            "A2": 110.0000,
            "D3": 146.8324,
            "G3": 195.9977,
            "B3": 246.9417,
            "E4": 329.6276
        }

    def freq_to_note(self, freq):
        if freq <= 0:
            return None, None

        note_number = 12 * np.log2(freq / 440.0) + 69
        note_index = int(round(note_number)) % 12
        octave = int(round(note_number)) // 12 - 1

        return self.NOTE_NAMES[note_index], octave

    def detect_pitch(self, x, samplerate):
        x = x - np.mean(x)  # remove DC offset

        corr = np.correlate(x, x, mode='full')
        corr = corr[len(corr)//2:]

        # Find first peak after lag 10
        d = np.diff(corr)
        start = np.where(d > 0)[0]
        if len(start) == 0:
            return 0
        start = start[0]

        peak = np.argmax(corr[start:]) + start
        if peak == 0:
            return 0

        freq = samplerate / peak
        return freq

    def process(self, input_block):
        # Update circular buffer
        for sample in input_block:
            self.audio_buffer[self.buffer_index] = sample
            self.buffer_index = (self.buffer_index + 1) % self.BUFFER_SIZE

        # Loudness measure
        rms = np.sqrt(np.mean(input_block**2))
            
        if self.print_counter % 150 == 0:
            # Convert to bar length (scale to 0–1 range)
            level = min(0.1 * rms * 40, 1.0)   # adjust multiplier to taste

            bar_length = 50
            filled = int(level * bar_length)
            empty = bar_length - filled
            
            if level < 0.66:
                colored = self._bar_green
            elif level < 0.88:
                colored = self._bar_yellow
            else:
                colored = self._bar_red

            bar = colored * filled + "░" * empty

            # Move cursor to start of line, print bar, flush immediately
            sys.stdout.write("\033[?25l") # hide cursor
            sys.stdout.write("\033[2J\033[H") # clear everything
            sys.stdout.write(bar + "\n")

            # Detect pitch
            chunk = np.copy(self.audio_buffer)
            freq = self.detect_pitch(chunk, 48000)
            note, octave = self.freq_to_note(freq)

            if freq > 20:  # ignore noise
                sys.stdout.write(f"Freq: {freq:7.2f} Hz | Note: {note}{octave if note else ''}         \n")
            else:
                sys.stdout.write("\rFreq: ---- | Note: --         \n")

            sys.stdout.write("\033[2A")
            sys.stdout.flush()

        self.print_counter += 1