
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

    def param1(self, d_value):
        logger.debug('{0.__class__} param1 {1}'.format(self, d_value))

    def param2(self, d_value):
        logger.debug('{0.__class__} param2 {1}'.format(self, d_value))

    def param3(self, d_value):
        logger.debug('{0.__class__} param3 {1}'.format(self, d_value))

    def param4(self, d_value):
        logger.debug('{0.__class__} param4 {1}'.format(self, d_value))

    def set_value(self, value):
        self.value = value

    def play(self):
        raise NotImplementedError
