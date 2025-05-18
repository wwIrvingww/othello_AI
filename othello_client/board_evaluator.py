import torch
import torch.nn as nn

class ResidualBlock(nn.Module):
    """
    Bloque residual tipo ResNet:
    Conv(3x3) → BatchNorm → ReLU → Conv(3x3) → BatchNorm + Skip → ReLU
    """
    def __init__(self, in_channels, out_channels, stride=1):
        super(ResidualBlock, self).__init__()
        self.conv1 = nn.Conv2d(in_channels, out_channels, kernel_size=3, stride=stride, padding=1, bias=False)
        self.bn1 = nn.BatchNorm2d(out_channels)
        self.relu = nn.ReLU(inplace=True)
        self.conv2 = nn.Conv2d(out_channels, out_channels, kernel_size=3, stride=1, padding=1, bias=False)
        self.bn2 = nn.BatchNorm2d(out_channels)

        # Ajuste del skip si cambia dimensión
        self.downsample = None
        if stride != 1 or in_channels != out_channels:
            self.downsample = nn.Sequential(
                nn.Conv2d(in_channels, out_channels, kernel_size=1, stride=stride, bias=False),
                nn.BatchNorm2d(out_channels)
            )

    def forward(self, x):
        identity = x
        out = self.conv1(x)
        out = self.bn1(out)
        out = self.relu(out)

        out = self.conv2(out)
        out = self.bn2(out)

        if self.downsample is not None:
            identity = self.downsample(x)

        out += identity
        out = self.relu(out)
        return out

class BoardEvaluator(nn.Module):
    """
    Modelo CNN mejorado con bloques residuales, BatchNorm y GlobalAvgPool.

    - Input: tensor [N, 3, 8, 8]
    - Conv inicial 3→64
    - ResidualBlock(64→64)
    - ResidualBlock(64→128, stride=2)
    - AdaptiveAvgPool2d(1x1)
    - FC(128→256) + ReLU + Dropout
    - FC(256→1) + Tanh
    """
    def __init__(self):
        super(BoardEvaluator, self).__init__()
        self.conv = nn.Conv2d(3, 64, kernel_size=3, stride=1, padding=1, bias=False)
        self.bn = nn.BatchNorm2d(64)
        self.relu = nn.ReLU(inplace=True)

        self.layer1 = ResidualBlock(64, 64, stride=1)
        self.layer2 = ResidualBlock(64, 128, stride=2)

        self.global_pool = nn.AdaptiveAvgPool2d((1, 1))
        self.fc1 = nn.Linear(128, 256)
        self.dropout = nn.Dropout(p=0.5)
        self.fc2 = nn.Linear(256, 1)
        self.tanh = nn.Tanh()

    def forward(self, x):
        # x: [N,3,8,8]
        x = self.conv(x)
        x = self.bn(x)
        x = self.relu(x)

        x = self.layer1(x)
        x = self.layer2(x)

        x = self.global_pool(x)      # → [N,128,1,1]
        x = torch.flatten(x, 1)      # → [N,128]

        x = self.fc1(x)
        x = self.relu(x)
        x = self.dropout(x)

        x = self.fc2(x)
        x = self.tanh(x)             # Salida [-1,1]
        return x
