
import time
import logging
logger = logging.getLogger('track')

import twisted.internet.reactor
import mido

import image2midi.note
import image2midi.backends.bwcluster
import image2midi.backends.rgbcluster

class Track(object):
    bpm = None
    last_time = None
    step_length = 0.0
    channels = []
    stopped = False

    def __init__(self, image_path, port_name, bpm, control_channel=None):
        self.control_channel = control_channel

        self.image = image2midi.backends.bwcluster.Image(self, image_path)
#        self.image = image2midi.backends.rgbcluster.Image(self, image_path)
        self.image.show_image(wait_interval=100)

        self.outport = mido.open_output(port_name)
        self.inport = mido.open_input(port_name, callback=self.midi_callback)

        self.set_bpm(bpm)

        # Init outport channel wrappers
        for i in range(0,16):
            if i == 9:
                self.channels.append(image2midi.note.NoteChannel(self, i))
            else:
                self.channels.append(image2midi.note.MonophonicNoteChannel(self, i))

        # Add cleanup function before shutdown
        # to stop all playing notes when program is stopped.
        twisted.internet.reactor.addSystemEventTrigger(
            'before', 'shutdown', self.cleanup
        )

    def cleanup(self):
        self.set_bpm(0)
        for channel in self.channels:
            channel.stop_all_notes()

    def set_bpm(self, bpm):
        prev_bpm = self.bpm
        self.bpm = bpm
        # 8-tackt(?! WTF)
        self.bpm *= 8
        # Initialize step length from BPM
        if self.bpm == 0:
            self.bpm_step_length = 0
        else:
            self.bpm_step_length = 60 / self.bpm
        if prev_bpm == 0 and self.bpm != 0:
            # Restart clock if bpm raised from zero.
            self.on_clock()

    def midi_callback(self, cc):
        # For externally clocked run. Not used now.
        if cc.type == 'clock':
            self.on_clock()

        if (hasattr(cc, 'channel') and
                cc.channel == self.control_channel):

            if cc.control == 20:
                self.set_bpm(cc.value)
            if cc.control == 85 and cc.value == 0:
                self.restart()

            self.image.midi_cc(cc)

            if cc.control == 117:
                self.stopped = cc.value == 127

    def restart(self):
        self.image.restart()

    def on_clock(self):
        if self.last_time is not None:
            self.step_length = time.time()-self.last_time
        self.last_time = time.time()

        self.image.next_cluster()

    def internal_clock(self):
        twisted.internet.reactor.callLater(self.bpm_step_length, self.internal_clock)
        if not self.stopped:
            self.on_clock()
