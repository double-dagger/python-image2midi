
import time
import logging
import json
import sys
import os
import os.path
import pkgutil
import importlib
logger = logging.getLogger('track')

import twisted.internet.reactor
import mido

import image2midi.note
import image2midi.backends

class Track(object):
    bpm = None
    image = None
    last_time = None
    step_length = 0.0
    channels = []
    stopped = False
    index_image = 0
    index_backend = 0
    exit_mode = False
    exit_counter = 0

    def __init__(self, image_dir, port_name, bpm, config_file, control_channel=None):
        self.control_channel = control_channel
        self.config_file = config_file

        self.outport = mido.open_output(port_name)
        self.inport = mido.open_input(port_name, callback=self.midi_callback)

        self.set_bpm(bpm)

        # Init outport channel wrappers
        for i in range(0,10):
            if i == 9:
                self.channels.append(image2midi.note.NoteChannel(self, i))
            else:
                self.channels.append(image2midi.note.MonophonicNoteChannel(self, i))

        # Find all images in image_dir
        self.find_image_paths(image_dir)

        # Import available backends
        self.import_backends()

        # Init image
        self.init_image()

        # Add cleanup function before shutdown
        # to stop all playing notes when program is stopped.
        twisted.internet.reactor.addSystemEventTrigger(
            'before', 'shutdown', self.cleanup
        )

        twisted.internet.reactor.addSystemEventTrigger(
            'after', 'shutdown', self.shutdown_with_exitcode
        )

    def shutdown_with_exitcode(self):
        os._exit(self.exit_counter)

    def next_image(self):
        self.load_image_index(self.index_image + 1)

    def prev_image(self):
        self.load_image_index(self.index_image - 1)

    def next_backend(self):
        self.load_backend_index(self.index_backend + 1)

    def prev_backend(self):
        self.load_backend_index(self.index_backend - 1)

    def load_image_index(self, index):
        if index < 0:
            index = len(self.image_paths) - 1
        if index >= len(self.image_paths):
            index = 0
        index = max(index, 0)
        index = min(index, len(self.image_paths))
        self.index_image = index
        self.init_image()
        self.restart()

    def load_backend_index(self, index):
        if index < 0:
            index = len(self.backends) - 1
        if index >= len(self.backends):
            index = 0
        index = max(index, 0)
        index = min(index, len(self.backends))
        self.index_backend = index
        self.init_image()
        self.restart()

    def find_image_paths(self, image_dir):
        self.image_paths = []
        for (dirpath, dirnames, filenames) in os.walk(image_dir):
            dirnames.sort()
            filenames.sort()
            for filename in filenames:
                if os.path.splitext(filename)[1].lower() in ('.jpg', '.jpeg', '.png'):
                    self.image_paths.append(os.path.join(dirpath, filename))

    def import_backends(self):
        self.backends = []
        for _, modname, _ in pkgutil.walk_packages(
            image2midi.backends.__path__,
            image2midi.backends.__name__ + '.'
        ):
            if modname == 'image2midi.backends.common':
                # Skip common
                continue
            self.backends.append(
                importlib.import_module(modname)
            )

    def init_image(self):
        if self.image is not None:
            del self.image
        self.image = self.backends[self.index_backend].Image(self, self.image_paths[self.index_image])
        self.image.show_image()
        self.set_bpm(self.bpm)
        self.stop_all_notes()
        self.load_cc()

    def stop_all_notes(self):
        for channel in self.channels:
            channel.stop_all_notes()

    def cleanup(self):
        self.set_bpm(0)
        self.stop_all_notes()

    def set_bpm(self, bpm):
        prev_bpm = self.bpm
        self.bpm = bpm
        # 8-tackt(?! WTF)
        ## self.bpm *= 8
        # Initialize step length from BPM
        if self.bpm == 0:
            self.bpm_step_length = 0
        else:
            self.bpm_step_length = 60 / self.bpm
        if self.image and hasattr(self.image, 'bpm_multiplier') and self.image.bpm_multiplier:
            self.bpm_step_length /= self.image.bpm_multiplier
        if prev_bpm == 0 and self.bpm != 0:
            # Restart clock if bpm raised from zero.
            self.on_clock()

    def midi_callback(self, cc):
        # For externally clocked run. Not used now.
        if cc.type == 'clock':
            self.on_clock()

        if (hasattr(cc, 'channel') and
                cc.channel == self.control_channel):

            if cc.type == 'control_change':
                self.midi_cc(cc)
            if cc.type == 'note_on':
                self.midi_note_on(cc)
            if cc.type == 'note_off':
                self.midi_note_off(cc)

    def midi_note_off(self, cc):
        if cc.note == 43:
            if self.exit_counter > 0:
                twisted.internet.reactor.stop()
            else:
                self.exit_mode = False
                self.exit_counter = 0

    def midi_note_on(self, cc):
        print(cc)
        if cc.note == 44:
            twisted.internet.reactor.callLater(0.01, self.next_image)
        if cc.note == 36:
            twisted.internet.reactor.callLater(0.01, self.prev_image)
        if cc.note == 45:
            twisted.internet.reactor.callLater(0.01, self.next_backend)
        if cc.note == 37:
            twisted.internet.reactor.callLater(0.01, self.prev_backend)
        if cc.note == 43:
            self.exit_mode = True
        if cc.note == 42 and self.exit_mode:
            self.exit_counter += 1

    def midi_cc(self, cc):
        self.save_cc(cc)

        if cc.control == 20:
            self.set_bpm(cc.value)
        if cc.control == 85 and cc.value == 0:
            self.restart()

        self.image.midi_cc(cc)

        if cc.control == 117:
            self.stopped = cc.value == 127

    def save_cc(self, cc):
        try:
            with open(self.config_file, 'r') as f:
                cc_json = json.load(f) or {}
        except:
            cc_json = {}
        cc_json[cc.control] = cc.value
        with open(self.config_file, 'w') as f:
            json.dump(cc_json, f)

    def load_cc(self):
        try:
            with open(self.config_file, 'r') as f:
                cc_json = json.load(f) or {}
        except:
            cc_json = {}
        for cc_item in cc_json.items():
            cc = mido.Message(
                'control_change',
                channel = self.control_channel,
                control = int(cc_item[0]),
                value = cc_item[1],
            )
            logger.debug('Loaded CC: {0}'.format(cc))
            self.midi_callback(cc)

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
