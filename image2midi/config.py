

class Configurable(object):
    """ Mixin class to set configuration of class attributes via
        JSON config file.
    """

    def configure(self, kwargs):
        for config_var in self.config_vars:
            if config_var in kwargs:
                setattr(self, config_var, kwargs.get(config_var))
