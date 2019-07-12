import numpy as np
import torch.nn as nn

__all__ = ['flops_handlers']


def conv(module, inputs, outputs):
    kernel_size = module.weight.size()
    output_size = outputs.size()
    return np.prod([output_size[0]] + list(output_size[2:]) + list(kernel_size))


def gemm(module, inputs, outputs):
    kernel_size = module.weight.size()
    output_size = outputs.size()
    return np.prod([output_size[0]] + list(kernel_size))


flops_handlers = [
    ((nn.Conv1d, nn.Conv2d, nn.Conv3d), conv),
    ((nn.ConvTranspose1d, nn.ConvTranspose2d, nn.ConvTranspose3d), conv),
    (nn.Linear, gemm)
]
