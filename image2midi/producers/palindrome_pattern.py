
import numpy
import twisted.internet.reactor

import image2midi.producers.euclidian_pattern

TYPE='GATE'


class Producer(image2midi.producers.euclidian_pattern.Producer):
    """
    """
    pattern_length = 8
    ## TODO steps_per_beat other than pattern length
    ## steps_per_beat = 8
    note = 36
    _name = 'Palindr'

    def gen_pattern(self):
        # Compute how many active steps from producer value
        self._k = int(self.value * self.pattern_length)

        # Generate half Euclidian pattern
        k = int(self._k / 2)
        pattern = image2midi.producers.euclidian_pattern.EuclidianPattern(k, int(self.pattern_length / 2))
        pattern = numpy.array(pattern).flatten()
        # Concatenate inverted / non-inverted half Euclidian pattern together
        patterns = [pattern[::-1],]
        if self.pattern_length % 2:
            if self._k % 2:
                patterns.append([1,])
            else:
                patterns.append([0,])
        patterns.append(pattern)
        self._pattern = numpy.concatenate(patterns)

        image2midi.producers.logger.info('Pattern: {0} {1}'.format(self.note, self._pattern))
