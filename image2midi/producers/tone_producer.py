
import twisted.internet.reactor

import image2midi.producers


class Producer(image2midi.producers.Producer):
    """
    """
    min_note = 12
    max_note = 36

    quant_note = 3

    config_vars = image2midi.producers.Producer.config_vars + ['min_note', 'max_note', 'quant_note']

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.configure(kwargs)

    def param1(self, d_value):
        self.min_note = min(self.max_note, ( self.min_note + d_value ) % 72)

    def param2(self, d_value):
        self.max_note = max(self.min_note, ( self.max_note + d_value ) % 72)

    def param3(self, d_value):
        self.quant_note = ( self.quant_note + d_value ) % 24

    def play(self):
        note = int( ( self.max_note - self.min_note ) * self.value + self.min_note )
        if self.quant_note:
            note = int( note / self.quant_note ) * self.quant_note

        if ( not self.track.channel.check_note(note) ) and note is not None:
            image2midi.producers.logger.info('Note change: {0}'.format(note))
            twisted.internet.reactor.callLater(
                self.track.player.step_length / 2,
                self.track.channel.play_note,
                note
            )

