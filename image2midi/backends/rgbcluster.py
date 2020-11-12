
import logging
logger = logging.getLogger('backends.rgbcluster')

import cv2

import image2midi.backends.common


class Cluster(image2midi.backends.common.Cluster):
    def __init__(self, parent, cluster):
        super().__init__(parent)
        self.__cluster = cluster
        self.color = self.__cluster.mean(axis=0).mean(axis=0)
        logger.debug('color: {0.color}'.format(self))

    def play(self):
        """ Play cluster value to channels
            1 - RED
            2 - GREEN
            3 - BLUE
        """
        super().play()
        self.play_value(channel=0, value=self.color[2])
        self.play_value(channel=1, value=self.color[1])
        self.play_value(channel=2, value=self.color[0])


class Image(image2midi.backends.common.ClusterImage):
    cluster_class = Cluster
    def __init__(self, parent, image_path):
        self.track = parent
        self._im = cv2.imread(image_path, cv2.IMREAD_COLOR)
        self.init_image()
