import os
import tempfile
import random
import time
import sys

class TempDir(tempfile.TemporaryDirectory):
    def __call__(self):
        name = os.path.join(self.name, 'F'+os.urandom(16).hex())
        while os.path.isfile(name):
            name = os.path.join(self.name, 'F'+os.urandom(16).hex())
        # open(name, 'w').close()
        return name

    def __del__(self):
        self.cleanup()


def random_bytestring(size):
    return os.urandom(size)

def random_asciistring(size):
    return ''.join(chr(random.randint(0,127)) for _ in range(size))

def random_text(size):
    return os.urandom(size//2).hex()
