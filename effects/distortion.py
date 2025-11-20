import sys
import numpy as np

class Distortion:
    def __init__(self):
        self.gain = 1000.0  # pre-distortion gain
        self.mix  = 1.0     # how much distorted vs clean

    def process(self, input_block):
        distorted = np.tanh(input_block * self.gain)
        return self.mix * distorted + (1 - self.mix) * input_block