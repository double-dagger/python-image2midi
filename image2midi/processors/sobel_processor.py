
import copy
import numpy
import cv2

import image2midi.processors


class Processor(image2midi.processors.ImageProcessor):
    """
    """
    k_size = 3
    scale = 1
    delta = 0

    config_vars = image2midi.processors.ImageProcessor.config_vars + ['k_size', 'scale', 'delta']

    processed_image = None

    def param4(self, d_value):
        self.k_size = min(max(1, self.k_size + d_value * 2), 31)
        self.process_image()

    def param3(self, d_value):
        self.scale = min(max(1, self.scale + d_value), 31)
        self.process_image()

    def param2(self, d_value):
        self.delta = min(max(0, self.delta + d_value), 31)
        self.process_image()

    def get_info(self):
        return ['Sobel',] + super().get_info() + [
            'd: {0}'.format(self.delta),
            's: {0}'.format(self.scale),
            'k: {0}'.format(self.k_size),
            None,
            '{0:.4f}'.format(self._value),
        ]

    def process_image(self):
        self.processed_image = copy.copy(self.image)
        # Apply blur and sobel edge detection for _im2
        blur = cv2.GaussianBlur(self.processed_image._im_original_bw, (5,5), 0)
        scale = 1
        delta = 0
        grad_x = cv2.Sobel(blur, cv2.CV_16S, 1, 0, ksize=self.k_size, scale=self.scale, delta=self.delta, borderType=cv2.BORDER_DEFAULT)
        grad_y = cv2.Sobel(blur, cv2.CV_16S, 0, 1, ksize=self.k_size, scale=self.scale, delta=self.delta, borderType=cv2.BORDER_DEFAULT)
        abs_grad_x = cv2.convertScaleAbs(grad_x)
        abs_grad_y = cv2.convertScaleAbs(grad_y)
        grad = cv2.addWeighted(abs_grad_x, 0.5, abs_grad_y, 0.5, 0)
        self.processed_image._im_original_bw = grad
        self.processed_image._im_original = cv2.cvtColor(grad, cv2.COLOR_GRAY2RGB)

    def draw_cursor(self):
        """ Draw cursor in color based on which channel it represents.
        """
        self.track.player.image.draw_sub_image(
            self.cursor.position,
            self.cursor.size,
            cv2.cvtColor(self.processed_image.get_subimage_bw(self.cursor.position, self.cursor.size), cv2.COLOR_GRAY2RGB)
        )

    def get_value(self):
        if not self.processed_image:
            self.process_image()
        subimage = self.processed_image.get_subimage_bw(self.cursor.position, self.cursor.size)
        self._value = min( 1.0, ( ( numpy.average(subimage) / 255 ) ** self.exponent ) * self.multiplier )
        image2midi.processors.logger.debug('get_color: {0:.4f}'.format(self._value))
        return self._value
