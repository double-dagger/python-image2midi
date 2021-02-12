
import numpy


class Configurable(object):
    """ Mixin class to set configuration of class attributes via
        JSON config file.
    """

    def configure(self, kwargs):
        for config_var in self.config_vars:
            if config_var in kwargs:
                setattr(self, config_var, kwargs.get(config_var))

    def __config_var_value(self, config_var):
        if hasattr(self, config_var):
            value = getattr(self, config_var)
            if type(value) == numpy.ndarray:
                value = value.tolist()
            return (config_var, value)

    def config2dict(self):
        return dict(
            filter(
                lambda x: x is not None,
                map(self.__config_var_value, self.config_vars)
            )
        )
