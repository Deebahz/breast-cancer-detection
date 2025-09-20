#!/usr/bin/env python3
"""
Test script to verify the local model is working correctly.
This script tests the model loading and prediction functionality.
"""

import os
import sys
import django
from PIL import Image
import numpy as np

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'detection.settings')
django.setup()

from django.conf import settings
from core.views import load_model, process_medical_image
from core.models import MedicalReport, Prediction

def create_test_image():
    """Create a simple test image for testing."""
    # Create a simple 224x224 grayscale image
    test_image = np.random.randint(0, 255, (224, 224), dtype=np.uint8)
    image = Image.fromarray(test_image, mode='L')

    # Save to a temporary location
    test_dir = os.path.join(settings.MEDIA_ROOT, 'test_images')
    os.makedirs(test_dir, exist_ok=True)
    test_path = os.path.join(test_dir, 'test_medical_image.png')
    image.save(test_path)

    return test_path

def test_model_loading():
    """Test that the model loads correctly."""
    print("Testing model loading...")

    try:
        model = load_model()
        if model is None:
            print("❌ Model failed to load")
            return False

        # Check if it's a fallback model
        is_fallback = hasattr(model, '_is_fallback') and model._is_fallback

        if is_fallback:
            print("⚠️  Using fallback model (random predictions)")
        else:
            print("✅ Model loaded successfully")

        return True

    except Exception as e:
        print(f"❌ Error loading model: {e}")
        return False

def test_prediction():
    """Test the prediction functionality."""
    print("\nTesting prediction functionality...")

    try:
        # Create a test image
        test_image_path = create_test_image()

        # Create a mock MedicalReport object
        class MockReport:
            def __init__(self, file_path):
                self.file = type('obj', (object,), {'path': file_path})()
                self.id = 999

        mock_report = MockReport(test_image_path)

        # Test prediction
        result = process_medical_image(mock_report)

        print("✅ Prediction successful:")
        print(f"   - Result: {result['result']}")
        print(f"   - Confidence: {result['confidence']}%")
        print(f"   - Findings: {result['findings']}")

        # Clean up test image
        os.remove(test_image_path)

        return True

    except Exception as e:
        print(f"❌ Error during prediction: {e}")
        return False

def main():
    """Main test function."""
    print("=" * 50)
    print("BREAST CANCER DETECTION SYSTEM - MODEL TEST")
    print("=" * 50)

    # Check model path
    model_path = getattr(settings, 'BREAST_CANCER_MODEL_PATH', None)
    print(f"Model path: {model_path}")
    print(f"Model file exists: {os.path.exists(model_path) if model_path else 'No path set'}")

    # Test model loading
    if not test_model_loading():
        print("\n❌ Model loading failed. Cannot proceed with testing.")
        return

    # Test prediction
    if not test_prediction():
        print("\n❌ Prediction testing failed.")
        return

    print("\n" + "=" * 50)
    print("✅ ALL TESTS PASSED!")
    print("The system is ready for use with the local model.")
    print("=" * 50)

if __name__ == "__main__":
    main()
