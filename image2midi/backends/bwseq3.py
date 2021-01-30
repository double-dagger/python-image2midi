
import copy
import logging
logger = logging.getLogger('backends.bwcluster')

import cv2
import numpy as np

import image2midi.backends.bwseq1


xx = None
class Cluster(image2midi.backends.bwseq1.Cluster):
    sequence_candidates = [
        [xx, 0, xx, xx],
        [xx, 6, xx, xx],
        [xx, 12, xx, xx],
        [xx, 18, xx, xx],
        [xx, 24, xx, xx],
        [xx, 24, xx, 12],
        [xx, 24, xx, 24],
        [xx, 24, 12, 24],
        [xx, 24, 12, 24],
        [12, 24, 12, 24],
        [12, 24, 12, 12],
        [12, 12, 12, 12],
        [12, 12, xx, 12],
        [24, 24, xx, 24],
        [xx, 24, xx, 24],
        [xx, xx, xx, 24],
    ]


class Image(image2midi.backends.bwseq1.Image):
    cluster_class = Cluster
