import sounddevice as sd
from effects.echo import Echo
from effects.distortion import Distortion
from console_visualization.volume_and_pitch import Visualizer
import customtkinter
from TkDial.tkdial.tkdial import Dial
from threading import Lock

volume_lock = Lock()
echo_lock = Lock()
echo_decay_lock = Lock()
echo_mix_lock = Lock()

input_devices = {}
output_devices = {}

for dev in sd.query_devices():
    # print(dev['index'], dev['name'], dev['max_input_channels'], dev['max_output_channels'])
    is_input = dev['max_input_channels'] > 0
    if is_input:
        input_devices[dev['name']] = dev['index']
    else:
        output_devices[dev['name']] = dev['index']

INPUT_DEVICE, OUTPUT_DEVICE = sd.default.device

BLOCKSIZE = 32
SAMPLERATE = 48000
VOLUME = 0.2

echo = Echo(SAMPLERATE, delay_ms=250, decay=0.45, mix=0.7)
distortion = Distortion()
console_visualizer = Visualizer()

def cb(indata, outdata, frames, time, status):
    if status:
        print(status)
    # INPUT
    input_block = indata[:, 0]
    # VISUALIZE
    console_visualizer.process(input_block)
    # DISTORTION
    x = distortion.process(input_block)
    # ECHO
    x = echo.process(x)
    # OUTPUT
    with volume_lock:
        outdata[:, 0] = x * VOLUME

def on_volume_change(val):
    global VOLUME
    with volume_lock:
        VOLUME = val / 100

def on_echo_change(val):
    echo.set_delay(val)

def on_echo_decay_change(val):
    echo.set_decay(val)

customtkinter.set_appearance_mode("Dark") 

app = customtkinter.CTk()
app_w = 650
app_h = 400
screen_w = app.winfo_screenwidth()
screen_h = app.winfo_screenheight()
app.geometry(f"{app_w}x{app_h}+{screen_w//2 - app_w//2}+{screen_h//2 - app_h//2}")
# app.geometry(f"450+100")
app.title("Guitar DSP")

app.grid_columnconfigure(0, weight=1)
app.grid_columnconfigure(1, weight=0)
app.grid_rowconfigure(0, weight=1)

frame_1 = customtkinter.CTkFrame(master=app)
frame_1.grid(row=0, column=0, rowspan=2, columnspan=1, padx=20, pady=20, sticky='nsew')

frame_2 = customtkinter.CTkFrame(master=app)
frame_2.grid(row=0, column=1, rowspan=1, columnspan=1, padx=20, pady=20, sticky='nsew')

dial1 = Dial(master=frame_1, start=0, end=100, scroll_steps=1, color_gradient=("green", "cyan"),
             text_color="white", text="Volume: ", unit_length=10, radius=50, command=on_volume_change)
dial1.grid(padx=20, pady=20)
dial1.set(20)

dial2 = Dial(master=frame_1, start=0, end=1000, scroll_steps=10, color_gradient=("yellow", "white"),
             text_color="white", text="Echo: ", unit_length=10, radius=50, command=on_echo_change)
dial2.grid(padx=20, pady=20)
dial2.set(250)

dial4 = Dial(master=frame_1, color_gradient=("white", "pink"),
             text_color="white", text="Decay: ", unit_length=10, radius=50, command=on_echo_decay_change)
dial4.grid(row=1, column=1, padx=20, pady=20)
dial4.set(75)

initialized = False

def on_output_select(choice):
    if not initialized:
        return
    global _stream
    global INPUT_DEVICE
    global OUTPUT_DEVICE

    OUTPUT_DEVICE = output_devices[choice]

    _stream.stop()
    _stream.close()

    _stream = sd.Stream(
        device=(INPUT_DEVICE, OUTPUT_DEVICE),
        channels=1,
        samplerate=SAMPLERATE,
        blocksize=BLOCKSIZE,
        dtype='float32',
        latency='low',
        callback=cb,
    )
    _stream.start()

def on_input_select(choice):
    if not initialized:
        return
    global _stream
    global INPUT_DEVICE
    global OUTPUT_DEVICE

    INPUT_DEVICE = input_devices[choice]

    _stream.stop()
    _stream.close()

    _stream = sd.Stream(
        device=(INPUT_DEVICE, OUTPUT_DEVICE),
        channels=1,
        samplerate=SAMPLERATE,
        blocksize=BLOCKSIZE,
        dtype='float32',
        latency='low',
        callback=cb,
    )
    _stream.start()

input_menu_label = customtkinter.CTkLabel(frame_2, text="input device: ", font=customtkinter.CTkFont())
input_menu_label.grid(padx=20, pady=1)

input_dropdown = customtkinter.CTkOptionMenu(
    master=frame_2,
    width=200,
    values=list(input_devices.keys()),
    command=on_input_select,
    dynamic_resizing=False,
)
input_dropdown.grid(padx=20, pady=20)
input_dropdown.set(sd.query_devices(INPUT_DEVICE)['name'])

output_menu_label = customtkinter.CTkLabel(frame_2, text="output device: ", font=customtkinter.CTkFont())
output_menu_label.grid(padx=20, pady=1)
output_dropdown = customtkinter.CTkOptionMenu(
    master=frame_2,
    width=200,
    values=list(output_devices.keys()),
    command=on_output_select,
    dynamic_resizing=False,
)
output_dropdown.grid(padx=20, pady=20)
output_dropdown.set(sd.query_devices(OUTPUT_DEVICE)['name'])
initialized = True

_stream = sd.Stream(
    device=(INPUT_DEVICE, OUTPUT_DEVICE),
    channels=1,
    samplerate=SAMPLERATE,
    blocksize=BLOCKSIZE,
    dtype='float32',
    latency='low',
    callback=cb,
)
_stream.start()
app.mainloop()
_stream.stop()
_stream.close()

print("\033[?25h\033[0m") # unhide cursor
print("\033[2J\033[H") # clear everything
