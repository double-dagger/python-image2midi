
import numpy
import twisted.internet.reactor

import image2midi.producers


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
    ## TODO steps_per_beat other than pattern length
    ## steps_per_beat = 8
    note = 36

    config_vars = image2midi.producers.Producer.config_vars + ['pattern_length', 'note']

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.configure(kwargs)

    def param1(self, d_value):
        self.pattern_length = ( self.pattern_length + d_value ) % 64

    def param4(self, d_value):
        self.note = ( self.note + d_value ) % 128

    def get_pattern(self):
        # Compute how many active steps from producer value
        k = int(self.value * self.pattern_length)

        # Generate Euclidian pattern, flatten and set note
        pattern = EuclidianPattern(k, self.pattern_length)
        pattern = numpy.array(pattern).flatten()
        image2midi.producers.logger.info('Pattern: {0} {1}'.format(self.note, pattern))
        return pattern

    def play(self):
        pattern = self.get_pattern()

        # Play pattern using twisted. Set callLater for every active step.
        step_length = self.track.player.step_length / self.pattern_length
        offset = 0.0
        for step in pattern:
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

