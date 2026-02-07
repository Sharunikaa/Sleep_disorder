# Sleep Disorder Prediction with Fully Homomorphic Encryption (FHE)

A privacy-preserving web application for sleep disorder prediction using Fully Homomorphic Encryption (FHE) with Concrete-ML, Flask, and Firebase.

## Overview

This application demonstrates how to build a privacy-first machine learning system where predictions are made on encrypted data. Users can input their health and lifestyle metrics, and the system predicts sleep disorder risk (Insomnia, Sleep Apnea, or No Issues) without ever exposing their sensitive information to the server.

### Key Features

- **Privacy-Preserving Predictions**: Uses Fully Homomorphic Encryption (FHE) to process encrypted data
- **Secure Authentication**: Firebase-based user authentication
- **Modern UI**: Responsive Bootstrap 5 interface
- **Comprehensive Analytics**: Detailed performance metrics and privacy analysis
- **Production-Ready**: Clean architecture with proper error handling

## Architecture

```
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│   Client    │────────▶│ Flask Server │────────▶│   Firebase  │
│  (Browser)  │◀────────│   (Python)   │◀────────│    (Auth)   │
└─────────────┘         └──────────────┘         └─────────────┘
      │                        │
      │                        │
      ▼                        ▼
┌─────────────┐         ┌──────────────┐
│  Encrypted  │         │  FHE Model   │
│    Data     │         │ (Concrete-ML)│
└─────────────┘         └──────────────┘
```

## Technology Stack

- **Backend**: Flask 3.0.3
- **ML Framework**: Concrete-ML 1.5.0 (FHE)
- **Model**: XGBoost Classifier
- **Authentication**: Firebase Auth
- **Frontend**: Bootstrap 5, Vanilla JavaScript
- **Data Processing**: Pandas, NumPy, Scikit-learn

## Prerequisites

- Python 3.9 or higher
- pip (Python package manager)
- Firebase account (for authentication)
- 4GB+ RAM (for FHE operations)
- Sleep Health and Lifestyle Dataset

## Installation

### 1. Clone the Repository

```bash
cd /Users/Sharunikaa/Desktop/Clg/Alopecia_veil
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Up Firebase

Follow the detailed instructions in [FIREBASE_SETUP.md](FIREBASE_SETUP.md) to:
- Create a Firebase project
- Enable Email/Password authentication
- Get your Firebase configuration
- Download service account key

### 5. Configure Environment Variables

```bash
cp .env.example .env
```

Edit `.env` and fill in your Firebase credentials:

```env
FIREBASE_API_KEY=your_api_key_here
FIREBASE_AUTH_DOMAIN=your_project.firebaseapp.com
FIREBASE_PROJECT_ID=your_project_id
FIREBASE_STORAGE_BUCKET=your_project.appspot.com
FIREBASE_MESSAGING_SENDER_ID=your_sender_id
FIREBASE_APP_ID=your_app_id

FIREBASE_SERVICE_ACCOUNT_PATH=serviceAccountKey.json

FLASK_SECRET_KEY=your_secret_key_here
FLASK_ENV=development
FLASK_DEBUG=True
```

### 6. Prepare Dataset

Place your Kaggle hair loss dataset in the `data/` folder:

```bash
# Download from Kaggle and place as:
data/hair_loss.csv
```

The dataset should have these columns:
- `total_protein`
- `total_keratine`
- `vitamin_A`
- `vitamin_E`
- `vitamin_D`
- `vitamin_B`
- `hemoglobin`
- `iron`
- `BMI`
- `stress_level`
- `Sleep Disorder` (target variable: Insomnia, Sleep Apnea, No Issues)

## Usage

### Step 1: Train the Model

Train and compile the FHE model:

```bash
python model.py
```

This will:
- Load and preprocess the dataset
- Train an XGBoost classifier
- Compile the model for FHE
- Save model artifacts to `models/fhe_model/`
- Generate performance metrics

**Note**: Compilation takes 5-10 minutes. Be patient!

For FHE evaluation (slower):

```bash
python model.py --evaluate-fhe
```

### Step 2: Run the Application

```bash
python app.py
```

The application will start at `http://localhost:5000`

### Step 3: Use the Application

1. **Register**: Create an account at `/register`
2. **Login**: Sign in at `/login`
3. **Predict**: Enter health metrics at `/predict`
4. **Report**: View analytics at `/report`

## Project Structure

