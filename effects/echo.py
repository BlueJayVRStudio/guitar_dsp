import numpy as np

class Echo:
    def __init__(self, sample_rate, delay_ms=300, decay=0.5, mix=1.0):
        self.sample_rate = sample_rate
        self.delay_samples = int(delay_ms * sample_rate / 1000)
        self.decay = decay      # how loud the echo is
        self.mix = mix          # wet level (0–1)
        self.buffer = np.zeros(self.delay_samples, dtype=np.float32)
        self.idx = 0            # circular buffer index

    def process(self, input_block):
        """
        input_block: 1D numpy array of audio samples (mono)
        returns: processed block (same length)
        """
        out = np.empty_like(input_block)

        for i, sample in enumerate(input_block):
            delayed = self.buffer[self.idx]
            out[i] = sample + self.decay * delayed
            # write into circular buffer
            self.buffer[self.idx] = sample
            # increment circular index
            self.idx = (self.idx + 1) % self.delay_samples

        # apply wet/dry mix
        return (1 - self.mix) * input_block + self.mix * out
