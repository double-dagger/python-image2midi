
import logging
logger = logging.getLogger('producer')

import image2midi.config

class Producer(image2midi.config.Configurable):
    """
    """
    # Parent track object
    track = None

    config_vars = []

    def __init__(self, parent, **kwargs):
        self.track = parent

    def set_value(self, value):
        self.value = value

    def play(self):
        raise NotImplementedError