```
Alopecia_veil/
├── app.py                    # Main Flask application
├── model.py                  # ML training & FHE compilation
├── preprocess.py             # Data preprocessing utilities
├── config.py                 # Configuration management
├── requirements.txt          # Python dependencies
├── .env.example              # Environment variables template
├── .gitignore               # Git ignore patterns
├── README.md                # This file
├── FIREBASE_SETUP.md        # Firebase setup guide
├── templates/               # HTML templates
│   ├── base.html           # Base template
│   ├── login.html          # Login page
│   ├── register.html       # Registration page
│   ├── predict.html        # Prediction form
│   ├── report.html         # Analytics dashboard
│   ├── 404.html            # 404 error page
│   └── 500.html            # 500 error page
├── static/                  # Static assets
│   ├── css/
│   │   └── style.css       # Custom styles
│   └── js/
│       └── predict.js      # Client-side logic
├── models/                  # Model artifacts
│   ├── fhe_model/          # Compiled FHE model
│   ├── scaler.pkl          # Feature scaler
│   └── metrics.json        # Performance metrics
└── data/                    # Dataset
    └── hair_loss.csv       # Kaggle dataset
```

## Features in Detail

### 1. Privacy-Preserving Predictions

The application uses Fully Homomorphic Encryption (FHE) to ensure that:
- User data is encrypted before processing
- Predictions are made on encrypted data
- The server never sees plaintext health information
- Results are returned in encrypted form

### 2. User Authentication

Firebase Authentication provides:
- Secure email/password authentication
- Token-based session management
- Server-side token verification
- Protected routes

### 3. Model Performance

The XGBoost model is optimized for FHE with:
- 6-bit quantization for efficiency
- Minimal accuracy degradation
- Reasonable inference latency
- Complete privacy guarantees

### 4. Analytics Dashboard

The report page shows:
- Plaintext vs FHE accuracy comparison
- Inference latency metrics
- Computational overhead analysis
- Privacy guarantees explanation

## Performance Metrics

Expected performance (will vary based on hardware):

| Metric | Plaintext | FHE | Overhead |
|--------|-----------|-----|----------|
| Accuracy | ~92% | ~90% | -2% |
| Latency | ~1ms | ~10-30s | 10,000x |
| Privacy | None | Complete | 100% |

## API Endpoints

### Authentication

- `GET /register` - Registration page
- `POST /register` - Create new user
- `GET /login` - Login page
- `POST /login` - Authenticate user
- `GET /logout` - Logout user

### Application

- `GET /` - Home page (redirects)
- `GET /predict` - Prediction form
- `POST /predict` - Make prediction (JSON API)
- `GET /report` - Analytics dashboard
- `GET /health` - Health check endpoint

## Development

### Running Tests

```bash
# Test preprocessing pipeline
python preprocess.py

# Test model training
python model.py
```

### Debug Mode

Set in `.env`:

```env
FLASK_DEBUG=True
```

### Demo Mode (No Firebase)

If Firebase is not configured, the app runs in demo mode:
- Authentication is disabled
- All routes are accessible
- Predictions still work

## Deployment

### Local Production

```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Cloud Deployment

For cloud deployment (Heroku, Railway, etc.):

1. Set environment variables
2. Use Gunicorn as WSGI server
3. Ensure HTTPS (required for Firebase)
4. Consider model loading optimization

## Troubleshooting

### Model Not Found

```
Error: FHE model not found
```

**Solution**: Run `python model.py` to train the model first.

### Firebase Configuration Error

```
Warning: Firebase not configured
```

**Solution**: Check `.env` file and ensure all Firebase credentials are set.

### Dataset Not Found

```
Error: Dataset not found at data/hair_loss.csv
```

**Solution**: Download the dataset and place it in `data/Sleep_health_and_lifestyle_dataset.csv`.

### Memory Error During Compilation

```
MemoryError: Cannot allocate memory
```

**Solution**: FHE compilation requires 4GB+ RAM. Close other applications or use a machine with more memory.

### Slow FHE Inference

**Expected**: FHE operations are computationally intensive. Inference takes 10-30 seconds per prediction.

## Security Considerations

- Never commit `.env` or `serviceAccountKey.json` to version control
- Use strong secret keys in production
- Enable HTTPS for production deployment
- Regularly update dependencies
- Implement rate limiting for prediction endpoint

## Academic Use

This project is designed for academic demonstration of:
- Fully Homomorphic Encryption in machine learning
- Privacy-preserving inference
- Secure web application architecture
- Trade-offs between privacy and performance

### For Viva/Presentation

Key points to highlight:
1. **Privacy Guarantees**: Complete data privacy using FHE
2. **Performance Trade-offs**: Accuracy vs latency analysis
3. **Real-world Application**: Healthcare data protection
4. **Technical Implementation**: Concrete-ML integration
5. **Security Architecture**: End-to-end encryption flow

## Contributing

This is an academic project. For improvements:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is for educational purposes.

## Acknowledgments

- **Concrete-ML**: Zama's FHE framework
- **Firebase**: Authentication and storage
- **Kaggle**: Sleep Health and Lifestyle Dataset
- **Bootstrap**: UI framework

## Contact

For questions or issues, please contact the project maintainer.

## References

- [Concrete-ML Documentation](https://docs.zama.ai/concrete-ml)
- [Firebase Documentation](https://firebase.google.com/docs)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [FHE Research Papers](https://eprint.iacr.org/)

---

**Built with privacy in mind. Your data, your control.**
