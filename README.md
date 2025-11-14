# guitar_dsp

Digital signal processing experiments for guitar effects, amp sims, and general tone-shaping.

**Purpose:**  
Build a minimal-latency, zero-nonsense guitar amp/effects setup without paying $200 every time I forget I already bought an amp sim two years ago.  
Also an excuse to mess around with DSP.

Works great on **macOS** thanks to CoreAudio.  
**Windows**: absolutely do not attempt.  
**Linux**: probably fine? Haven’t tried.

This is a true weekend project. Expect weirdness.

**Attribution:**  
This project uses the excellent [`sounddevice`](https://github.com/spatialaudio/python-sounddevice)
library, which provides real-time audio I/O for Python by wrapping the
cross-platform [PortAudio](https://github.com/PortAudio/portaudio) engine.

Without these two open-source projects, doing low-latency guitar DSP in Python
would basically be impossible. Huge thanks to their authors and maintainers.
