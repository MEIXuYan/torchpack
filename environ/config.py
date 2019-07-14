import importlib

from .container import G

__all__ = ['Config', 'configs', 'update_configs_from_module', 'update_configs_from_modules']


class Config(G):
    def __init__(self, callable=None):
        super().__init__()
        self.__callable__ = callable

    def keys(self):
        for key in super().keys():
            if key != '__callable__':
                yield key

    def items(self):
        for key, val in super().items():
            if key != '__callable__':
                yield key, val

    def __call__(self, *args, **kwargs):
        for key, val in self.items():
            if key not in kwargs:
                kwargs[key] = val
        return self.__callable__(*args, **kwargs)

    def __str__(self, indent=0, verbose=None):
        # default value: True for non-callable; False for callable
        verbose = (self.__callable__ is None) if verbose is None else verbose

        assert self.__callable__ is not None or verbose
        if self.__callable__ is not None and not verbose:
            return str(self.__callable__)

        text = ''
        if self.__callable__ is not None and indent == 0:
            text += str(self.__callable__) + '\n'
            indent += 2

        for key, val in self.items():
            text += ' ' * indent + '[{}]'.format(key)
            if not isinstance(val, Config):
                text += ' = {}'.format(val)
            else:
                if val.__callable__ is not None:
                    text += ' = ' + str(val.__callable__)
                text += '\n' + val.__str__(indent + 2, verbose=verbose)
            text += '\n'

        # remove the last newline
        return text[:-1]


configs = Config()


def update_configs_from_module(module, recursive=False):
    update_configs_from_modules([module], recursive=recursive)


def update_configs_from_modules(modules, recursive=False):
    imports = set()

    for module in modules:
        # format: aaa/bbb/ccc/ddd.py => aaa.bbb.ccc.ddd
        module = module.replace('.py', '').replace('/', '.')

        # import: aaa.__init__, aaa.bbb.__init__, aaa.bbb.ccc.__init__
        if recursive:
            for index in [index for index, char in enumerate(module) if char == '.']:
                submod = module[:index + 1] + '__init__'
                if submod not in imports:
                    imports.add(submod)
                    importlib.import_module(submod)

        # import: aaa.bbb.ccc.ddd
        if module not in imports:
            imports.add(module)
            importlib.import_module(module)
