
import copy
import logging
logger = logging.getLogger('backends.bwcluster')

import cv2
import numpy as np

import image2midi.backends.common


class Cluster(image2midi.backends.common.SequenceCluster):
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
        self.player = parent
        self._im = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        self.init_image()

        # Apply blur and sobel edge detection for _im2
        blur = cv2.GaussianBlur(self._im, (5,5), 0)
        scale = 1
        delta = 0
        grad_x = cv2.Sobel(blur, cv2.CV_16S, 1, 0, ksize=3, scale=scale, delta=delta, borderType=cv2.BORDER_DEFAULT)
        grad_y = cv2.Sobel(blur, cv2.CV_16S, 0, 1, ksize=3, scale=scale, delta=delta, borderType=cv2.BORDER_DEFAULT)
        abs_grad_x = cv2.convertScaleAbs(grad_x)
        abs_grad_y = cv2.convertScaleAbs(grad_y)
        grad = cv2.addWeighted(abs_grad_x, 0.5, abs_grad_y, 0.5, 0)
        self._im2 = grad

    def get_cluster(self):
        return self.cluster_class(
            self,
            self._im[self._y:self._y2(), self._x:self._x2()],
            self._im2[self._y:self._y2(), self._x:self._x2()],
        )
