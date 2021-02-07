
import numpy

import image2midi.processors


class Processor(image2midi.processors.ImageProcessor):
    """
    """
    def get_value(self):
        subimage = self.image.get_subimage_bw(self.cursor.position, self.cursor.size)
        value = numpy.average(subimage) / 255
        image2midi.processors.logger.debug('get_color: {0:.4f}'.format(value))
        return value
