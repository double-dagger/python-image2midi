
import numpy
import logging
logger = logging.getLogger('processor')

import image2midi.config


class Processor(image2midi.config.Configurable):
    """
    """
    # Parent track object
    track = None

    config_vars = []

    def __init__(self, parent, *args, **kwargs):
        self.track = parent

    def step(self):
        raise NotImplementedError


class ImageProcessor(Processor):
    """
    """
    # Cursor to perform navigation through image.
    cursor = None

    # Custom processor image. Derived from and defaults to track.player.image
    image = None

    exponent = 1.0
    multiplier = 1.0
    config_vars = Processor.config_vars + ['exponent', 'multiplier']

    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.image = self.track.player.image
        if 'cursor' in kwargs.keys():
            self.cursor = kwargs.get('cursor')
        else:
            self.cursor = ReturningCursor(self, **kwargs)
        self.configure(kwargs)

    def param1(self, d_value):
        self.exponent = min(max(0.01, self.exponent + d_value * 0.01), 10.0)

    def param2(self, d_value):
        logger.debug('{0.__class__} param1 {1}'.format(self, d_value))

    def param3(self, d_value):
        logger.debug('{0.__class__} param1 {1}'.format(self, d_value))

    def param4(self, d_value):
        logger.debug('{0.__class__} param1 {1}'.format(self, d_value))

    def param5(self, d_value):
        self.multiplier = min(max(0.01, self.multiplier + d_value * 0.01), 10.0)

    def get_info(self):
        return ['e: {0:.2f}'.format(self.exponent), 'm: {0:.2f}'.format(self.multiplier), self.cursor.locked, self.cursor.hold_axis]

    def step(self):
        self.cursor.step()

    def draw_cursor(self):
        """ Basic draw_cursor with red rectangle.
        """
        self.track.player.image.draw_rect(self.cursor.position, self.cursor.size, color=(0, 0, 0), thickness=2)

    def get_value(self):
        """ Every processor must have get_value() implemented itself.
            Returning value should be normalized to 0..1
        """
        raise NotImplementedError


class Cursor(image2midi.config.Configurable):
    """
    """
    # Default cursor position in top left corner.
    position = [0, 0]

    # Default cursor size 16x16 pixels.
    size = [50, 50]

    # Default cursor step size
    step_size = [30, 30]

    # When cursor is locked it does not update from master cursor
    # in shared cursor mode. And does not restart.
    locked = False

    config_vars = ['position', 'size', 'step_size', 'locked']

    def __init__(self, parent, **kwargs):
        self.processor = parent
        self.configure(kwargs)

    def restart(self):
        if not self.locked:
            self.position = [0, 0]

    def switch_locked(self):
        self.locked = not self.locked

    def share_cursor(self):
        self.processor.track.player.share_cursor(self)

    def update_size(self, axis, diff):
        self.size[axis] = min(
            max(1, self.size[axis] + diff),
            self.processor.image.shape()[axis] - self.step_size[axis]
        )
        self.share_cursor()

    def update_size_x(self, diff):
        self.update_size(0, diff)

    def update_size_y(self, diff):
        self.update_size(1, diff)

    def update_step(self, axis, diff):
        self.step_size[axis] = min(
            max(1, self.step_size[axis] + diff),
            self.processor.image.shape()[axis] - self.size[axis]
        )
        self.share_cursor()

    def update_step_x(self, diff):
        self.update_step(0, diff)

    def update_step_y(self, diff):
        self.update_step(1, diff)

    def update_from_cursor(self, master_cursor):
        if not self.locked:
            self.configure(
                master_cursor.config2dict()
            )

    def step(self, vector=(1, 0)):
        """ Move cursor within the processor.image.
            vector = (1, 0) which means 1 step on X axis.
        """
        delta_step = numpy.multiply(vector, self.step_size)
        self.position = numpy.add(self.position, delta_step)
        pt2 = self.position + self.size
        if pt2[0] > self.processor.image.shape()[0]:
            # Cursor overlaps X axis
            self.position[0] = 0
            self.step((0, 1))
        if pt2[1] > self.processor.image.shape()[1]:
            # Cursor overlaps Y axis
            self.step((0, -1))


class ReturningCursor(Cursor):
    """
    """
    # Starting step move vector
    vector = (1, 0)

    # Flag to stop in currently running row/column
    hold_axis = False

    config_vars = Cursor.config_vars + ['hold_axis', 'vector',]

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.configure(kwargs)

    def switch_direction(self):
        self.vector = numpy.multiply(self.vector, -1)
        self.share_cursor()

    def switch_axis(self):
        self.vector = self.vector[::-1]
        self.share_cursor()

    def switch_hold_axis(self):
        self.hold_axis = not self.hold_axis

    def step(self, custom_delta=None):
        vector = self.vector
        if custom_delta is not None:
            vector = custom_delta
        delta_step = numpy.multiply(vector, self.step_size)
        next_position = numpy.add(self.position, delta_step)
        pt2 = next_position + self.size
        overlap = pt2 / self.processor.image.shape()

        if (overlap > 1).any():
            # If cursor is going to overlap boundaries invert vector and
            # do the real step
            self.vector = numpy.multiply(vector, -1)
            self.step()

        elif (next_position < 0).any():
            # If cursor is going to overlap boundaries to the negative side,
            # check for stop row.
            if self.hold_axis:
                # If stop row is enabled, stay on current row
                self.vector = numpy.multiply(vector, -1)
                self.step()
            else:
                # If not, make one step on the axis axis and proceed.
                self.vector = numpy.multiply(vector, -1)
                self.step(self.vector[::-1])

        else:
            self.position = next_position
