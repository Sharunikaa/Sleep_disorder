"""
Configuration management for the Sleep Health FHE Application.
Loads environment variables and provides configuration objects.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Base configuration class."""
    
    # Flask Configuration
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY', os.urandom(24).hex())
    DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    # Firebase Configuration
    FIREBASE_CONFIG = {
        "apiKey": os.getenv('FIREBASE_API_KEY'),
        "authDomain": os.getenv('FIREBASE_AUTH_DOMAIN'),
        "projectId": os.getenv('FIREBASE_PROJECT_ID'),
        "storageBucket": os.getenv('FIREBASE_STORAGE_BUCKET'),
        "messagingSenderId": os.getenv('FIREBASE_MESSAGING_SENDER_ID'),
        "appId": os.getenv('FIREBASE_APP_ID'),
        "databaseURL": ""  # Not needed for auth/storage only
    }
    
    # Firebase Admin SDK
    FIREBASE_SERVICE_ACCOUNT = os.getenv('FIREBASE_SERVICE_ACCOUNT_PATH')
    
    # Model Configuration
    MODEL_PATH = 'models/fhe_model'
    SCALER_PATH = 'models/scaler.pkl'
    METRICS_PATH = 'models/metrics.json'
    
    # Dataset Configuration
    DATASET_PATH = 'data/Sleep_health_and_lifestyle_dataset.csv'
    
    # Feature names (must match dataset columns after preprocessing)
    # These are the numeric features we'll use for prediction
    FEATURE_NAMES = [
        'Age',
        'Sleep Duration',
        'Quality of Sleep',
        'Physical Activity Level',
        'Stress Level',
        'Heart Rate',
        'Daily Steps',
        'Gender_Encoded',
        'BMI_Encoded',
        'BP_Systolic',
        'BP_Diastolic'
    ]
    
    # Raw columns from CSV (before preprocessing)
    RAW_FEATURE_NAMES = [
        'Gender',
        'Age',
        'Sleep Duration',
        'Quality of Sleep',
        'Physical Activity Level',
        'Stress Level',
        'BMI Category',
        'Blood Pressure',
        'Heart Rate',
        'Daily Steps'
    ]
    
    TARGET_NAME = 'Sleep Disorder'
    
    # Label encoding mappings
    GENDER_MAPPING = {'Female': 0, 'Male': 1}
    BMI_MAPPING = {'Normal': 0, 'Normal Weight': 1, 'Obese': 2, 'Overweight': 3}
    TARGET_MAPPING = {'Insomnia': 0, 'No Issues': 1, 'Sleep Apnea': 2}
    TARGET_LABELS = ['Insomnia', 'No Issues', 'Sleep Apnea']
    
    # FHE Configuration
    FHE_N_BITS = 6  # Quantization bits for FHE (start with 6, increase if accuracy too low)
    
    @classmethod
    def validate(cls):
        """Validate that required configuration is present."""
        required_firebase = ['apiKey', 'authDomain', 'projectId', 'storageBucket']
        missing = [k for k in required_firebase if not cls.FIREBASE_CONFIG.get(k)]
        
        if missing:
            print(f"Warning: Missing Firebase config: {', '.join(missing)}")
            print("Please set up .env file with Firebase credentials.")
            return False
        return True


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False


# Default configuration
config = DevelopmentConfig()
