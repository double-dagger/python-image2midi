
import copy
import numpy
import cv2


SIZE_IMAGE = (900, 600)
SIZE_DISPLAY = (1024, 600)
BORDER_ADD = (
    int((SIZE_DISPLAY[0] - SIZE_IMAGE[0]) / 2),
    int((SIZE_DISPLAY[1] - SIZE_IMAGE[1]) / 2)
)

class Image(object):
    # Parent Player object
    player = None

    _im_original = None
    _im_original_bw = None
    _im_display = None

    def __init__(self, parent, image_path):
        self.player = parent
        self.load_image(image_path)

    def reset_display(self):
        self._im_display = self._im_original

    def load_image(self, image_path):
        self._im_original = cv2.imread(image_path, cv2.IMREAD_COLOR)
        self._im_original = cv2.resize(
            self._im_original, SIZE_IMAGE,
            interpolation=cv2.INTER_NEAREST
        )
        self._im_original_bw = cv2.cvtColor(self._im_original, cv2.COLOR_BGR2GRAY)
        self._im_display = self._im_original

    def shape(self):
        return self._im_original.shape[:2][::-1]

    def draw_rect(self, position, size, color=(0, 0, 255), thickness=-1):
        self._im_display = cv2.rectangle(
            self._im_original.copy(),
            tuple(position),
            tuple(numpy.add(position, size)),
            color,
            thickness,
        )

    def __get_sub_image(self, im, position, size):
        return im[
            position[1]:position[1]+size[1],
            position[0]:position[0]+size[0]
        ]

    def get_subimage(self, position, size):
        return self.__get_sub_image(self._im_original, position, size)

    def get_subimage_bw(self, position, size):
        return self.__get_sub_image(self._im_original_bw, position, size)

    def show_image(self, wait_interval=1, fullscreen=False):
        im = cv2.copyMakeBorder(
            self._im_display,
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
