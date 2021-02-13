
import numpy

import image2midi.processors


class Processor(image2midi.processors.ImageProcessor):
    """
    """
    def get_info(self):
        return ['sBright',] + super().get_info() + [None, '{0:.4f}'.format(self._value),]

    def get_value(self):
        subimage = self.image.get_subimage_bw(self.cursor.position, self.cursor.size)
        self._value = min( 1.0, ( ( numpy.average(subimage) / 255 ) ** self.exponent ) * self.multiplier )
        image2midi.processors.logger.debug('get_color: {0:.4f}'.format(self._value))
        return self._value
