
import time
import logging
import json
import sys
import os
import os.path
import pkgutil
import importlib
import hashlib
logger = logging.getLogger('player')

import twisted.internet.reactor
import mido

import image2midi.track
import image2midi.image
import image2midi.note

class Player(object):
    bpm = None
    image = None
    last_time = None
    step_length = 0.0
    channels = []
    stopped = False
    index_image = 0
    index_backend = 0
    switch_dirs_mode = False
    exit_mode = False
    exit_counter = 0
    tracks = []
    active_track = 0
    alt = False
    shared_cursor = True
    show_cursor = True
    show_working_image = False
    show_info = True

    def __init__(self, image_dir, port_name, bpm, config_file, control_channel=None):
        # Setup midi and configuration from command line arguments.
        self.control_channel = control_channel
        self.config_file = config_file
        self.outport = mido.open_output(port_name)
        self.inport = mido.open_input(port_name, callback=self.midi_callback)

        # Setup BPM from command line argument. Settings might override.
        self.set_bpm(bpm)

        # Find all images in image_dir and initalize Image object.
        self.load_image_paths(image_dir)
        self.image = image2midi.image.Image(self, self.image_paths[0])

        # Load configuration and try to find image_path if specified.
        self.load_config()
        self.find_image_path(self.config.get('image_path'))

        # Init configured tracks
        self.init_tracks()
        self.active_track = self.config.get('active_track', 0) % len(self.tracks)

        # Manual configuration
        self.shared_cursor = self.config.get('shared_cursor', self.shared_cursor)
        self.show_cursor = self.config.get('show_cursor', self.show_cursor)
        self.show_working_image = self.config.get('show_working_image', self.show_working_image)
        self.show_info = self.config.get('show_info', self.show_info)

        # Simulate switch_image to load proper image.
        self.switch_image(0)

        # Add cleanup function before shutdown
        # to stop all playing notes when program is stopped.
        twisted.internet.reactor.addSystemEventTrigger(
            'before', 'shutdown', self.cleanup
        )

        twisted.internet.reactor.addSystemEventTrigger(
            'after', 'shutdown', self.shutdown_with_exitcode
        )

    def load_config(self):
        try:
            with open(self.config_file, 'r') as f:
                self.config = json.load(f) or {}
        except FileNotFoundError:
            logger.warning('Can not open file `{0}`'.format(self.config_file))

    def image_hash(self):
        try:
            with open(self.image_paths[self.index_image], 'rb') as f:
                md5 = hashlib.md5()
                while True:
                    data = f.read(65536)
                    if not data:
                        break
                    md5.update(data)
                return md5.hexdigest()
        except FileNotFoundError:
            logger.warning('Can not open file `{0}`'.format(self.config_file))

    def image_config_file(self):
        return os.path.join('.', '{0}.json'.format(self.image_hash()))

    def save_image_config(self):
        track_config = []
        for track in self.tracks:
            processor_config = track.processor.config2dict()
            processor_config.update({'processor': track.processor.__module__})
            processor_config.update(track.processor.cursor.config2dict())
            producer_config = track.producer.config2dict()
            producer_config.update({'producer': track.producer.__module__})
            track_config.append({
                'channel_number': track.channel.channel_number,
                'processor_config': processor_config,
                'producer_config': producer_config,
            })
        config_filename = self.image_config_file()
        try:
            with open(config_filename, 'w') as f:
                json.dump(track_config, f, indent=2)
                logger.info('Configuration for current image saved to: {0}'.format(config_filename))
        except FileNotFoundError:
            logger.warning('Can not write file `{0}`'.format(config_filename))

    def load_image_config(self):
        config_filename = self.image_config_file()
        try:
            with open(config_filename, 'r') as f:
                config = json.load(f)
                for i in range(len(config)):
                    self.tracks[i].configure(config[i])
                logger.info('Configuration loaded from: {0}'.format(config_filename))
        except FileNotFoundError:
            logger.warning('Can not open file `{0}`'.format(config_filename))


    def init_tracks(self):
        if not self.config.get('tracks'):
            logger.warning('Loaded config with no tracks specified.')
            return
        for track in self.config.get('tracks'):
            self.tracks.append(image2midi.track.Track(
                self, **track
            ))

    def shutdown_with_exitcode(self):
        os._exit(self.exit_counter)

    def switch_image(self, d_index):
        if self.alt:
            # In switch dirs mode find the first image in different dir
            # in given direction.
            # When going backwards, it results in the last image of dir
            act_dir = new_dir = os.path.dirname(self.image_paths[self.index_image])
            step = max(min(d_index, 1), -1)
            while act_dir == new_dir:
                self.index_image = ( self.index_image + d_index ) % len(self.image_paths)
                new_dir = os.path.dirname(self.image_paths[self.index_image])
        else:
            self.index_image = ( self.index_image + d_index ) % len(self.image_paths)
        self.reload_image()

    def reload_image(self):
        self.image.load_image(self.image_paths[self.index_image])
        self.image.show_image()

    def find_image_path(self, image_path):
        """ Try to find index of image specified by image_path.
            If not found, fallback to 0
        """
        try:
            self.index_image = self.image_paths.index(image_path)
        except ValueError:
            self.index_image = 0

    def load_image_paths(self, image_dir):
        self.image_paths = []
        for (dirpath, dirnames, filenames) in os.walk(image_dir):
            dirnames.sort(key=lambda d: os.stat(os.path.join(dirpath, d)).st_mtime, reverse=True)
            filenames.sort()
            for filename in filenames:
                if os.path.splitext(filename)[1].lower() in ('.jpg', '.jpeg', '.png'):
                    self.image_paths.append(os.path.join(dirpath, filename))

    def track(self):
        """ Reference to active track
        """
        return self.tracks[self.active_track]

    def switch_track(self, d_index):
        self.active_track = min(max(0, self.active_track + d_index), len(self.tracks) - 1)

    def share_cursor(self, size, step_size):
        if self.shared_cursor:
            for track in self.tracks:
                if track != self.track():
                    track.processor.cursor.configure({
                        'size': size.copy(),
                        'step_size': step_size.copy(),
                    })

    def stop_all_notes(self):
        for channel in self.channels:
            channel.stop_all_notes()

    def cleanup(self):
        self.set_bpm(0)
        self.stop_all_notes()

    def set_bpm(self, bpm):
        prev_bpm = self.bpm
        self.bpm = bpm
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
        if cc.note == 44:
            self.switch_dirs_mode = False

    def midi_note_on(self, cc):
        if cc.note == 44:
            self.switch_dirs_mode = True
        if cc.note == 43:
            self.exit_mode = True
        if cc.note == 42 and self.exit_mode:
            self.exit_counter += 1

    def relative_cc_convert(self, cc):
        if cc.value > 64:
            return cc.value - 128
        return cc.value

    def self_eval(self, command):
        try:
            exec(command)
        except Exception as e:
            logger.error('CC eval failed: `{0}`: {1}'.format(command, e))

    def midi_cc(self, cc):
        if str(cc.control) in self.config.get('midi_control').keys():
            cc_config = self.config.get('midi_control').get(str(cc.control))

            if cc_config.get('type') == 'absolute_value':
                cc_value = cc.value
            elif cc_config.get('type') == 'relative_value':
                if cc.value == 0:
                    # Relative value == 0 is void action.
                    return
                cc_value = self.relative_cc_convert(cc)
            elif cc_config.get('type') == 'boolean_value':
                cc_value = cc.value != 0
            elif cc_config.get('type') == 'no_value':
                cc_value = ''
                if cc.value == 0:
                    # Only on ``key down``
                    return
            else:
                logger.warning('Unknown CC({0.control}) configuration `type` = `{1}`'.format(cc, cc_config.get('type')))
                return

            if cc_config.get('operation') == 'call':
                dest = cc_config.get('dest')
                if self.alt and 'alt_dest' in cc_config.keys():
                    dest = cc_config.get('alt_dest')
                command = '{0}({1})'.format(dest, cc_value)
            elif cc_config.get('operation') == 'assign':
                command = '{0} = {1}'.format(cc_config.get('dest'), cc_value)
            elif cc_config.get('operation') == 'alt':
                self.alt = cc_value != 0
                return
            elif cc_config.get('operation') == 'stop':
                self.stopped = cc_value != 0
                return
            elif cc_config.get('operation') == 'restart':
                if cc_value == 0:
                    self.restart()
                return
            else:
                logger.warning('Unknown CC({0.control}) configuration `operation` = `{1}`'.format(cc, cc_config.get('operation')))
                return

            logger.debug('CC: {0}'.format(command))
            twisted.internet.reactor.callLater(0.01, self.self_eval, command)

    def restart(self):
        """
        """
        for track in self.tracks:
            track.processor.reset()

    def on_clock(self):
        if self.last_time is not None:
            self.step_length = time.time()-self.last_time
        self.last_time = time.time()
        self.step()

    def step(self):
        """ Perform step. Process step on all tracks, draw active cursor, show image.
        """
        self.image.reset_display()
        for track in self.tracks:
            track.step()
        if self.show_working_image:
            # TOOD
            pass
        if self.show_cursor:
            self.track().processor.draw_cursor()
        if self.show_info:
            info = [
                [' ( {0} )'.format(self.active_track), None, *self.track().processor.get_info()],
                ['ch: {0}'.format(self.track().channel.channel_number), None, *self.track().producer.get_info()],
            ]
            self.image.set_info(info)
        self.image.show_image()

    def internal_clock(self):
        twisted.internet.reactor.callLater(self.bpm_step_length, self.internal_clock)
        if not self.stopped:
            self.on_clock()
