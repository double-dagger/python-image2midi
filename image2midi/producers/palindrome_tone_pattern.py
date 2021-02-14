
import numpy
import twisted.internet.reactor

import image2midi.producers
import image2midi.producers.tone_producer
import image2midi.producers.palindrome_pattern

TYPE='NOTE'


class Producer(image2midi.producers.tone_producer.Producer, image2midi.producers.palindrome_pattern.Producer):
    _name = 'nPali'
    _pattern = []
    _notes = []

    config_vars = image2midi.producers.Producer.config_vars + ['one_step', 'min_note', 'max_note', 'quant_note', 'pattern_length', 'note', 'steps_per_beat']

    def get_info(self):
       return image2midi.producers.Producer.get_info(self) + [
            '< {0}'.format(self.min_note),
            '> {0}'.format(self.max_note),
            '~ {0}'.format(self.quant_note),
            'len: {0}'.format(self.pattern_length),
            'ste: {0}'.format(self.steps_per_beat or '-'),
            None,
            self._pattern
        ]

    def generate_pattern(self):
        # Compute how many active steps from producer value
        self.generate_k()
        self.generate_note()
        self._notes.insert(0, self._note)

        # Generate half Euclidian pattern
        k = int(self._k / 2)
        pattern = image2midi.producers.euclidian_pattern.EuclidianPattern(k, int(self.pattern_length / 2))
        pattern = numpy.array(pattern).flatten()[::-1]

        # Replace pattern active steps with historical note values
        ii = 0
        for i in range(len(pattern)):
            if pattern[i]:
                pattern[i] = self._notes[min(ii, len(self._notes) - 1)]
                ii += 1

        # Concatenate inverted / non-inverted half Euclidian pattern together
        patterns = [pattern,]
        if self.pattern_length % 2:
            if self._k % 2:
                patterns.append([self._notes[min(ii, len(self._notes) - 1)],])
            else:
                patterns.append([0,])
        patterns.append(pattern[::-1])
        self._pattern = numpy.concatenate(patterns)

        image2midi.producers.logger.info('Pattern: {0} {1}'.format(self.note, self._pattern))

    def play(self):
        image2midi.producers.palindrome_pattern.Producer.play(self)
