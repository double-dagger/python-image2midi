
import numpy
import twisted.internet.reactor

import image2midi.producers.euclidian_pattern

TYPE='GATE'


class Producer(image2midi.producers.euclidian_pattern.Producer):
    """
    """
    _name = 'Palindr'

    def generate_pattern(self):
        # Compute how many active steps from producer value
        self.generate_k()

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
        self.quantize_pattern()

        image2midi.producers.logger.info('Pattern: {0} {1}'.format(self.note, self._pattern))
