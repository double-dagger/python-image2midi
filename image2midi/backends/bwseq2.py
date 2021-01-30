
import copy
import logging
logger = logging.getLogger('backends.bwcluster')

import cv2
import numpy as np

import image2midi.backends.bwseq1


xx = None
class Cluster(image2midi.backends.bwseq1.Cluster):
    sequence_candidates = [
        [xx, 12, xx, xx, xx, xx, xx, xx, xx],
        [xx, 12, xx, 12, xx, xx, xx, xx, xx],
        [xx, 12, xx, 12, xx, 12, xx, xx, xx],
        [xx, 12, xx, 12, xx, 12, xx, 12, xx],
        [xx, 12, xx, 12, xx, 12, 12, 12, xx],
        [xx, 12, xx, 12, xx, 12, 12, 12, 12],
        [xx, 12, xx, 12, xx, 12, xx, 12, 12],
        [xx, 12, xx, xx, xx, 12, xx, 12, 12],
        [xx, xx, xx, xx, xx, 12, xx, 12, 12],
        [xx, xx, xx, xx, xx, xx, xx, 12, 12],
        [xx, xx, xx, xx, xx, xx, xx, xx, 12],
        [xx, xx, xx, xx, xx, xx, xx, xx, 12],
    ]


class Image(image2midi.backends.bwseq1.Image):
    cluster_class = Cluster
