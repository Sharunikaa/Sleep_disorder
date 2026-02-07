/**
 * Sleep Disorder Prediction - Client-side JavaScript with FHE Support
 * Handles form submission with option for FHE or plaintext prediction
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
    const useFHE = document.getElementById('useFHE')?.checked || false;
    const resultsCard = document.getElementById('resultsCard');
    const errorAlert = document.getElementById('errorAlert');
    
    // Disable button and show loading
    predictBtn.disabled = true;
    const loadingText = useFHE ? 
        '<span class="spinner-border spinner-border-sm me-2"></span>Encrypting & Predicting (FHE)...' :
        '<span class="spinner-border spinner-border-sm me-2"></span>Predicting...';
    predictBtn.innerHTML = loadingText;
    resultsCard.style.display = 'none';
    errorAlert.style.display = 'none';
    
    try {
        // Collect form data
        const formData = new FormData(e.target);
        const data = {};
        
        // Process each field
        for (let [key, value] of formData.entries()) {
            if (key === 'Gender') {
                data['Gender_Encoded'] = value === 'Female' ? 0 : 1;
            } else if (key === 'BMI Category') {
                const bmiMap = {'Normal': 0, 'Normal Weight': 1, 'Obese': 2, 'Overweight': 3};
                data['BMI_Encoded'] = bmiMap[value] || 0;
            } else if (key === 'Blood Pressure') {
                const [systolic, diastolic] = value.split('/').map(Number);
                data['BP_Systolic'] = systolic;
                data['BP_Diastolic'] = diastolic;
            } else {
                data[key] = parseFloat(value);
            }
        }
        
        console.log('🔍 Prediction request:', data);
        console.log('🔐 Using FHE:', useFHE);
        
        let result;
        
        if (useFHE && typeof FHEClient !== 'undefined') {
            // Use FHE prediction
            console.log('🔐 Starting FHE prediction flow...');
            result = await predictWithFHE(data);
        } else {
            // Use plaintext prediction
            console.log('📝 Using plaintext prediction...');
            result = await predictPlaintext(data);
        }
        
        console.log('✅ Prediction result:', result);
        
        // Display results
        displayResults(result);
        
    } catch (error) {
        console.error('❌ Prediction error:', error);
        document.getElementById('errorMessage').textContent = error.message;
        errorAlert.style.display = 'block';
    } finally {
        // Re-enable button
        predictBtn.disabled = false;
        predictBtn.innerHTML = '<i class="bi bi-cpu"></i> Predict';
    }
});

/**
 * Plaintext prediction (fast, no encryption)
 */
async function predictPlaintext(data) {
    console.log('📤 Sending plaintext request to /predict');
    
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
    result.mode = result.mode || 'plaintext';
    return result;
}

/**
 * FHE prediction (secure, encrypted)
 */
async function predictWithFHE(data) {
    console.log('🔐 Starting FHE prediction...');
    
    // Check if FHEClient is available
    if (typeof FHEClient === 'undefined') {
        throw new Error('FHE client not loaded. Please refresh the page.');
    }
    
    try {
        // Initialize FHE client
        const fheClient = new FHEClient();
        
        // Step 1: Generate keys (if not already generated)
        console.log('🔑 Generating FHE keys...');
        const startKeyGen = performance.now();
        await fheClient.generateKeys();
        const keyGenTime = (performance.now() - startKeyGen) / 1000;
        console.log(`✅ Keys generated in ${keyGenTime.toFixed(2)}s`);
        
        // Step 2: Encrypt data
        console.log('🔐 Encrypting input data...');
        const startEncrypt = performance.now();
        const encryptedData = await fheClient.encrypt(data);
        const encryptTime = (performance.now() - startEncrypt) / 1000;
        console.log(`✅ Data encrypted in ${encryptTime.toFixed(2)}s`);
        
        // Step 3: Send to server for FHE inference
        console.log('📤 Sending encrypted data to server...');
        const startInference = performance.now();
        const encryptedResult = await fheClient.sendToServer(encryptedData);
        const inferenceTime = (performance.now() - startInference) / 1000;
        console.log(`✅ Server inference completed in ${inferenceTime.toFixed(2)}s`);
        
        // Step 4: Decrypt result
        console.log('🔓 Decrypting result...');
        const startDecrypt = performance.now();
        const decryptedResult = await fheClient.decrypt(encryptedResult);
        const decryptTime = (performance.now() - startDecrypt) / 1000;
        console.log(`✅ Result decrypted in ${decryptTime.toFixed(2)}s`);
        
        // Total time
        const totalTime = keyGenTime + encryptTime + inferenceTime + decryptTime;
        console.log(`⏱️  Total FHE time: ${totalTime.toFixed(2)}s`);
        
        // Format result to match plaintext response
        return {
            prediction: decryptedResult.prediction,
            result: `Sleep Disorder Prediction: ${decryptedResult.label}`,
            label: decryptedResult.label,
            interpretation: getInterpretation(decryptedResult.label),
            latency_ms: totalTime * 1000,
            mode: 'fhe',
            fhe_metrics: {
                key_generation: keyGenTime,
                encryption: encryptTime,
                inference: inferenceTime,
                decryption: decryptTime,
                total: totalTime
            }
        };
        
    } catch (error) {
        console.error('❌ FHE prediction failed:', error);
        console.log('⚠️  Falling back to plaintext prediction...');
        return await predictPlaintext(data);
    }
}

