import numpy as np
from threading import Lock

class Echo:
    def __init__(self, sample_rate, delay_ms=300, decay=0.5, mix=1.0):
        self.sample_rate = sample_rate
        self.delay_samples = int(delay_ms * sample_rate / 1000)
        self.ignore_count = self.delay_samples
        self.decay = decay      # how loud the echo is
        self.mix = mix          # wet level (0–1)
        self.buffer = np.zeros(int(1000 * sample_rate / 1000), dtype=np.float32) # 1000ms delay max
        self.idx = 0            # circular buffer index
        self.lock = Lock()

    def set_delay(self, val):
        with self.lock:
            self.idx = 0
            self.delay_samples = int(max(1, val)  * self.sample_rate / 1000)
            self.ignore_count = self.delay_samples

    def set_decay(self, val):
        with self.lock:
            self.decay = (val/100)

    def process(self, input_block):
        """
        input_block: 1D numpy array of audio samples (mono)
        returns: processed block (same length)
        """
        with self.lock:
            out = np.empty_like(input_block)

            for i, sample in enumerate(input_block):
                delayed = self.buffer[self.idx] if self.ignore_count == 0 else 0
                out[i] = sample + self.decay * delayed
                # write into circular buffer
                self.buffer[self.idx] = sample
                # increment circular index
                self.idx = (self.idx + 1) % self.delay_samples
                self.ignore_count = max(self.ignore_count - 1, 0)

            # apply wet/dry mix
            return (1 - self.mix) * input_block + self.mix * out
