
import copy
import numpy
import cv2
import logging
logger = logging.getLogger('image')


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

    _info = None

    def __init__(self, parent, image_path):
        self.player = parent
        self.load_image(image_path)

    def reset_display(self):
        self._im_display = self._im_original
        self._info = None

    def set_info(self, info):
        self._info = info

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

    def draw_sub_image(self, position, size, subimage):
        self._im_display = self._im_display.copy()
        self._im_display[
            position[1]:position[1]+size[1],
            position[0]:position[0]+size[0]
        ] = subimage

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

    def draw_info(self, im, start_point, info_list):
        for info in info_list:
            if type(info) in (str, int, float):
                cv2.putText(im, str(info), tuple(start_point), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (191, 127, 255), 1, cv2.LINE_AA, False)
            elif type(info) == bool:
                thickness = info and -1 or 1
                cv2.circle(im, tuple(numpy.add(start_point, [25, -5])), 7, (191, 127, 255), thickness)
            elif type(info) in (list, numpy.ndarray):
                # Assume list to be pattern
                for step in info:
                    if step:
                        color = (191, 127, 255)
                    else:
                        color = (31, 0, 63)
                    cv2.rectangle(
                        im,
                        tuple(start_point),
                        tuple(numpy.add(start_point, [42, 7])),
                        color,
                        -1,
                    )
                    start_point[1] += 10
            elif info is None:
                pass
            else:
                logger.warning('Unknown info {0}: {1}'.format(type(info), info))
            start_point[1] += 25

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

        if self._info is not None:
            self.draw_info(im, [5, 30], self._info[0])
            self.draw_info(im, [970, 30], self._info[1])

        if fullscreen:
            cv2.namedWindow('Image', cv2.WND_PROP_FULLSCREEN)
            cv2.setWindowProperty(
                'Image', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN
            )

        cv2.imshow('Image', im)
        cv2.waitKey(wait_interval)
