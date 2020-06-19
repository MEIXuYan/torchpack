import copy
import os.path as osp
from ast import literal_eval

from ..utils import io

__all__ = ['Config', 'configs']


class Config(dict):
    def __getattr__(self, key):
        if key not in self:
            raise AttributeError(key)
        return self[key]

    def __setattr__(self, key, value):
        self[key] = value

    def load(self, fpath, *, recursive=False):
        if not osp.exists(fpath):
            raise FileNotFoundError(fpath)

        fpaths = [fpath]
        if recursive:
            while fpath:
                fpath = osp.dirname(fpath)
                for fname in ['default.yaml', 'default.yml']:
                    fpaths.append(osp.join(fpath, fname))
        fpaths = fpaths[::-1]

        for fpath in fpaths:
            if osp.exists(fpath):
                self.update(io.load(fpath))

    def reload(self, fpath, *, recursive=False):
        self.clear()
        self.load(fpath, recursive=recursive)

    def update(self, other):
        def __update_from_configs(self, configs):
            for key, value in configs.items():
                if isinstance(value, (dict, Config)):
                    if key not in self or not isinstance(self[key], Config):
                        self[key] = Config()
                    __update_from_configs(self[key], value)
                else:
                    self[key] = value

        def __update_from_arguments(self, opts):
            index = 0
            while index < len(opts):
                opt = opts[index]
                if opt.startswith('--'):
                    opt = opt[2:]
                if '=' in opt:
                    key, value = opt.split('=', 1)
                    index += 1
                else:
                    key, value = opt, opts[index + 1]
                    index += 2
                current = self
                subkeys = key.split('.')
                value = literal_eval(value)
                for subkey in subkeys[:-1]:
                    current = current[subkey]
                current[subkeys[-1]] = value

        if isinstance(other, (dict, Config)):
            __update_from_configs(self, other)
        elif isinstance(other, (list, tuple)):
            __update_from_arguments(self, other)
        else:
            raise TypeError(type(other))

    def clone(self):
        return copy.deepcopy(self)

    def dict(self, *, flatten=False):
        configs = dict()
        for key, value in self.items():
            if isinstance(value, Config):
                value = value.dict(flatten=flatten)
            if flatten and isinstance(value, dict):
                for subkey, subval in value.items():
                    configs[key + '.' + subkey] = subval
            else:
                configs[key] = value
        return configs

    def __str__(self):
        texts = []
        for key, value in self.items():
            if isinstance(value, Config):
                seperator = '\n'
            else:
                seperator = ' '
            text = key + ':' + seperator + str(value)
            lines = text.split('\n')
            for k, line in enumerate(lines):
                if k > 0:
                    lines[k] = (' ' * 2) + line
            texts.extend(lines)
        return '\n'.join(texts)

    def __repr__(self):
        return repr(self.dict(flatten=True))


configs = Config()
