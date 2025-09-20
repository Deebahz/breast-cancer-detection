import torch
import torch.nn as nn
from torchvision.models import resnet50
import os

def create_local_model():
    """
    Create a local ResNet50 model compatible with the breast cancer detection system.
    The model will be configured for 1-channel input (grayscale medical images).
    """
    print("Creating local model for breast cancer detection...")

    # Create the model with the same architecture as used in core/views.py
    model = resnet50(pretrained=False)

    # Modify first conv layer for 1-channel input (grayscale)
    model.conv1 = nn.Conv2d(1, 64, kernel_size=7, stride=2, padding=3, bias=False)

    # Modify final layer for binary classification
    model.fc = nn.Linear(model.fc.in_features, 1)

    # Put model in evaluation mode
    model.eval()

    # Create models directory if it doesn't exist
    model_dir = os.path.join(os.path.dirname(__file__), 'models')
    os.makedirs(model_dir, exist_ok=True)

    # Save the model
    model_path = os.path.join(model_dir, 'breast_cancer_model.pth')
    torch.save(model.state_dict(), model_path)

    print(f"Local model created and saved to: {model_path}")
    print("Model architecture:")
    print(f"- Input channels: 1 (grayscale)")
    print(f"- Output classes: 1 (binary classification)")
    print(f"- Modified layers: conv1, fc")

    return model_path

if __name__ == "__main__":
    create_local_model()
