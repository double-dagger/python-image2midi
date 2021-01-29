
import optparse
import logging
logger = logging.getLogger('')

import image2midi.track

import twisted.internet.reactor

if __name__ == '__main__':
    # Setup logging
    formatter = logging.Formatter(
        fmt='%(asctime)s [%(levelname)s]\t%(module)s: %(message)s'
    )
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)

    # Parse command line options
    p = optparse.OptionParser()
    p.add_option(
        '-p', '--port',
        dest='port_name',
        help='Name of MIDI Port name for output',
        default='KeyStep Pro:KeyStep Pro MIDI 1 20:0'
    )
    p.add_option(
        '-b', '--bpm',
        dest='bpm',
        help='BPM for playback',
        type='float',
        default=66
    )
    p.add_option(
        '-c', '--control-channel',
        dest='control_channel',
        help='Control channel number. Intended for Arturia BS Pro control mode',
        type='int',
        default=15
    )
    p.add_option(
        '--config',
        dest='config_file',
        help='Configuration file to store / load from.',
        default='/tmp/midi_image.config.json'
    )
    p.add_option(
        '--image-dir',
        dest='image_dir',
        help='Directory containing images to play. All *.jpg files will be added recursively',
        default='/tmp',
    )

    (options, args) = p.parse_args()

    # Initialize Track object
    track = image2midi.track.Track(
        port_name=options.port_name,
        bpm=options.bpm,
        control_channel=options.control_channel,
        config_file=options.config_file,
        image_dir=options.image_dir,
    )

    # Create loop and run
    track.internal_clock()

    # Start reactor
    twisted.internet.reactor.run()
