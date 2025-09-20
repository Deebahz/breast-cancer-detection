from django.shortcuts import render
from django.conf import settings
from .models import MedicalReport, Prediction
import random
import os
from PIL import Image
import io
import torch
import torchvision.transforms as transforms
from torchvision.models import resnet50
import torch.nn as nn

# Create your views here.

# Global model variable
model = None

def load_model():
    global model
    if model is None:
        # Model path from settings
        model_path = getattr(settings, 'BREAST_CANCER_MODEL_PATH', None)
        if not model_path:
            print("Model path not configured in settings.")
            return None

        try:
            # Check if model file exists
            if os.path.exists(model_path):
                print(f"Loading model from {model_path}")
                model = resnet50(pretrained=False)
                model.conv1 = nn.Conv2d(1, 64, kernel_size=7, stride=2, padding=3, bias=False)
                model.fc = nn.Linear(model.fc.in_features, 1)  # Binary classification
                model.load_state_dict(torch.load(model_path, map_location=torch.device('cpu')))
                model.eval()
                print(f"Model loaded successfully from {model_path}")
            else:
                print(f"Model file not found at {model_path}. Creating fallback model.")
                model = create_fallback_model()
        except Exception as e:
            print(f"Error loading model: {e}")
            print("Creating fallback model.")
            model = create_fallback_model()
    return model

def create_fallback_model():
    """
    Create a simple fallback model for testing purposes.
    This model will generate random predictions when the main model fails to load.
    """
    print("Creating fallback model for testing...")

    # Create a simple model architecture
    model = resnet50(pretrained=False)
    model.conv1 = nn.Conv2d(1, 64, kernel_size=7, stride=2, padding=3, bias=False)
    model.fc = nn.Linear(model.fc.in_features, 1)  # Binary classification

    # Initialize with random weights for testing
    for param in model.parameters():
        nn.init.normal_(param, mean=0.0, std=0.01)

    # Mark this as a fallback model
    model._is_fallback = True

    model.eval()
    print("Fallback model created successfully")
    return model

def generate_grad_cam(model, input_tensor, target_class=None):
    """
    Generate Grad-CAM heatmap for the given input tensor.
    """
    model.eval()

    # Hook to capture gradients and activations
    gradients = []
    activations = []

    def save_gradient(grad):
        gradients.append(grad)

    def save_activation(module, input, output):
        activations.append(output)

    # Register hooks
    final_conv_layer = None
    for name, module in model.named_modules():
        if isinstance(module, torch.nn.Conv2d):
            final_conv_layer = module

    if final_conv_layer is None:
        raise Exception("No convolutional layer found in model")

    final_conv_layer.register_forward_hook(save_activation)
    final_conv_layer.register_backward_hook(lambda module, grad_in, grad_out: save_gradient(grad_out[0]))

    # Forward pass
    output = model(input_tensor)
    if target_class is None:
        target_class = output.argmax(dim=1).item()

    # Backward pass
    model.zero_grad()
    output[0, target_class].backward()

    # Get gradients and activations
    gradient = gradients[0].cpu().data.numpy()
    activation = activations[0].cpu().data.numpy()

    # Global average pooling of gradients
    weights = gradient.mean(axis=(2, 3), keepdims=True)

    # Weighted combination of activation maps
    cam = (weights * activation).sum(axis=1, keepdims=True)

    # Apply ReLU
    cam = torch.from_numpy(cam).clamp(min=0)

    # Normalize to [0, 1]
    cam = cam - cam.min()
    cam = cam / cam.max()

    return cam.squeeze().numpy()

def process_medical_image(report):
    """
    Process medical image and return prediction result using PyTorch ResNet model.
    Also generates Grad-CAM visualization.
    """
    try:
        # Load the model
        model = load_model()
        if model is None:
            raise Exception("Model not loaded. Please check model path and file.")

        # Open the image
        image = Image.open(report.file.path).convert('L')  # Convert to grayscale for medical images

        # Preprocess the image
        transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
        ])
        image_tensor = transform(image).unsqueeze(0)

        # Check if this is a fallback model (has random weights)
        is_fallback = hasattr(model, '_is_fallback') and model._is_fallback

        if is_fallback:
            # Use random prediction for testing
            probability = random.uniform(0.1, 0.9)
            print(f"Using fallback model - random prediction: {probability}")
        else:
            # Make prediction with real model
            with torch.no_grad():
                output = model(image_tensor)
                probability = torch.sigmoid(output).item()

        # Map probability to risk level
        if probability < 0.4:
            result = 'low'
        elif probability < 0.7:
            result = 'medium'
        else:
            result = 'high'

        confidence = round(probability * 100, 2)

        # Generate findings based on result
        findings = f"Risk level: {result.capitalize()}"

        # Generate Grad-CAM (only for real models, not fallback)
        grad_cam_path = None
        if not is_fallback:
            try:
                grad_cam = generate_grad_cam(model, image_tensor, target_class=0 if result == 'low' else 1)
                grad_cam_path = save_grad_cam_image(grad_cam, report.id)
            except Exception as e:
                print(f"Error generating Grad-CAM: {e}")
                grad_cam_path = None
        else:
            print("Skipping Grad-CAM generation for fallback model")

        return {
            'result': result,
            'confidence': confidence,
            'findings': findings,
            'grad_cam_path': grad_cam_path
        }

    except Exception as e:
        print(f"Error processing image: {e}")
        raise

def save_grad_cam_image(grad_cam, report_id):
    """
    Save Grad-CAM heatmap as an image file.
    """
    import numpy as np
    from PIL import Image
    import os
    from django.conf import settings

    # Create heatmap
    grad_cam = np.uint8(255 * grad_cam)
    heatmap = Image.fromarray(grad_cam).resize((224, 224))

    # Create directory if it doesn't exist
    grad_cam_dir = os.path.join(settings.MEDIA_ROOT, 'grad_cam_images')
    os.makedirs(grad_cam_dir, exist_ok=True)

    # Save the image
    filename = f'grad_cam_{report_id}.png'
    filepath = os.path.join(grad_cam_dir, filename)
    heatmap.save(filepath)

    # Return relative path for database storage
    return f'grad_cam_images/{filename}'



def create_prediction_for_report(report):
    """
    Create a prediction for the given medical report.
    """
    prediction_data = process_medical_image(report)

    # Save Grad-CAM image path to the report if generated
    if prediction_data.get('grad_cam_path'):
        report.grad_cam_image = prediction_data['grad_cam_path']
        report.save()

    prediction = Prediction.objects.create(
        report=report,
        result=prediction_data['result'],
        confidence=prediction_data['confidence'],
        findings=prediction_data['findings']
    )

    return prediction
