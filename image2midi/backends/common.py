
import copy
import logging
logger = logging.getLogger('backends.common')

import twisted.internet.reactor
import cv2

SIZE_IMAGE = (900, 600)
SIZE_DISPLAY = (1024, 600)
BORDER_ADD = (
	int((SIZE_DISPLAY[0] - SIZE_IMAGE[0]) / 2),
    int((SIZE_DISPLAY[1] - SIZE_IMAGE[1]) / 2)
)

class Cluster(object):
    channels = []

    def __init__(self, parent):
        self.image = parent

    def play(self):
        channel = self.image.track.channels[9]
        note = 36
        channel.add_note(note)
        twisted.internet.reactor.callLater(
            self.image.track.step_length / 2,
            channel.stop_note,
            note
        )

    def play_value(self, channel, value):
        self.play_note(
            self.image.value_to_note(value),
            channel,
        )

    def play_note(self, note, channel):
        if note is not None:
            logger.debug('{0}: {1}'.format(channel, note))
        channel = self.image.track.channels[channel]
        if ( not channel.check_note(note) ) and note is not None:
            twisted.internet.reactor.callLater(
                self.image.track.step_length / 2,
                channel.play_note,
                note
            )


class Image(object):
    _im = None
    _x = 0
    _y = 0
    _step_x = 1
    _step_y = 1
    _view_resize = 1
    _returning = False
    __going_back = False

    def __init__(self, parent, image_path):
        self.track = parent
        self._im = cv2.imread(image_path, cv2.IMREAD_COLOR)
        self.init_image()

    def restart(self):
        self._x = 0
        self._y = 0

    def value_to_note(self, value):
        if value > 192:
            return None
        if value < 32:
            return None
        return int(value/16)*3 + 36

    def init_image(self):
        self._im = cv2.resize(
            self._im, SIZE_IMAGE,
            interpolation=cv2.INTER_NEAREST
        )
        self._im_height = self._im.shape[0]
        self._im_width = self._im.shape[1]

    def next_cluster(self):
        raise NotImplementedError

    def resize_im(self, im):
        if self._view_resize != 1:
            resized_im = cv2.resize(
                im, (0, 0), fx=self._view_resize, fy=self._view_resize,
                interpolation=cv2.INTER_NEAREST
            )
        else:
            resized_im = self._im
        return resized_im

    def show_image(self, wait_interval=1, rect_color=0, fullscreen=False):
        im = copy.copy(self._im)

        # If Image has attribute _im2 show current cluster from _im2
        if hasattr(self, '_im2'):
            im[
                self._y:self._y2(), self._x:self._x2()
            ]=self._im2[
                self._y:self._y2(), self._x:self._x2()
            ]
        # Else make border around current cluster with given rect_color
        else:
            im = cv2.rectangle(
                im,
                (self._x, self._y),
                (self._x2(), self._y2()),
                rect_color*0.8,
                2,
            )

        im = cv2.copyMakeBorder(
            im,
            top=BORDER_ADD[1],
            bottom=BORDER_ADD[1],
            left=BORDER_ADD[0],
            right=BORDER_ADD[0],
            borderType=cv2.BORDER_CONSTANT,
            value=0
        )

        if fullscreen:
            cv2.namedWindow('Image', cv2.WND_PROP_FULLSCREEN)
            cv2.setWindowProperty(
                'Image', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN
            )

        cv2.imshow('Image', im)
        cv2.waitKey(wait_interval)

    def step(self, steps_x=None, steps_y=None):
        if steps_x is not None:
            if self.__going_back:
                x = self._x - self._step_x * steps_x
            else:
                x = self._x + self._step_x * steps_x
            if x + self._step_x > self._im_width:
                if self._returning:
                    self.__going_back = True
                    return self.step(steps_x, steps_y)
                else:
                    x = 0
                    steps_y = (steps_y or 0) + 1
            elif self.__going_back and x < 0:
                self.__going_back = False
                x = 0
                steps_y = (steps_y or 0) + 1
        else:
            x = self._x
        if steps_y is not None:
            y = self._y + self._step_y * steps_y
            if y + self._step_y > self._im_height:
                y = self._y
        else:
            y = self._y
        return x, y


