"""
Model training and FHE compilation for Sleep Disorder Prediction.
Handles Random Forest model training, FHE compilation, and deployment.
"""

import os
import json
import time
import numpy as np
from pathlib import Path
from typing import Tuple, Optional, Dict
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
import joblib

# Concrete-ML imports
from concrete.ml.sklearn import RandomForestClassifier
from concrete.ml.deployment import FHEModelDev, FHEModelClient, FHEModelServer

from config import config
from preprocess import (
    load_dataset, 
    validate_dataset, 
    clean_dataset, 
    prepare_features,
    split_data,
    scale_features,
    load_scaler
)


class SleepDisorderFHEModel:
    """Wrapper class for Sleep Disorder FHE Model."""
    
    def __init__(self, n_bits: int = 6):
        """
        Initialize the model.
        
        Args:
            n_bits: Number of bits for quantization (lower = faster FHE, higher = better accuracy)
        """
        self.n_bits = n_bits
        self.model = None
        self.scaler = None
        self.metrics = {}
        
    def train(
        self, 
        X_train: np.ndarray, 
        y_train: np.ndarray,
        X_test: np.ndarray,
        y_test: np.ndarray
    ) -> Dict:
        """
        Train the XGBoost model.
        
        Args:
            X_train: Training features (scaled)
            y_train: Training labels
            X_test: Testing features (scaled)
            y_test: Testing labels
            
        Returns:
            Dictionary with training metrics
        """
        print(f"\n{'='*60}")
        print("Training Random Forest Model for FHE")
        print(f"{'='*60}")
        print(f"n_bits: {self.n_bits}")
        print(f"Training samples: {X_train.shape[0]}")
        print(f"Features: {X_train.shape[1]}")
        
        # Initialize Concrete-ML Random Forest classifier
        self.model = RandomForestClassifier(
            n_bits=self.n_bits,
            n_estimators=10,  
            max_depth=5,      
            random_state=42,
            n_jobs=1          
        )
        
        # Train the model
        start_time = time.time()
        self.model.fit(X_train, y_train)
        training_time = time.time() - start_time
        
        print(f"Training completed in {training_time:.2f} seconds")
        
        # Evaluate on test set (plaintext)
        y_pred = self.model.predict(X_test)
        
        metrics = {
            'accuracy': float(accuracy_score(y_test, y_pred)),
            'precision': float(precision_score(y_test, y_pred, average='weighted', zero_division=0)),
            'recall': float(recall_score(y_test, y_pred, average='weighted', zero_division=0)),
            'f1': float(f1_score(y_test, y_pred, average='weighted', zero_division=0)),
            'training_time': training_time
        }
        
        # Confusion matrix
        cm = confusion_matrix(y_test, y_pred)
        metrics['confusion_matrix'] = cm.tolist()
        
        print(f"\nPlaintext Model Performance:")
        print(f"  Accuracy:  {metrics['accuracy']:.4f}")
        print(f"  Precision: {metrics['precision']:.4f}")
        print(f"  Recall:    {metrics['recall']:.4f}")
        print(f"  F1 Score:  {metrics['f1']:.4f}")
        print(f"\nConfusion Matrix:")
        print(cm)
        
        self.metrics['plaintext'] = metrics
        return metrics
    
    def compile_fhe(self, X_sample: np.ndarray) -> Dict:
        """
        Compile the model for FHE execution.
        
        Args:
            X_sample: Representative sample for compilation (e.g., first 100 training samples)
            
        Returns:
            Dictionary with compilation metrics
        """
        print(f"\n{'='*60}")
        print("Compiling Model for FHE")
        print(f"{'='*60}")
        print(f"Sample size for compilation: {X_sample.shape[0]}")
        
        start_time = time.time()
        
        # Compile the model
        self.model.compile(X_sample)
        
        compilation_time = time.time() - start_time
        
        print(f"FHE compilation completed in {compilation_time:.2f} seconds")
        
        # Get circuit information
        try:
            circuit = self.model.fhe_circuit
            print(f"\nFHE Circuit Information:")
            print(f"  Graph: {circuit.graph if hasattr(circuit, 'graph') else 'N/A'}")
            print(f"  Complexity: {circuit.complexity if hasattr(circuit, 'complexity') else 'N/A'}")
        except Exception as e:
            print(f"Could not retrieve circuit info: {e}")
        
        metrics = {
            'compilation_time': compilation_time,
            'n_bits': self.n_bits
        }
        
        self.metrics['compilation'] = metrics
        return metrics
    
    def evaluate_fhe(
        self, 
        X_test: np.ndarray, 
        y_test: np.ndarray,
        num_samples: int = 10
    ) -> Dict:
        """
        Evaluate model performance with FHE execution.
        
        Args:
            X_test: Test features (scaled)
            y_test: Test labels
            num_samples: Number of samples to test (FHE is slow, so use small sample)
            
        Returns:
            Dictionary with FHE evaluation metrics
        """
        print(f"\n{'='*60}")
        print("Evaluating FHE Model Performance")
        print(f"{'='*60}")
        print(f"Testing {num_samples} samples with FHE...")
        
        # Use only a subset for FHE evaluation (it's very slow)
        X_test_sample = X_test[:num_samples]
        y_test_sample = y_test[:num_samples]
        
        latencies = []
        predictions = []
        
        for i, x in enumerate(X_test_sample):
            start_time = time.time()
            # Predict with FHE
            y_pred = self.model.predict(x.reshape(1, -1), fhe="execute")
            latency = time.time() - start_time
            
            latencies.append(latency)
            predictions.append(y_pred[0])
            
            print(f"  Sample {i+1}/{num_samples}: {latency:.2f}s")
        
        predictions = np.array(predictions)
        
        # Calculate metrics
        accuracy = float(accuracy_score(y_test_sample, predictions))
        avg_latency = float(np.mean(latencies))
        
        # Compare with plaintext latency
        start_time = time.time()
        _ = self.model.predict(X_test_sample, fhe="disable")
        plaintext_latency = (time.time() - start_time) / num_samples
        
        overhead_factor = avg_latency / plaintext_latency if plaintext_latency > 0 else 0
        
        metrics = {
            'accuracy': accuracy,
            'avg_latency_seconds': avg_latency,
            'plaintext_latency_seconds': plaintext_latency,
            'overhead_factor': overhead_factor,
            'num_samples_tested': num_samples
        }
        
        print(f"\nFHE Model Performance:")
        print(f"  Accuracy:           {accuracy:.4f}")
        print(f"  Avg FHE Latency:    {avg_latency:.2f}s")
        print(f"  Plaintext Latency:  {plaintext_latency:.4f}s")
        print(f"  Overhead Factor:    {overhead_factor:.1f}x")
        
        self.metrics['fhe'] = metrics
        return metrics
    
    def save(self, model_dir: Optional[str] = None):
        """
        Save the compiled FHE model for deployment.
        
        Args:
            model_dir: Directory to save model. If None, uses config.MODEL_PATH
        """
        if model_dir is None:
            model_dir = config.MODEL_PATH
        
        print(f"\n{'='*60}")
        print("Saving FHE Model")
        print(f"{'='*60}")
        
        # Remove existing model directory if it exists
        model_path = Path(model_dir)
        if model_path.exists():
            print(f"Removing existing model at {model_dir}...")
            import shutil
            shutil.rmtree(model_path)
        
        # Create fresh directory
        model_path.mkdir(parents=True, exist_ok=True)
        
        # Save using FHEModelDev
        dev = FHEModelDev(model_dir, self.model)
        dev.save()
        
        print(f"FHE circuit saved to {model_dir}")
        
        # Save the trained model separately (for evaluation)
        # Note: We save the underlying sklearn model, not the Concrete-ML wrapper
        # because Concrete-ML models with FHE circuits cannot be pickled
        model_pkl_path = os.path.join(model_dir, 'model.pkl')
        try:
            # Try to save the underlying sklearn model if available
            if hasattr(self.model, 'sklearn_model'):
                joblib.dump(self.model.sklearn_model, model_pkl_path)
                print(f"Trained sklearn model saved to {model_pkl_path}")
            else:
                # For Concrete-ML models, save the model itself (will work for inference)
                # The FHE circuit is already saved by FHEModelDev
                print(f"Concrete-ML model cannot be pickled directly")
                print(f"   FHE circuit saved to {model_dir} (use FHEModelServer to load)")
                # Create a placeholder file so evaluate_fhe.py knows the model exists
                with open(model_pkl_path, 'w') as f:
                    f.write("# Concrete-ML model - use FHEModelServer to load\n")
                print(f"Placeholder created at {model_pkl_path}")
        except Exception as e:
            print(f"Could not save model.pkl: {e}")
            print(f"   FHE circuit is saved and can be loaded with FHEModelServer")
        
        # Save scaler
        scaler_path = config.SCALER_PATH
        if self.scaler is not None:
            joblib.dump(self.scaler, scaler_path)
            print(f"Scaler saved to {scaler_path}")
        
        # Save metrics
        metrics_path = config.METRICS_PATH
        with open(metrics_path, 'w') as f:
            json.dump(self.metrics, f, indent=2)
        print(f"Metrics saved to {metrics_path}")
    
    @classmethod
    def load(cls, model_dir: Optional[str] = None) -> 'HairLossFHEModel':
        """
        Load a saved FHE model.
        
        Args:
            model_dir: Directory containing the model. If None, uses config.MODEL_PATH
            
        Returns:
            Loaded HairLossFHEModel instance
        """
        if model_dir is None:
            model_dir = config.MODEL_PATH
        
        print(f"Loading FHE model from {model_dir}...")
        
        # This would be used for loading, but for server deployment,
        # we use FHEModelServer directly (see load_fhe_model_server function)
        instance = cls()
        
        # Load metrics if available
        try:
            with open(config.METRICS_PATH, 'r') as f:
                instance.metrics = json.load(f)
            print("Metrics loaded successfully")
        except FileNotFoundError:
            print("No metrics file found")
        
        return instance


