from setuptools import find_packages, setup

from torchpack import __version__

setup(
    name='torchpack',
    version=__version__,
    packages=find_packages(exclude=['examples']),
    install_requires=[
        'loguru>=0.5.1',
        'numpy>=1.14',
        'pyyaml',
        'termcolor>=1.1',
        'torch>=1.4',
        'torchvision>=0.5',
        'tqdm>=4.31.0',
    ],
    url='https://github.com/zhijian-liu/torchpack',
)
