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
        if not os.path.exists(model_path):
            print(f"Model file not found at {model_path}.")
            return None
        try:
            model = resnet50(pretrained=False)
            model.conv1 = nn.Conv2d(1, 64, kernel_size=7, stride=2, padding=3, bias=False)
            model.fc = nn.Linear(model.fc.in_features, 1)  # Binary classification
            model.load_state_dict(torch.load(model_path, map_location=torch.device('cpu')))
            model.eval()
            print(f"Model loaded successfully from {model_path}")
        except Exception as e:
            print(f"Error loading model: {e}")
            model = None
    return model

def process_medical_image(report):
    """
    Process medical image and return prediction result using PyTorch ResNet model.
    """
    try:
        # Load the model
        model = load_model()
        if model is None:
            raise Exception("Model not loaded. Please check model path and file.")

        # Open the image
        image = Image.open(report.file.path).convert('RGB')

        # Preprocess the image
        transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
        image_tensor = transform(image).unsqueeze(0)

        # Make prediction
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

        return {
            'result': result,
            'confidence': confidence,
            'findings': findings
        }

    except Exception as e:
        print(f"Error processing image: {e}")
        raise



def create_prediction_for_report(report):
    """
    Create a prediction for the given medical report.
    """
    prediction_data = process_medical_image(report)

    prediction = Prediction.objects.create(
        report=report,
        result=prediction_data['result'],
        confidence=prediction_data['confidence'],
        findings=prediction_data['findings']
    )

    return prediction