/**
 * Get interpretation for prediction label
 */
function getInterpretation(label) {
    const interpretations = {
        'Insomnia': 'Difficulty falling or staying asleep. Consider consulting a sleep specialist.',
        'No Issues': 'No sleep disorder detected. Maintain healthy sleep habits!',
        'Sleep Apnea': 'Breathing interruptions during sleep. Medical evaluation recommended.'
    };
    return interpretations[label] || '';
}

/**
 * Display prediction results
 */
function displayResults(result) {
    const resultsCard = document.getElementById('resultsCard');
    const predictionResult = document.getElementById('predictionResult');
    const predictionInterpretation = document.getElementById('predictionInterpretation');
    const predictionIcon = document.getElementById('predictionIcon');
    const predictionLabel = document.getElementById('predictionLabel');
    const latency = document.getElementById('latency');
    const modeIndicator = document.getElementById('modeIndicator');
    
    // Set result text
    predictionResult.textContent = result.result || 'Prediction completed';
    predictionInterpretation.textContent = result.interpretation || '';
    latency.textContent = result.latency_ms ? result.latency_ms.toFixed(2) : 'N/A';
    
    // Show mode indicator
    if (modeIndicator) {
        const mode = result.mode || 'plaintext';
        if (mode === 'fhe') {
            modeIndicator.innerHTML = '<span class="badge bg-success">🔐 FHE Encrypted</span>';
            
            // Show detailed FHE metrics if available
            if (result.fhe_metrics) {
                const metrics = result.fhe_metrics;
                modeIndicator.innerHTML += `
                    <div class="mt-2 small text-muted">
                        <div>Key Gen: ${metrics.key_generation.toFixed(2)}s</div>
                        <div>Encryption: ${metrics.encryption.toFixed(2)}s</div>
                        <div>Inference: ${metrics.inference.toFixed(2)}s</div>
                        <div>Decryption: ${metrics.decryption.toFixed(2)}s</div>
                    </div>
                `;
            }
        } else {
            modeIndicator.innerHTML = '<span class="badge bg-secondary">📝 Plaintext</span>';
        }
    }
    
    // Set icon and label based on prediction
    const label = result.label || '';
    predictionLabel.textContent = label;
    
    if (label === 'Insomnia') {
        predictionIcon.innerHTML = '😴';
        predictionIcon.style.color = '#ffc107';
    } else if (label === 'Sleep Apnea') {
        predictionIcon.innerHTML = '😪';
        predictionIcon.style.color = '#dc3545';
    } else if (label === 'No Issues') {
        predictionIcon.innerHTML = '😊';
        predictionIcon.style.color = '#28a745';
    } else {
        predictionIcon.innerHTML = '❓';
        predictionIcon.style.color = '#6c757d';
    }
    
    // Show results card with animation
    resultsCard.style.display = 'block';
    resultsCard.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}
