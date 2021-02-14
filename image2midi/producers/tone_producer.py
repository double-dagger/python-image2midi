
import twisted.internet.reactor

import image2midi.producers

TYPE = 'NOTE'


class Producer(image2midi.producers.Producer):
    """
    """
    min_note = 12
    max_note = 36
    quant_note = 3

    config_vars = image2midi.producers.Producer.config_vars + ['min_note', 'max_note', 'quant_note']

    _name = 'sTone'
    _note = None

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.configure(kwargs)

    def param1(self, d_value):
        self.min_note = max(0, min(self.max_note, ( self.min_note + d_value )))

    def param2(self, d_value):
        self.max_note = min(127, max(self.min_note, ( self.max_note + d_value )))

    def param3(self, d_value):
        self.quant_note = min(max(1, self.quant_note + d_value ), 24)

    def get_info(self):
        return super().get_info() + ['< {0}'.format(self.min_note), '> {0}'.format(self.max_note), '~ {0}'.format(self.quant_note), None, self._note]

    def generate_note(self):
        last_note = self._note

        self._note = int( ( self.max_note - self.min_note ) * self.value + self.min_note )
        if self.quant_note:
            self._note = int( self._note / self.quant_note ) * self.quant_note

        if last_note and self.one_step and abs(self._note - last_note) > self.quant_note:
            self._note = max(min(last_note + self.quant_note, self._note), last_note - self.quant_note)

    def play(self):
        self.generate_note()

        if ( not self.track.channel.check_note(self._note) ) and self._note is not None:
            image2midi.producers.logger.info('Note change: {0}'.format(self._note))
            twisted.internet.reactor.callLater(
                self.track.player.step_length / 2,
                self.track.channel.play_note,
                self._note
            )

