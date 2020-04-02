import json
import pickle
from contextlib import contextmanager

import numpy as np
import torch

__all__ = [
    'load', 'save',
    'load_txt', 'save_txt',
    'load_json', 'save_json',
    'load_npy', 'save_npy',
    'load_npz', 'save_npz',
    'load_pth', 'save_pth'
]


@contextmanager
def file_descriptor(f, mode='r'):
    new_fp = False
    try:
        if isinstance(f, str):
            new_fp = True
            f = open(f, mode)
        yield f
    finally:
        if new_fp:
            f.close()


def load_txt(f, **kwargs):
    with file_descriptor(f, 'r') as fd:
        return fd.readlines(**kwargs)


def save_txt(f, obj, **kwargs):
    with file_descriptor(f, 'w') as fd:
        raise NotImplementedError()


def load_json(f, **kwargs):
    with file_descriptor(f, 'r') as fd:
        return json.load(fd, **kwargs)


def save_json(f, obj, **kwargs):
    with file_descriptor(f, 'w') as fd:
        return json.dump(obj, fd, **kwargs)


def load_pkl(f, **kwargs):
    with file_descriptor(f, 'rb') as fd:
        try:
            return pickle.load(fd, **kwargs)
        except UnicodeDecodeError:
            if 'encoding' in kwargs:
                raise
            return pickle.load(fd, encoding='latin1', **kwargs)


def save_pkl(f, obj, **kwargs):
    with file_descriptor(f, 'wb') as fd:
        return pickle.dump(obj, fd, **kwargs)


def load_npy(f, **kwargs):
    return np.load(f, **kwargs)


def save_npy(f, obj, **kwargs):
    return np.save(f, obj, **kwargs)


def load_npz(f, **kwargs):
    return np.load(f, **kwargs)


def save_npz(f, obj, **kwargs):
    return np.savez(f, obj, **kwargs)


def load_pth(f, **kwargs):
    return torch.load(f, **kwargs)


def save_pth(f, obj, **kwargs):
    return torch.save(obj, f, **kwargs)


load_funcs = {'.txt': load_txt, '.json': load_json, '.pkl': load_pkl,
              '.npy': load_npy, '.npz': load_npz, '.pth': load_pth, '.pth.tar': load_pth}
save_funcs = {'.txt': load_txt, '.json': save_json, '.pkl': save_pkl,
              '.npy': save_npy, '.npz': save_npz, '.pth': save_pth, '.pth.tar': save_pth}


def load(fpath, **kwargs):
    assert isinstance(fpath, str), type(fpath)
    for extension in sorted(load_funcs.keys(), key=len, reverse=True):
        if fpath.endswith(extension):
            return load_funcs[extension](fpath, **kwargs)
    raise NotImplementedError()


def save(fname, obj, **kwargs):
    assert isinstance(fname, str), type(fname)
    for ext in sorted(save_funcs.keys(), key=len, reverse=True):
        if fname.endswith(ext):
            return save_funcs[ext](fname, obj, **kwargs)
    raise NotImplementedError()
