"""
Data preprocessing utilities for the Sleep Health FHE Application.
Handles data loading, cleaning, and feature engineering.
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
from typing import Tuple, Optional
import joblib
from config import config


def load_dataset(filepath: Optional[str] = None) -> pd.DataFrame:
    """
    Load the sleep health dataset from CSV.
    
    Args:
        filepath: Path to CSV file. If None, uses config.DATASET_PATH
        
    Returns:
        DataFrame with the dataset
        
    Raises:
        FileNotFoundError: If dataset file doesn't exist
    """
    if filepath is None:
        filepath = config.DATASET_PATH
    
    try:
        df = pd.read_csv(filepath)
        print(f"Dataset loaded successfully: {df.shape[0]} rows, {df.shape[1]} columns")
        return df
    except FileNotFoundError:
        raise FileNotFoundError(
            f"Dataset not found at {filepath}. "
            f"Please place your Sleep_health_and_lifestyle_dataset.csv file in the data/ folder."
        )


def validate_dataset(df: pd.DataFrame) -> bool:
    """
    Validate that the dataset has required columns and proper format.
    
    Args:
        df: DataFrame to validate
        
    Returns:
        True if valid, raises ValueError otherwise
    """
    # For Sleep Health dataset, check original columns before encoding
    required_original_columns = [
        'Gender', 'Age', 'Sleep Duration', 'Quality of Sleep',
        'Physical Activity Level', 'Stress Level', 'BMI Category',
        'Blood Pressure', 'Heart Rate', 'Daily Steps', 'Sleep Disorder'
    ]
    
    missing_columns = [col for col in required_original_columns if col not in df.columns]
    
    if missing_columns:
        raise ValueError(
            f"Dataset missing required columns: {', '.join(missing_columns)}\n"
            f"Expected columns: {', '.join(required_original_columns)}"
        )
    
    # Check for missing values in target
    target_missing = df[config.TARGET_NAME].isnull().sum()
    if target_missing > 0:
        print(f"Warning: {target_missing} missing values in target column '{config.TARGET_NAME}'")
    
    print("Dataset validation passed!")
    return True


def clean_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean the Sleep Health dataset by handling missing values and encoding categorical features.
    
    Args:
        df: Raw DataFrame
        
    Returns:
        Cleaned DataFrame with encoded features
    """
    df_clean = df.copy()
    
    # Handle missing target values - treat NaN as "No Issues"
    initial_nulls = df_clean[config.TARGET_NAME].isnull().sum()
    if initial_nulls > 0:
        df_clean[config.TARGET_NAME].fillna('No Issues', inplace=True)
        print(f"Filled {initial_nulls} missing target values with 'No Issues'")
    
    # Encode Gender
    le_gender = LabelEncoder()
    df_clean['Gender_Encoded'] = le_gender.fit_transform(df_clean['Gender'])
    print(f"Gender encoded: {dict(enumerate(le_gender.classes_))}")
    
    # Encode BMI Category
    le_bmi = LabelEncoder()
    df_clean['BMI_Encoded'] = le_bmi.fit_transform(df_clean['BMI Category'])
    print(f"BMI Category encoded: {dict(enumerate(le_bmi.classes_))}")
    
    # Parse Blood Pressure into Systolic and Diastolic
    df_clean[['BP_Systolic', 'BP_Diastolic']] = df_clean['Blood Pressure'].str.split('/', expand=True).astype(int)
    print("Blood Pressure split into Systolic and Diastolic")
    
    # Encode target variable
    le_target = LabelEncoder()
    df_clean['Sleep_Disorder_Encoded'] = le_target.fit_transform(df_clean[config.TARGET_NAME])
    print(f"Target encoded: {dict(enumerate(le_target.classes_))}")
    
    # Remove duplicates
    initial_rows = len(df_clean)
    df_clean.drop_duplicates(inplace=True)
    removed_rows = initial_rows - len(df_clean)
    if removed_rows > 0:
        print(f"Removed {removed_rows} duplicate rows")
    
    print(f"Dataset cleaned: {len(df_clean)} rows remaining")
    
    # Save encoders for later use
    joblib.dump(le_gender, 'models/gender_encoder.pkl')
    joblib.dump(le_bmi, 'models/bmi_encoder.pkl')
    joblib.dump(le_target, 'models/target_encoder.pkl')
    print("Encoders saved to models/")
    
    return df_clean


