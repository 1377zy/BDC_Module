from app.models.car import Car, CarImage, UserPreference
import sys
import os

# Get the parent directory
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Add parent directory to path so we can import models.py
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# This file makes the models directory a proper Python package
# and allows for importing models from app.models
