
import numpy

import image2midi.processors


class Processor(image2midi.processors.ImageProcessor):
    """
    """
    # Color channel to get value from (0 - blue, 1 - green, 2 - red)
    color_channel = 0

    config_vars = image2midi.processors.ImageProcessor.config_vars
    config_vars.extend(['color_channel'])

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.configure(kwargs)

    def draw_cursor(self):
        """ Draw cursor in color based on which channel it represents.
        """
        color = [0, 0, 0]
        color[self.color_channel] = 255
        self.track.player.image.draw_rect(self.cursor.position, self.cursor.size, color=tuple(color), thickness=1)

    def get_value(self):
        subimage = self.image.get_subimage(self.cursor.position, self.cursor.size)[:,:,self.color_channel]
        value = numpy.average(subimage) / 255
        image2midi.processors.logger.debug('get_color: {0:.4f}'.format(value))
        return value