def train_and_compile(
    evaluate_fhe: bool = True,
    num_fhe_samples: int = 10
) -> SleepDisorderFHEModel:
    """
    Complete pipeline: load data, train model, compile for FHE, and save.
    
    Args:
        evaluate_fhe: Whether to evaluate FHE performance (slow)
        num_fhe_samples: Number of samples to test with FHE
        
    Returns:
        Trained and compiled SleepDisorderFHEModel
    """
    print(f"\n{'='*60}")
    print("SLEEP DISORDER FHE MODEL - TRAINING PIPELINE")
    print(f"{'='*60}\n")
    
    # Step 1: Load and preprocess data
    print("Step 1: Loading and preprocessing data...")
    df = load_dataset()
    validate_dataset(df)
    df_clean = clean_dataset(df)
    
    X, y = prepare_features(df_clean)
    X_train, X_test, y_train, y_test = split_data(X, y)
    X_train_scaled, X_test_scaled, scaler = scale_features(X_train, X_test)
    
    # Step 2: Train model
    print("\nStep 2: Training model...")
    model = SleepDisorderFHEModel(n_bits=config.FHE_N_BITS)
    model.train(X_train_scaled, y_train, X_test_scaled, y_test)
    model.scaler = scaler
    
    # Step 3: Compile for FHE
    print("\nStep 3: Compiling for FHE...")
    # Use first 50 samples for compilation (smaller sample to avoid segfault)
    compilation_sample = X_train_scaled[:min(50, len(X_train_scaled))]
    model.compile_fhe(compilation_sample)
    
    # Step 4: Evaluate FHE (optional, slow)
    if evaluate_fhe:
        print("\nStep 4: Evaluating FHE performance...")
        print("Warning: This will be slow! Testing only a few samples.")
        try:
            model.evaluate_fhe(X_test_scaled, y_test, num_samples=num_fhe_samples)
        except KeyboardInterrupt:
            print("\nFHE evaluation interrupted by user. Saving model anyway...")
        except Exception as e:
            print(f"\nFHE evaluation failed: {e}. Saving model anyway...")
    else:
        print("\nStep 4: Skipping FHE evaluation (use --evaluate-fhe to enable)")
    
    # Step 5: Save model
    print("\nStep 5: Saving model...")
    model.save()
    
    print(f"\n{'='*60}")
    print("TRAINING PIPELINE COMPLETED SUCCESSFULLY!")
    print(f"{'='*60}\n")
    
    return model


