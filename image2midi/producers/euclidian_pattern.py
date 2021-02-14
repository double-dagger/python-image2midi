
import numpy
import twisted.internet.reactor
import logging
logger = logging.getLogger('producer')

import image2midi.producers

TYPE='GATE'


def EuclidianPattern(k, n):
    pattern = [[1]] * k + [[0]] * (n - k)
    while k:
        cut = min(k, len(pattern) - k)
        k, pattern = cut, [pattern[i] + pattern[k + i] for i in range(cut)] + \
            pattern[cut:k] + pattern[k + cut:]
    return pattern


class Producer(image2midi.producers.Producer):
    """
    """
    pattern_length = 8
    steps_per_beat = None
    note = 36

    _name = 'Euclid'
    __in_pattern = False
    config_vars = image2midi.producers.Producer.config_vars + ['pattern_length', 'note', 'steps_per_beat']

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.configure(kwargs)

    def param1(self, d_value):
        self.pattern_length = min(max(1, ( self.pattern_length + d_value )), 128)

    def param4(self, d_value):
        self.note = ( self.note + d_value ) % 128

    def param8(self, d_value):
        if self.steps_per_beat is None:
            if d_value > 0:
                self.steps_per_beat = d_value
            return
        self.steps_per_beat = min( self.steps_per_beat + d_value, 128)
        if self.steps_per_beat < 1:
            self.steps_per_beat = None

    def get_info(self):
        return (self._name, 'len: {0}'.format(self.pattern_length), 'ste: {0}'.format(self.steps_per_beat or '-'), None, 'nt.: {0}'.format(self.note), self._pattern)

    def generate_pattern(self):
        # Compute how many active steps from producer value
        self._k = int(self.value * self.pattern_length)

        # Generate Euclidian pattern, flatten and set note
        self._pattern = EuclidianPattern(self._k, self.pattern_length)
        self._pattern = numpy.array(self._pattern).flatten()
        image2midi.producers.logger.info('Pattern: {0} {1}'.format(self.note, self._pattern))

    def reset_in_pattern(self):
        self.__in_pattern = False

    def play(self):
        if self.__in_pattern:
            # Playing previous pattern. Do not start a new one
            logger.debug('Playing previous pattern ...')
            return

        # Generate pattern
        self.generate_pattern()

        if self.steps_per_beat is not None:
            # If steps_per_beat is specified generate pattern which might overlap
            # beat step. Set __in_pattern flag and schedule reset.
            step_length = self.track.player.step_length / self.steps_per_beat
            self.__in_pattern = True
            twisted.internet.reactor.callLater(
                step_length * (self.pattern_length - 0.5),
                self.reset_in_pattern,
            )
        else:
            # If steps_per_beat is not specified, design pattern to fit in
            # beat step.
            step_length = self.track.player.step_length / self.pattern_length

        offset = 0.0
        # Play pattern using twisted. Set callLater for every active step.
        for step in self._pattern:
            if step == 1:
                twisted.internet.reactor.callLater(
                    offset,
                    self.track.channel.add_note,
                    self.note
                )
                twisted.internet.reactor.callLater(
                    offset + step_length / 2,
                    self.track.channel.stop_note,
                    self.note
                )
            offset += step_length

