/**
 * Sleep Disorder Prediction - Client-side JavaScript
 * Handles form submission and result display
 */

// Sample data for testing
const sampleData = {
    'Gender': 'Male',
    'Age': 35,
    'Sleep Duration': 7.2,
    'Quality of Sleep': 7,
    'Physical Activity Level': 60,
    'Stress Level': 6,
    'BMI Category': 'Normal',
    'Blood Pressure': '125/80',
    'Heart Rate': 72,
    'Daily Steps': 8000
};

// Fill form with sample data
function fillSampleData() {
    Object.keys(sampleData).forEach(key => {
        const element = document.getElementById(key) || document.getElementsByName(key)[0];
        if (element) {
            element.value = sampleData[key];
        }
    });
}

// Initialize tooltips
document.addEventListener('DOMContentLoaded', function() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
});

// Handle form submission
document.getElementById('predictionForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const predictBtn = document.getElementById('predictBtn');
    const resultsCard = document.getElementById('resultsCard');
    const errorAlert = document.getElementById('errorAlert');
    
    // Disable button and show loading
    predictBtn.disabled = true;
    predictBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Predicting...';
    resultsCard.style.display = 'none';
    errorAlert.style.display = 'none';
    
    try {
        // Collect form data
        const formData = new FormData(e.target);
        const data = {};
        
        // Process each field
        for (let [key, value] of formData.entries()) {
            if (key === 'Gender') {
                // Encode gender: Female=0, Male=1
                data['Gender_Encoded'] = value === 'Female' ? 0 : 1;
            } else if (key === 'BMI Category') {
                // Encode BMI: Normal=0, Normal Weight=1, Obese=2, Overweight=3
                const bmiMap = {'Normal': 0, 'Normal Weight': 1, 'Obese': 2, 'Overweight': 3};
                data['BMI_Encoded'] = bmiMap[value] || 0;
            } else if (key === 'Blood Pressure') {
                // Split blood pressure into systolic and diastolic
                const [systolic, diastolic] = value.split('/').map(Number);
                data['BP_Systolic'] = systolic;
                data['BP_Diastolic'] = diastolic;
            } else {
                // Numeric fields
                data[key] = parseFloat(value);
            }
        }
        
        console.log('Sending prediction request:', data);
        
        // Send prediction request
        const response = await fetch('/predict', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Prediction failed');
        }
        
        const result = await response.json();
        console.log('Prediction result:', result);
        
        // Display results
        displayResults(result);
        
    } catch (error) {
        console.error('Prediction error:', error);
        document.getElementById('errorMessage').textContent = error.message;
        errorAlert.style.display = 'block';
    } finally {
        // Re-enable button
        predictBtn.disabled = false;
        predictBtn.innerHTML = '<i class="bi bi-cpu"></i> Predict';
    }
});

// Display prediction results
function displayResults(result) {
    const resultsCard = document.getElementById('resultsCard');
    const predictionResult = document.getElementById('predictionResult');
    const predictionInterpretation = document.getElementById('predictionInterpretation');
    const predictionIcon = document.getElementById('predictionIcon');
    const predictionLabel = document.getElementById('predictionLabel');
    const latency = document.getElementById('latency');
    
    // Set result text
    predictionResult.textContent = result.result || 'Prediction completed';
    predictionInterpretation.textContent = result.interpretation || '';
    latency.textContent = result.latency_ms ? result.latency_ms.toFixed(2) : 'N/A';
    
    // Set icon and label based on prediction
    const label = result.label || '';
    predictionLabel.textContent = label;
    
    if (label === 'Insomnia') {
        predictionIcon.innerHTML = '😴';
        predictionIcon.style.color = '#ffc107'; // Warning yellow
    } else if (label === 'Sleep Apnea') {
        predictionIcon.innerHTML = '😪';
        predictionIcon.style.color = '#dc3545'; // Danger red
    } else if (label === 'No Issues') {
        predictionIcon.innerHTML = '😊';
        predictionIcon.style.color = '#28a745'; // Success green
    } else {
        predictionIcon.innerHTML = '❓';
        predictionIcon.style.color = '#6c757d'; // Secondary gray
    }
    
    // Show results card with animation
    resultsCard.style.display = 'block';
    resultsCard.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}