def prepare_features(df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
    """
    Prepare features and target for model training.
    
    Args:
        df: Cleaned DataFrame (with encoded features)
        
    Returns:
        Tuple of (X, y) where X is features array and y is target array
    """
    X = df[config.FEATURE_NAMES].values
    y = df['Sleep_Disorder_Encoded'].values  # Use encoded target
    
    print(f"Features shape: {X.shape}")
    print(f"Target shape: {y.shape}")
    print(f"Target distribution: {np.bincount(y.astype(int))}")
    
    return X, y


def split_data(
    X: np.ndarray, 
    y: np.ndarray, 
    test_size: float = 0.2, 
    random_state: int = 42
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Split data into training and testing sets.
    
    Args:
        X: Feature array
        y: Target array
        test_size: Proportion of data for testing
        random_state: Random seed for reproducibility
        
    Returns:
        Tuple of (X_train, X_test, y_train, y_test)
    """
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=y
    )
    
    print(f"Training set: {X_train.shape[0]} samples")
    print(f"Testing set: {X_test.shape[0]} samples")
    
    return X_train, X_test, y_train, y_test


def scale_features(
    X_train: np.ndarray, 
    X_test: np.ndarray,
    save_path: Optional[str] = None
) -> Tuple[np.ndarray, np.ndarray, StandardScaler]:
    """
    Scale features using StandardScaler.
    
    Args:
        X_train: Training features
        X_test: Testing features
        save_path: Path to save the scaler. If None, uses config.SCALER_PATH
        
    Returns:
        Tuple of (X_train_scaled, X_test_scaled, scaler)
    """
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    print("Features scaled using StandardScaler")
    print(f"Mean: {scaler.mean_}")
    print(f"Std: {scaler.scale_}")
    
    # Save scaler for later use
    if save_path is None:
        save_path = config.SCALER_PATH
    
    joblib.dump(scaler, save_path)
    print(f"Scaler saved to {save_path}")
    
    return X_train_scaled, X_test_scaled, scaler


def load_scaler(filepath: Optional[str] = None) -> StandardScaler:
    """
    Load a saved scaler from disk.
    
    Args:
        filepath: Path to scaler file. If None, uses config.SCALER_PATH
        
    Returns:
        Loaded StandardScaler object
    """
    if filepath is None:
        filepath = config.SCALER_PATH
    
    scaler = joblib.load(filepath)
    print(f"Scaler loaded from {filepath}")
    return scaler


def preprocess_single_input(
    input_data: dict,
    scaler: Optional[StandardScaler] = None
) -> np.ndarray:
    """
    Preprocess a single input for prediction.
    
    Args:
        input_data: Dictionary with feature names as keys
        scaler: StandardScaler object. If None, loads from config.SCALER_PATH
        
    Returns:
        Scaled feature array ready for prediction
    """
    if scaler is None:
        scaler = load_scaler()
    
    # Ensure features are in correct order
    features = [input_data.get(name, 0.0) for name in config.FEATURE_NAMES]
    X = np.array(features).reshape(1, -1)
    
    # Scale
    X_scaled = scaler.transform(X)
    
    return X_scaled


def get_feature_statistics(df: pd.DataFrame) -> dict:
    """
    Calculate statistics for each feature.
    
    Args:
        df: DataFrame with features
        
    Returns:
        Dictionary with feature statistics
    """
    stats = {}
    for feature in config.FEATURE_NAMES:
        stats[feature] = {
            'mean': float(df[feature].mean()),
            'std': float(df[feature].std()),
            'min': float(df[feature].min()),
            'max': float(df[feature].max()),
            'median': float(df[feature].median())
        }
    
    return stats


if __name__ == "__main__":
    """Test preprocessing pipeline."""
    print("Testing preprocessing pipeline...")
    
    # Load and validate
    df = load_dataset()
    validate_dataset(df)
    
    # Clean
    df_clean = clean_dataset(df)
    
    # Prepare features
    X, y = prepare_features(df_clean)
    
    # Split
    X_train, X_test, y_train, y_test = split_data(X, y)
    
    # Scale
    X_train_scaled, X_test_scaled, scaler = scale_features(X_train, X_test)
    
    # Get statistics
    stats = get_feature_statistics(df_clean)
    print("\nFeature Statistics:")
    for feature, stat in stats.items():
        print(f"{feature}: mean={stat['mean']:.2f}, std={stat['std']:.2f}")
    
    print("\nPreprocessing pipeline test completed successfully!")
