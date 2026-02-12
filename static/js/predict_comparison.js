/**
 * Sleep Disorder Prediction with Plaintext vs FHE Comparison
 * Runs both methods and compares performance
 */

// Sample data for testing
const sampleData = {
    // Personal Information (not used in prediction)
    'fullName': 'John Doe',
    'emailAddress': 'john.doe@example.com',
    'phoneNumber': '+1-555-123-4567',
    'jobDescription': 'Software Engineer',
    
    // Health Metrics (used in prediction)
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

// Store comparison results
let comparisonResults = [];

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
    
    // Load previous comparisons from localStorage
    loadComparisonHistory();
});

// Handle form submission
document.getElementById('predictionForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const predictBtn = document.getElementById('predictBtn');
    const compareMode = document.getElementById('compareMode')?.checked || false;
    const resultsCard = document.getElementById('resultsCard');
    const comparisonCard = document.getElementById('comparisonCard');
    const errorAlert = document.getElementById('errorAlert');
    
    // Disable button and show loading
    predictBtn.disabled = true;
    resultsCard.style.display = 'none';
    if (comparisonCard) comparisonCard.style.display = 'none';
    errorAlert.style.display = 'none';
    
    try {
        // Collect form data
        const formData = new FormData(e.target);
        const data = {};
        
        // Fields to exclude from prediction (personal information only for display)
        const excludedFields = ['fullName', 'emailAddress', 'phoneNumber', 'jobDescription'];
        
        // Process each field
        for (let [key, value] of formData.entries()) {
            // Skip personal information fields - they are not used in prediction
            if (excludedFields.includes(key)) {
                console.log(`ℹ️ Skipping personal field: ${key} (not used in prediction)`);
                continue;
            }
            
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
        
        console.log('🔍 Starting prediction...');
        console.log('📊 Compare mode:', compareMode);
        
        if (compareMode) {
            // Run both plaintext and FHE for comparison
            predictBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Running Comparison (Plaintext + FHE)...';
            await runComparison(data);
        } else {
            // Run single prediction (plaintext only)
            predictBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Predicting...';
            const result = await predictPlaintext(data);
            displayResults(result, false);
        }
        
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

/**
 * Run both plaintext and FHE predictions for comparison
 */
async function runComparison(data) {
    console.log('📊 Starting comparison: Plaintext vs FHE');
    
    const comparisonCard = document.getElementById('comparisonCard');
    const comparisonBody = document.getElementById('comparisonBody');
    
    // Show comparison card with loading
    if (comparisonCard) {
        comparisonCard.style.display = 'block';
        comparisonBody.innerHTML = `
            <div class="text-center py-4">
                <div class="spinner-border text-primary mb-3" role="status"></div>
                <p>Running comparison...</p>
            </div>
        `;
    }
    
    const comparison = {
        timestamp: new Date().toISOString(),
        input: data
    };
    
    try {
        // 1. Run Plaintext Prediction
        console.log('📝 Running plaintext prediction...');
        const plaintextStart = performance.now();
        const plaintextResult = await predictPlaintext(data);
        const plaintextTime = (performance.now() - plaintextStart) / 1000;
        
        comparison.plaintext = {
            prediction: plaintextResult.prediction,
            label: plaintextResult.label,
            time: plaintextTime,
            latency_ms: plaintextResult.latency_ms
        };
        
        console.log(`Plaintext: ${plaintextResult.label} (${plaintextTime.toFixed(3)}s)`);
        
        // 2. Run FHE Prediction
        console.log('🔐 Running FHE prediction...');
        const fheStart = performance.now();
        
        let fheResult;
        try {
            fheResult = await predictWithFHE(data);
            const fheTime = (performance.now() - fheStart) / 1000;
            
            comparison.fhe = {
                prediction: fheResult.prediction,
                label: fheResult.label,
                time: fheTime,
                latency_ms: fheResult.latency_ms,
                metrics: fheResult.fhe_metrics
            };
            
            console.log(`FHE: ${fheResult.label} (${fheTime.toFixed(3)}s)`);
        } catch (error) {
            console.error('FHE prediction failed:', error);
            console.error('Error details:', error.stack);
            comparison.fhe = {
                error: error.message || 'FHE prediction failed',
                time: (performance.now() - fheStart) / 1000
            };
        }
        
        // 3. Calculate comparison metrics
        if (comparison.fhe && !comparison.fhe.error) {
            comparison.speedup = comparison.fhe.time / comparison.plaintext.time;
            comparison.overhead_ms = (comparison.fhe.time - comparison.plaintext.time) * 1000;
            comparison.predictions_match = comparison.plaintext.label === comparison.fhe.label;
        }
        
        // 4. Store comparison
        comparisonResults.push(comparison);
        saveComparisonHistory();
        
        // 5. Display results
        displayComparison(comparison);
        displayResults(plaintextResult, true);
        
    } catch (error) {
        console.error('Comparison failed:', error);
        if (comparisonBody) {
            comparisonBody.innerHTML = `
                <div class="alert alert-danger">
                    <strong>Comparison failed:</strong> ${error.message}
                </div>
            `;
        }
    }
}

/**
 * Display comparison results
 */
function displayComparison(comparison) {
    const comparisonBody = document.getElementById('comparisonBody');
    if (!comparisonBody) return;
    
    const plaintext = comparison.plaintext;
    const fhe = comparison.fhe;
    
    let html = `
        <div class="row">
            <div class="col-md-6">
                <div class="card border-primary">
                    <div class="card-header bg-primary text-white">
                        <h6 class="mb-0">📝 Plaintext Prediction</h6>
                    </div>
                    <div class="card-body">
                        <p><strong>Result:</strong> ${plaintext.label}</p>
                        <p><strong>Time:</strong> ${plaintext.time.toFixed(3)}s</p>
                        <p><strong>Latency:</strong> ${plaintext.latency_ms.toFixed(2)}ms</p>
                        <span class="badge bg-success">Fast</span>
                        <span class="badge bg-warning">No Privacy</span>
                    </div>
                </div>
            </div>
            
            <div class="col-md-6">
                <div class="card border-success">
                    <div class="card-header bg-success text-white">
                        <h6 class="mb-0">🔐 FHE Prediction</h6>
                    </div>
                    <div class="card-body">
    `;
    
    if (fhe.error) {
        html += `
                        <p class="text-danger"><strong>Error:</strong> ${fhe.error}</p>
                        <p><strong>Time:</strong> ${fhe.time.toFixed(3)}s</p>
        `;
    } else {
        html += `
                        <p><strong>Result:</strong> ${fhe.label}</p>
                        <p><strong>Time:</strong> ${fhe.time.toFixed(3)}s</p>
                        <p><strong>Latency:</strong> ${fhe.latency_ms.toFixed(2)}ms</p>
                        <span class="badge bg-warning">Slower</span>
                        <span class="badge bg-success">Private</span>
        `;
        
        if (fhe.metrics) {
            html += `
                        <hr>
                        <small class="text-muted">
                            <div>Key Gen: ${fhe.metrics.key_generation.toFixed(2)}s</div>
                            <div>Encryption: ${fhe.metrics.encryption.toFixed(2)}s</div>
                            <div>Inference: ${fhe.metrics.inference.toFixed(2)}s</div>
                            <div>Decryption: ${fhe.metrics.decryption.toFixed(2)}s</div>
                        </small>
            `;
        }
    }
    
    html += `
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Add comparison metrics
    if (comparison.speedup) {
        html += `
            <div class="alert alert-info mt-3">
                <h6><i class="bi bi-bar-chart"></i> Comparison Metrics</h6>
                <div class="row">
                    <div class="col-md-4">
                        <strong>Overhead:</strong> ${comparison.speedup.toFixed(1)}x slower
                    </div>
                    <div class="col-md-4">
                        <strong>Time Difference:</strong> ${(comparison.overhead_ms / 1000).toFixed(2)}s
                    </div>
                    <div class="col-md-4">
                        <strong>Results Match:</strong> 
                        ${comparison.predictions_match ? 
                            '<span class="badge bg-success">✓ Yes</span>' : 
                            '<span class="badge bg-danger">✗ No</span>'}
                    </div>
                </div>
            </div>
        `;
    }
    
    // Add link to full report
    html += `
        <div class="text-center mt-3">
            <a href="/report" class="btn btn-outline-primary">
                <i class="bi bi-bar-chart"></i> View Full Analysis Report
            </a>
        </div>
    `;
    
    comparisonBody.innerHTML = html;
}

/**
 * Plaintext prediction
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
 * FHE prediction
 */
async function predictWithFHE(data) {
    console.log('🔐 Starting FHE prediction...');
    
    if (typeof FHEClient === 'undefined') {
        throw new Error('FHE client not loaded');
    }
    
    const fheClient = new FHEClient();
    
    // Generate keys
    const startKeyGen = performance.now();
    await fheClient.generateKeys();
    const keyGenTime = (performance.now() - startKeyGen) / 1000;
    
    // Encrypt
    const startEncrypt = performance.now();
    const encryptedData = await fheClient.encrypt(data);
    const encryptTime = (performance.now() - startEncrypt) / 1000;
    
    // Inference
    const startInference = performance.now();
    const encryptedResult = await fheClient.sendToServer(encryptedData);
    const inferenceTime = (performance.now() - startInference) / 1000;
    
    // Decrypt
    const startDecrypt = performance.now();
    const decryptedResult = await fheClient.decrypt(encryptedResult);
    const decryptTime = (performance.now() - startDecrypt) / 1000;
    
    const totalTime = keyGenTime + encryptTime + inferenceTime + decryptTime;
    
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
}

/**
 * Get interpretation
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
 * Display results
 */
function displayResults(result, isComparison) {
    const resultsCard = document.getElementById('resultsCard');
    const predictionResult = document.getElementById('predictionResult');
    const predictionInterpretation = document.getElementById('predictionInterpretation');
    const predictionIcon = document.getElementById('predictionIcon');
    const predictionLabel = document.getElementById('predictionLabel');
    const latency = document.getElementById('latency');
    const modeIndicator = document.getElementById('modeIndicator');
    
    predictionResult.textContent = result.result || 'Prediction completed';
    predictionInterpretation.textContent = result.interpretation || '';
    latency.textContent = result.latency_ms ? result.latency_ms.toFixed(2) : 'N/A';
    
    if (modeIndicator) {
        const mode = result.mode || 'plaintext';
        if (isComparison) {
            modeIndicator.innerHTML = '<span class="badge bg-info">📊 Comparison Mode</span>';
        } else if (mode === 'fhe') {
            modeIndicator.innerHTML = '<span class="badge bg-success">🔐 FHE Encrypted</span>';
        } else {
            modeIndicator.innerHTML = '<span class="badge bg-secondary">📝 Plaintext</span>';
        }
    }
    
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
    
    resultsCard.style.display = 'block';
    resultsCard.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

/**
 * Save comparison history to localStorage
 */
function saveComparisonHistory() {
    try {
        localStorage.setItem('fhe_comparisons', JSON.stringify(comparisonResults));
        console.log(`💾 Saved ${comparisonResults.length} comparisons`);
    } catch (error) {
        console.error('Failed to save comparisons:', error);
    }
}

/**
 * Load comparison history from localStorage
 */
function loadComparisonHistory() {
    try {
        const saved = localStorage.getItem('fhe_comparisons');
        if (saved) {
            comparisonResults = JSON.parse(saved);
            console.log(`📂 Loaded ${comparisonResults.length} comparisons`);
        }
    } catch (error) {
        console.error('Failed to load comparisons:', error);
        comparisonResults = [];
    }
}

/**
 * Export comparisons for report
 */
function exportComparisons() {
    return comparisonResults;
}

// Make available globally
window.exportComparisons = exportComparisons;
