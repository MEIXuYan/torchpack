import torchvision.datasets as datasets
from torchvision.transforms import (Compose, Normalize, RandomCrop,
                                    RandomHorizontalFlip, Resize, ToTensor)

from ..dataset import Dataset

__all__ = ['CIFAR']


class CIFAR10Dataset(datasets.CIFAR10):
    def __init__(self,
                 *,
                 root,
                 split,
                 transform=None,
                 target_transform=None,
                 download=True):
        super().__init__(root=root,
                         train=(split == 'train'),
                         transform=transform,
                         target_transform=target_transform,
                         download=download)

    def __getitem__(self, index):
        image, label = super().__getitem__(index)
        return {'image': image, 'class': label}


class CIFAR100Dataset(datasets.CIFAR100):
    def __init__(self,
                 *,
                 root,
                 split,
                 transform=None,
                 target_transform=None,
                 download=True):
        super().__init__(root=root,
                         train=(split == 'train'),
                         transform=transform,
                         target_transform=target_transform,
                         download=download)

    def __getitem__(self, index):
        image, label = super().__getitem__(index)
        return {'image': image, 'class': label}


class CIFAR(Dataset):
    def __init__(self, *, root, num_classes=10, transforms=None):
        if num_classes == 10:
            CIFARDataset = CIFAR10Dataset
        elif num_classes == 100:
            CIFARDataset = CIFAR100Dataset
        else:
            raise NotImplementedError(f'CIFAR-{num_classes} is not supported.')

        if transforms is None:
            transforms = dict()
        if 'train' not in transforms:
            transforms['train'] = Compose([
                RandomCrop(32, padding=4),
                RandomHorizontalFlip(),
                ToTensor(),
                Normalize(mean=[0.4914, 0.4822, 0.4465],
                          std=[0.2023, 0.1994, 0.2010])
            ])
        if 'test' not in transforms:
            transforms['test'] = Compose([
                Resize(32),
                ToTensor(),
                Normalize(mean=[0.4914, 0.4822, 0.4465],
                          std=[0.2023, 0.1994, 0.2010])
            ])

        super().__init__({
            split: CIFARDataset(root=root,
                                split=split,
                                transform=transforms[split])
            for split in ['train', 'test']
        })
