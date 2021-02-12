

import pkgutil
import importlib
import logging
logger = logging.getLogger('track')

import image2midi.note
import image2midi.processors
import image2midi.producers


class Track(object):
    # Imported available Processor modules / classes
    processors = {}

    # Imported available Producer modules / classes
    producers = {}

    # Currently active Processor / Producer for this Track
    processor = None
    producer = None

    # MIDI channel wrapper for this Track
    channel = None

    def __init__(self, parent, channel_number, producer_config=dict(), processor_config=dict()):
        self.player = parent

        # Import all available processor / producer modules
        self.import_processors()
        self.import_producers()
        logger.info('Track.processors loaded: {0}'.format(self.processors.keys()))
        logger.info('Track.producers loaded: {0}'.format(self.producers.keys()))

        # Setup channel wrapper on specified MIDI channel
        self.channel = image2midi.note.NoteChannel(self, channel_number)

        # Setup processor / producer from specified values, fallback to
        # first available value as default
        if processor_config.get('processor') in self.processors.keys():
            self.processor = self.processors.get(processor_config.get('processor')).Processor(self, **processor_config)
        else:
            self.processor = list(self.processors.values())[0].Processor(self, **processor_config)
        if producer_config.get('producer') in self.producers.keys():
            self.producer = self.producers.get(producer_config.get('producer')).Producer(self, **producer_config)
        else:
            self.producer = list(self.producers.values())[0].Producer(self, **producer_config)

    def switch_processor(self, d_index):
        index = ( list(self.processors.keys()).index(self.processor.__module__) + d_index ) % len(self.processors)
        act_config = self.processor.config2dict()
        act_config.update({'cursor': self.processor.cursor})
        self.processor = self.processors.get(list(self.processors.keys())[index]).Processor(
            self,
            **act_config
        )

    def switch_producer(self, d_index):
        index = ( list(self.producers.keys()).index(self.producer.__module__) + d_index ) % len(self.producers)
        act_config = self.producer.config2dict()
        self.producer = self.producers.get(list(self.producers.keys())[index]).Producer(
            self,
            **act_config
        )

    def import_processors(self):
        """ Find available Processor providing modules.
        """
        for _, modname, _ in pkgutil.walk_packages(
            image2midi.processors.__path__,
            image2midi.processors.__name__ + '.'
        ):
            self.processors.update({
                modname: importlib.import_module(modname)
            })

    def import_producers(self):
        """ Find available Producer providing modules.
        """
        for _, modname, _ in pkgutil.walk_packages(
            image2midi.producers.__path__,
            image2midi.producers.__name__ + '.'
        ):
            self.producers.update({
                modname: importlib.import_module(modname)
            })

    def step(self):
        """ Perform track step. Will be called every BPM cycle from player.
        """
        self.processor.step()
        self.producer.set_value(
            self.processor.get_value()
        )
        self.producer.play()
