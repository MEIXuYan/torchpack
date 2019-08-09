import torch
import torch.backends.cudnn as cudnn
import torch.nn as nn

from torchpack.callbacks import *
from torchpack.datasets.vision.imagenet import ImageNet
from torchpack.models.vision.mobilenetv2 import MobileNetV2
from torchpack.trainer import Trainer
from torchpack.utils.argument import ArgumentParser
from torchpack.utils.logging import get_logger

logger = get_logger(__file__)


def main():
    parser = ArgumentParser()
    parser.add_argument('--devices', action='set_devices', default='*', help='list of device(s) to use.')
    args = parser.parse_args()

    cudnn.benchmark = True

    logger.info('Loading the dataset.')
    dataset = ImageNet(root='/dataset/imagenet/', num_classes=100, image_size=224)
    loaders = {}
    for split in dataset:
        loaders[split] = torch.utils.data.DataLoader(
            dataset[split],
            shuffle=(split == 'train'),
            batch_size=256,
            num_workers=16,
            pin_memory=True
        )

    logger.info('Building the model.')
    model = MobileNetV2(num_classes=100).cuda()
    model = nn.DataParallel(model)

    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.SGD(model.parameters(), lr=0.05, momentum=0.9, weight_decay=4e-5)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=150)

    trainer = Trainer()
    trainer.train(
        loader=loaders['train'], model=model, criterion=criterion,
        callbacks=[
            LambdaCallback(before_step=lambda _, fd: optimizer.zero_grad(),
                           after_step=lambda _, fd, od: optimizer.step()),
            LambdaCallback(before_epoch=lambda _: scheduler.step()),
            InferenceRunner(loaders['test'], callbacks=[
                ClassificationError(k=1, summary_name='acc/test-top1'),
                ClassificationError(k=5, summary_name='acc/test-top5')
            ]),
            ProgressBar(),
            EstimatedTimeLeft()
        ],
        monitors=[
            # TFEventWriter(),
            ScalarPrinter()
        ],
        max_epoch=150
    )


if __name__ == '__main__':
    main()
