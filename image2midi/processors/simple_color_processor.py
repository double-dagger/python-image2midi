
import numpy

import image2midi.processors


class Processor(image2midi.processors.ImageProcessor):
    """
    """
    # Color channel to get value from (0 - blue, 1 - green, 2 - red)
    color_channel = 0

    config_vars = image2midi.processors.ImageProcessor.config_vars + ['color_channel',]

    def param4(self, d_value):
        self.color_channel = ( self.color_channel + d_value ) % 3

    def get_info(self):
        return ['sColor',] + super().get_info() + [None, '{0:.4f}'.format(self._value),]

    def draw_cursor(self):
        """ Draw cursor in color based on which channel it represents.
        """
        color = [0, 0, 0]
        color[self.color_channel] = 255
        self.track.player.image.draw_rect(self.cursor.position, self.cursor.size, color=tuple(color), thickness=2)

    def get_value(self):
        subimage = self.image.get_subimage(self.cursor.position, self.cursor.size)[:,:,self.color_channel]
        self._value = min( 1.0, ( ( numpy.average(subimage) / 255 ) ** self.exponent ) * self.multiplier )
        image2midi.processors.logger.debug('get_color: {0:.4f}'.format(self._value))
        return self._value
