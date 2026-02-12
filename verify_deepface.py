
import sys
import os
import numpy as np
import cv2

print(f"Python: {sys.version}")

try:
    import deepface
    print(f"DeepFace version: {deepface.__version__}")
    from deepface import DeepFace
    print("DeepFace imported successfully.")
except ImportError as e:
    print(f"FAILED to import DeepFace: {e}")
    sys.exit(1)
except Exception as e:
    print(f"Error importing DeepFace: {e}")
    sys.exit(1)

# Create a dummy image (black square) - validation will fail to find a face, but that's expected.
# We just want to ensure the function runs.
img = np.zeros((300, 300, 3), dtype=np.uint8)
cv2.rectangle(img, (100, 100), (200, 200), (255, 255, 255), -1) # Draw a white square

print("Attempting DeepFace.represent on dummy image...")
try:
    # This should raise ValueError because no face is there, confirming it works
    DeepFace.represent(img_path=img, model_name="VGG-Face", detector_backend="opencv", enforce_detection=True)
    print("Unexpectedly found a face in a dummy image!")
except ValueError:
    print("DeepFace.represent threw ValueError as expected (No face detected). Engine is working.")
except Exception as e:
    print(f"DeepFace.represent threw unexpected error: {e}")

print("Verification complete.")
