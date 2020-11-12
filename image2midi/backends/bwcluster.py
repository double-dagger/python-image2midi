
import copy
import logging
logger = logging.getLogger('backends.bwcluster')

import cv2
import numpy as np

import image2midi.backends.common


class Cluster(image2midi.backends.common.Cluster):
    def __init__(self, parent, cluster, cluster2):
        super().__init__(parent)
        self.__cluster = cluster
        self.__cluster2 = cluster2
        self.color = int(np.average(self.__cluster.flat))
        self.edges = int(np.average(self.__cluster2.flat))
        logger.debug('color: {0.color}, edges: {0.edges}'.format(self))

    def play(self):
        super().play()
        self.play_value(channel=0, value=self.color)
        self.play_value(channel=1, value=self.edges)


class Image(image2midi.backends.common.ClusterImage):
    cluster_class = Cluster

    def __init__(self, parent, image_path):
        self.track = parent
        self._im = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        self.init_image()
        self._im2 = copy.copy(self._im)
        self._im2 = cv2.blur(self._im2, (5,5))
        self._im2 = cv2.Canny(self._im2,10,100)

    def show_image(self, wait_interval=1, rect_color=0):
        im = copy.copy(self._im)
        im[
            self._y:self._y2(), self._x:self._x2()
        ]=self._im2[
            self._y:self._y2(), self._x:self._x2()
        ]
        ##resized_im = self.resize_im(im)
#        cv2.namedWindow('Image', cv2.WND_PROP_FULLSCREEN)
#        cv2.setWindowProperty(
#            'Image', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN
#        )
        cv2.imshow('Image', im)
        cv2.waitKey(wait_interval)

    def get_cluster(self):
        return self.cluster_class(
            self,
            self._im[self._y:self._y2(), self._x:self._x2()],
            self._im2[self._y:self._y2(), self._x:self._x2()],
        )