class ClusterImage(Image):
    _step_x = 16
    _step_y = 16
    _cluster_size_x = 16
    _cluster_size_y = 16
    _note_threshold_min = 32
    _note_threshold_max = 192
    _note_div = 16
    _note_mult = 3

    def _x2(self):
        return self._x+self._cluster_size_x

    def _y2(self):
        return self._y+self._cluster_size_y

    def value_to_note(self, value):
        if value > self._note_threshold_max:
            return None
        if value < self._note_threshold_min:
            return None
        return min(int(value/self._note_div)*self._note_mult, 127)

    def midi_cc(self, cc):
        if cc.control == 28:
            self._step_x = cc.value
        if cc.control == 29:
            self._step_y = cc.value
        if cc.control == 30:
            self._cluster_size_x = cc.value
        if cc.control == 31:
            self._cluster_size_y = cc.value
        if cc.control == 3:
            self._note_threshold_min = cc.value * 2
        if cc.control == 9:
            self._note_threshold_max = cc.value * 2
        if cc.control == 14:
            self._note_div = max(cc.value, 1)
        if cc.control == 15:
            self._note_mult = cc.value
        if cc.control == 116:
            self._returning = cc.value == 127

    def cluster_area(self, im):
        return im[
            self._y:self._y+self._cluster_size_y,
            self._x:self._x+self._cluster_size_x
        ]

    def get_cluster(self):
        return self.cluster_class(
            self,
            self._im[self._y:self._y2(), self._x:self._x2()],
        )

    def next_cluster(self):
        cluster = self.get_cluster()
        cluster.play()

        rect_color = 0
        if hasattr(cluster, 'color'):
            rect_color = cluster.color
        self.show_image(rect_color=rect_color)

        # proceed in image
        self._x, self._y = self.step(steps_x=1)


xx = None
class SequenceCluster(Cluster):
    sequences = [None, None]

    sequence_candidates = [
        [xx, 12, xx, xx, xx, xx, xx, xx, xx],
        [xx, 14, xx, xx, xx, xx, xx, xx, xx],
        [xx, 16, xx, xx, xx, xx, xx, xx, xx],
        [xx, 16, xx, xx, xx, xx, 16, xx, xx],
        [xx, 16, 16, xx, 16, xx, 16, xx, xx],
        [xx, 16, 16, xx, 16, xx, 16, 16, xx],
        [xx, 18, 18, xx, 18, xx, 18, 18, xx],
        [xx, 20, 20, xx, 20, xx, 20, 20, xx],
        [xx, xx, 20, xx, xx, xx, 20, 20, xx],
        [xx, xx, xx, xx, xx, xx, 22, 22, xx],
        [xx, xx, xx, xx, xx, xx, 24, 24, xx],
        [xx, xx, xx, xx, xx, xx, 24, xx, xx],
    ]

    def __init__(self, parent):
        super().__init__(parent)
        self.steps = len(self.sequence_candidates[0])
        ## self.value_divider = int(255 / len(self.sequence_candidates)) + 1
        self.step_length = self.image.track.step_length / self.steps

    def play(self):
        """
        """
        super().play()

    def value_to_sequence_id(self, value):
        """ Convert value ( 0-255 ) to index of selected sequence from
            self.sequence_candidates.
            Interval can be specified _note_threshold_min, _note_threshold_max
            pick from inside

        """
        if value > self.image._note_threshold_max:
            return None
        if value < self.image._note_threshold_min:
            return None
        scale = self.image._note_threshold_max - self.image._note_threshold_min
        value = value - self.image._note_threshold_min
        div = int(scale / len(self.sequence_candidates)) + 1
        return int(value / div)

    def play_value(self, channel, value):
        value = self.value_to_sequence_id(value)
        if value is None:
            self.sequences[channel] = [None,] * self.steps
        else:
            self.sequences[channel] = self.sequence_candidates[value]
        logger.debug('seq: {0}'.format(self.sequences[channel]))
        if channel == 1:
            twisted.internet.reactor.callLater(
                self.step_length / 8,
                self.play_step,
                0, channel,
            )
        else:
            self.play_step(0, channel)

    def play_step(self, i, channel):
        """
        """
        ch = self.image.track.channels[channel]
        note = self.sequences[channel][i]
        if note is not None:
            ch.add_note(note)
            twisted.internet.reactor.callLater(
                self.step_length / 2,
                ch.stop_note,
                note
            )
        i += 1
        if i < len(self.sequences[channel]):
            twisted.internet.reactor.callLater(
                self.step_length,
                self.play_step,
                i, channel,
            )
