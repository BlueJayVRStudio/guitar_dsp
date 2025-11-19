import sys
import sounddevice as sd
import numpy as np
import time
from effects.echo import Echo

# USE THIS TO FIND YOUR INPUT AND OUTPUT DEVICES
# for i, dev in enumerate(sd.query_devices()):
#     print(i, dev['name'], dev['max_input_channels'], dev['max_output_channels'])
# quit()

INPUT_DEVICE  = 1   # put your input device index here
OUTPUT_DEVICE = 2   # put your output device index here
gain = 1000.0       # pre-distortion gain
mix  = 1.0        # how much distorted vs clean
print_counter = 0 

NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F",
              "F#", "G", "G#", "A", "A#", "B"]

TARGET_FREQS = {
    "E2": 82.4069,
    "A2": 110.0000,
    "D3": 146.8324,
    "G3": 195.9977,
    "B3": 246.9417,
    "E4": 329.6276
}

BUFFER_SIZE = 4096   # get more samples for low notes
audio_buffer = np.zeros(BUFFER_SIZE)
buffer_index = 0

BLOCKSIZE = 32
SAMPLERATE = 48000
VOLUME = 0.2

def freq_to_note(freq):
    if freq <= 0:
        return None, None

    note_number = 12 * np.log2(freq / 440.0) + 69
    note_index = int(round(note_number)) % 12
    octave = int(round(note_number)) // 12 - 1

    return NOTE_NAMES[note_index], octave

def detect_pitch(x, samplerate):
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

echo = Echo(SAMPLERATE, delay_ms=250, decay=0.45, mix=0.7)
_bar_green = "\033[32m█\033[0m"
_bar_yellow = "\033[33m█\033[0m"
_bar_red= "\033[31m█\033[0m"

def cb(indata, outdata, frames, time, status):
    global print_counter
    global buffer_index
    global lp_state, hp_prev_x, hp_prev_y

    if status:
        print(status)

    x = indata[:, 0]

    # Update circular buffer
    for sample in x:
        audio_buffer[buffer_index] = sample
        buffer_index = (buffer_index + 1) % BUFFER_SIZE

    # Loudness measure
    rms = np.sqrt(np.mean(x**2))
        
    if print_counter % 150 == 0:
        # Convert to bar length (scale to 0–1 range)
        level = min(0.1 * rms * 40, 1.0)   # adjust multiplier to taste

        bar_length = 50
        filled = int(level * bar_length)
        empty = bar_length - filled
        
        if level < 0.66:
            colored = _bar_green
        elif level < 0.88:
            colored = _bar_yellow
        else:
            colored = _bar_red

        bar = colored * filled + "░" * empty

        # Move cursor to start of line, print bar, flush immediately
        sys.stdout.write("\033[?25l") # hide cursor
        sys.stdout.write("\033[2J\033[H") # clear everything
        sys.stdout.write(bar + "\n")

        # Detect pitch
        chunk = np.copy(audio_buffer)
        freq = detect_pitch(chunk, 48000)
        note, octave = freq_to_note(freq)

        if freq > 20:  # ignore noise
            sys.stdout.write(f"Freq: {freq:7.2f} Hz | Note: {note}{octave if note else ''}         \n")
        else:
            sys.stdout.write("\rFreq: ---- | Note: --         \n")

        sys.stdout.write("\033[2A")
        sys.stdout.flush()

    print_counter += 1

    # DISTORTION
    x = x * gain
    distorted = np.tanh(x)
    y = mix * distorted + (1 - mix) * indata[:, 0]
    
    y = echo.process(y)

    outdata[:, 0] = y * VOLUME

with sd.Stream(
    device=(INPUT_DEVICE, OUTPUT_DEVICE),
    channels=1,
    samplerate=SAMPLERATE,
    blocksize=BLOCKSIZE,
    dtype='float32',
    latency='low',
    callback=cb,
):
    print("Guitar with distortion — Ctrl+C to stop")
    while True:
        time.sleep(0.1)