def load_fhe_model_server(model_dir: Optional[str] = None) -> FHEModelServer:
    """
    Load FHE model for server-side inference.
    
    Args:
        model_dir: Directory containing the model. If None, uses config.MODEL_PATH
        
    Returns:
        FHEModelServer instance ready for encrypted inference
    """
    if model_dir is None:
        model_dir = config.MODEL_PATH
    
    if not os.path.exists(model_dir):
        raise FileNotFoundError(
            f"FHE model not found at {model_dir}. "
            f"Please run 'python model.py' to train and compile the model first."
        )
    
    print(f"Loading FHE model server from {model_dir}...")
    server = FHEModelServer(model_dir)
    print("FHE model server loaded successfully!")
    
    return server


def load_metrics() -> Dict:
    """
    Load saved model metrics.
    
    Returns:
        Dictionary with model metrics
    """
    try:
        with open(config.METRICS_PATH, 'r') as f:
            metrics = json.load(f)
        return metrics
    except FileNotFoundError:
        return {
            'plaintext': {'accuracy': 0.0},
            'fhe': {'accuracy': 0.0, 'avg_latency_seconds': 0.0}
        }


if __name__ == "__main__":
    """
    Run this script to train and compile the model.
    
    Usage:
        python model.py                    # Train with FHE evaluation (default)
        python model.py --skip-fhe         # Train without FHE evaluation (faster)
    """
    import sys
    
    skip_fhe = '--skip-fhe' in sys.argv
    evaluate_fhe = not skip_fhe
    num_samples = 0 if skip_fhe else 10
    
    try:
        model = train_and_compile(
            evaluate_fhe=evaluate_fhe,
            num_fhe_samples=num_samples
        )
                
    except FileNotFoundError as e:
        print(f"\n Error: {e}")
        print(f"\nPlease ensure your dataset is at: {config.DATASET_PATH}")
    except Exception as e:
        print(f"\nError during training: {e}")
        import traceback
        traceback.print_exc()
