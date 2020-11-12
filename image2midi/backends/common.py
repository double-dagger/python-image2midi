
import copy
import logging
logger = logging.getLogger('backends.common')

import twisted.internet.reactor
import cv2

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
            self._im, (1024,681),
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

    def show_image(self, wait_interval=1):
        pixel = list(self._im[self._y, self._x])
        self._im[self._y, self._x] = [0, 0, 255]
        resized_im = self.resize_im(self._im)
        cv2.imshow('Image', resized_im)
        self._im[self._y, self._x] = pixel
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
        return min(int(value/self._note_div)*self._note_mult + 24, 127)

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

    def show_image(self, wait_interval=1, rect_color=0):
        im = copy.copy(self._im)
        im = cv2.rectangle(
            im,
            (self._x, self._y),
            (self._x2(), self._y2()),
            rect_color*0.8,
            2,
        )
        ##resized_im = self.resize_im(im)
        cv2.imshow('Image', im)
        cv2.waitKey(wait_interval)

    def get_cluster(self):
        return self.cluster_class(
            self,
            self._im[self._y:self._y2(), self._x:self._x2()],
        )

    def next_cluster(self):
        cluster = self.get_cluster()
        cluster.play()
        self.show_image(rect_color=cluster.color)

        # proceed in image
        self._x, self._y = self.step(steps_x=1)
