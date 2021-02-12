
import logging
logger = logging.getLogger('note')

import mido

class NoteChannel(object):
    channel_number = None
    notes = None

    def __init__(self, parent, channel_number):
        self.track = parent
        self.channel_number = channel_number
        self.notes = []

    def add_note(self, note):
        logger.debug('add_note #{0.channel_number} {0.notes} {1}'.format(self, note))
        if note is None:
            return
        self.notes.append(note)
        self.track.player.outport.send(
            mido.Message('note_on', note=note, channel=self.channel_number)
        )

    def stop_note(self, note):
        ## logger.debug('stop_note #{0.channel_number} {0.notes} {1}'.format(self, note))
        if note is None or note not in self.notes:
            return
        self.notes.remove(note)
        self.track.player.outport.send(
            mido.Message('note_off', note=note, channel=self.channel_number)
        )

    def stop_all_notes(self):
        for playing_note in list(self.notes):
            self.stop_note(playing_note)

    def play_note(self, note):
        """ Play note
        """
        self.add_note(note)

    def check_note(self, note):
        """ Check is note is present ( playing )
            If other note is playing stop it.
        """
        ## logger.debug('check_note #{0.channel_number} {0.notes} {1}'.format(self, note))
        if note in self.notes:
            return True
        self.stop_all_notes()

