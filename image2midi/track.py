

import pkgutil
import importlib
import logging
logger = logging.getLogger('track')

import image2midi.note
import image2midi.processors
import image2midi.producers
import image2midi.config


class Track(image2midi.config.Configurable):
    # Imported available Processor modules / classes
    processors = {}

    # Imported available Producer modules / classes
    producers = {}

    # Currently active Processor / Producer for this Track
    processor = None
    producer = None

    # MIDI channel wrapper for this Track
    channel = None

    channel_number = 0
    producer_type = None
    config_vars = ['channel_number', 'producer_type']

    def __init__(self, parent, **kwargs):
        self.player = parent
        super().configure(kwargs)

        # Import all available processor / producer modules
        self.import_processors()
        self.import_producers()
        logger.info('Track.processors loaded: {0}'.format(self.processors.keys()))
        logger.info('Track.producers loaded: {0}'.format(self.producers.keys()))

        # Setup channel wrapper on specified MIDI channel
        self.channel = image2midi.note.NoteChannel(self, self.channel_number)

        # Setup processor / producer from specified values, fallback to
        # first available value as default
        self.init_processor(kwargs.get('processor_config'))
        self.init_producer(kwargs.get('producer_config'))

    def init_processor(self, processor_config):
        if processor_config.get('processor') in self.processors.keys():
            self.processor = self.processors.get(processor_config.get('processor')).Processor(self, **processor_config)
        else:
            self.processor = list(self.processors.values())[0].Processor(self, **processor_config)

    def init_producer(self, producer_config):
        if producer_config.get('producer') in self.producers.keys():
            self.producer = self.producers.get(producer_config.get('producer')).Producer(self, **producer_config)
        else:
            self.producer = list(self.producers.values())[0].Producer(self, **producer_config)

    def configure(self, kwargs):
        """ Custom (re)configuration method
        """
        super().configure(kwargs)
        if 'processor_config' in kwargs.keys():
            self.init_processor(kwargs.get('processor_config'))
        if 'producer_config' in kwargs.keys():
            self.init_producer(kwargs.get('producer_config'))

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
        self.producers = {}
        for _, modname, _ in pkgutil.walk_packages(
            image2midi.producers.__path__,
            image2midi.producers.__name__ + '.'
        ):
            module = importlib.import_module(modname)
            if self.producer_type is not None and ( not hasattr(module, 'TYPE') or module.TYPE != self.producer_type ):
                logger.debug('Skipping to import module: {0}'.format(module))
            else:
                self.producers.update({
                    modname: module
                })

    def step(self):
        """ Perform track step. Will be called every BPM cycle from player.
        """
        self.processor.step()
        self.producer.set_value(
            self.processor.get_value()
        )
        self.producer.play()
