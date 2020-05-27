import torch
import torch.nn as nn

__all__ = ['ShuffleNetV2', 'ShuffleBlockV2']


def channel_shuffle(inputs, groups):
    batch_size, num_channels, *sizes = inputs.size()
    inputs = inputs.view(batch_size, groups, num_channels // groups, *sizes)
    inputs = inputs.transpose(1, 2).contiguous()
    inputs = inputs.view(batch_size, num_channels, *sizes)
    return inputs


class ShuffleBlockV2(nn.Module):
    def __init__(self, in_channels, out_channels, kernel_size, *, stride=1):
        super().__init__()
        self.in_channels = in_channels
        self.out_channels = out_channels
        self.kernel_size = kernel_size
        self.stride = stride

        if stride == 1:
            in_channels = in_channels // 2
        out_channels = out_channels // 2

        if stride != 1:
            self.branch1 = nn.Sequential(
                nn.Conv2d(in_channels,
                          in_channels,
                          kernel_size,
                          stride=stride,
                          padding=kernel_size // 2,
                          groups=in_channels,
                          bias=False),
                nn.BatchNorm2d(in_channels),
                nn.Conv2d(in_channels, out_channels, 1, bias=False),
                nn.BatchNorm2d(out_channels),
                nn.ReLU(inplace=True),
            )

        self.branch2 = nn.Sequential(
            nn.Conv2d(in_channels, out_channels, 1, bias=False),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_channels,
                      out_channels,
                      kernel_size,
                      stride=stride,
                      padding=kernel_size // 2,
                      groups=out_channels,
                      bias=False),
            nn.BatchNorm2d(out_channels),
            nn.Conv2d(out_channels, out_channels, 1, bias=False),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),
        )

    def forward(self, x):
        if self.stride != 1:
            x1 = self.branch1(x)
            x2 = self.branch2(x)
        else:
            x1, x2 = torch.chunk(x, 2, dim=1)
            x2 = self.branch2(x2)

        x = torch.cat((x1, x2), dim=1)
        x = channel_shuffle(x, 2)
        return x


class ShuffleNetV2(nn.Module):
    blocks = {
        0.5: [24, (48, 4, 2), (96, 8, 2), (192, 4, 2), 1024],
        1.0: [24, (116, 4, 2), (232, 8, 2), (464, 4, 2), 1024],
        1.5: [24, (176, 4, 2), (352, 8, 2), (704, 4, 2), 1024],
        2.0: [24, (244, 4, 2), (488, 8, 2), (976, 4, 2), 2048]
    }

    def __init__(self, *, in_channels=3, num_classes=1000, width_multiplier=1):
        super().__init__()

        out_channels = self.blocks[width_multiplier][0]
        layers = [
            nn.Sequential(
                nn.Conv2d(in_channels,
                          out_channels,
                          3,
                          stride=2,
                          padding=1,
                          bias=False),
                nn.BatchNorm2d(out_channels),
                nn.ReLU(inplace=True),
            )
        ]
        in_channels = out_channels

        for out_channels, num_blocks, strides in \
                self.blocks[width_multiplier][1:-1]:
            for stride in [strides] + [1] * (num_blocks - 1):
                layers.append(
                    ShuffleBlockV2(in_channels, out_channels, 3,
                                   stride=stride))
                in_channels = out_channels

        out_channels = self.blocks[width_multiplier][-1]
        layers.append(
            nn.Sequential(
                nn.Conv2d(in_channels, out_channels, 1, bias=False),
                nn.BatchNorm2d(out_channels),
                nn.ReLU(inplace=True),
            ))
        in_channels = out_channels

        self.features = nn.Sequential(*layers)
        self.classifier = nn.Linear(in_channels, num_classes)
        self.reset_parameters()

    def reset_parameters(self):
        for m in self.modules():
            if isinstance(m, nn.Conv2d):
                nn.init.kaiming_normal_(m.weight,
                                        mode='fan_out',
                                        nonlinearity='relu')
                if m.bias is not None:
                    nn.init.zeros_(m.bias)
            if isinstance(m, nn.Linear):
                nn.init.normal_(m.weight, std=0.01)
                if m.bias is not None:
                    nn.init.zeros_(m.bias)

    def forward(self, x):
        x = self.features(x)
        x = x.mean([2, 3])
        x = self.classifier(x)
        return x
