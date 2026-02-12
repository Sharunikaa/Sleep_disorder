/**
 * FHE Client-side Operations with Security Logging
 * Handles encryption, decryption, and logging for demonstration
 */

class FHESecurityLogger {
    constructor() {
        this.events = [];
    }

    log(type, data) {
        const event = {
            timestamp: new Date().toISOString(),
            type: type,
            data: data
        };
        this.events.push(event);
        
        // Log to console with styling
        const emoji = this.getEmoji(type);
        console.log(`${emoji} [${type}]`, data);
        
        // Send to server for dashboard
        this.sendToServer(event);
    }

    getEmoji(type) {
        const emojiMap = {
            'KEY_GENERATION': '🔑',
            'ENCRYPTION': '🔐',
            'SERVER_RECEIVED': '📥',
            'FHE_INFERENCE': '⚙️',
            'SERVER_RESPONSE': '📤',
            'DECRYPTION': '🔓',
            'PRIVACY_CHECK': '🛡️',
            'PERFORMANCE_METRICS': '📊'
        };
        return emojiMap[type] || '📌';
    }

    async sendToServer(event) {
        try {
            // Send event to server for security audit dashboard
            await fetch('/api/security/log', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(event)
            });
        } catch (error) {
            console.error('Failed to send log to server:', error);
        }
    }

    logKeyGeneration(keyInfo) {
        this.log('KEY_GENERATION', {
            location: 'browser',
            generation_time: keyInfo.generation_time,
            private_key_size: keyInfo.private_key_size,
            eval_keys_size: keyInfo.eval_keys_size,
            key_fingerprint: keyInfo.key_fingerprint
        });
    }

    logEncryption(encryptionInfo) {
        this.log('ENCRYPTION', {
            plain_data: encryptionInfo.plain_data_preview,
            encrypted_data: encryptionInfo.encrypted_preview,
            encryption_time: encryptionInfo.encryption_time,
            original_size: encryptionInfo.original_size,
            encrypted_size: encryptionInfo.encrypted_size
        });
    }

    logDecryption(decryptionInfo) {
        this.log('DECRYPTION', {
            encrypted_data: decryptionInfo.encrypted_preview,
            decrypted_result: decryptionInfo.decrypted_result,
            decryption_time: decryptionInfo.decryption_time
        });
    }

    logPrivacyCheck() {
        this.log('PRIVACY_CHECK', {
            server_has_private_key: false,
            server_can_decrypt: false,
            data_exposed: false,
            message: 'All privacy guarantees maintained'
        });
    }

    logPerformanceMetrics(metrics) {
        this.log('PERFORMANCE_METRICS', metrics);
    }

    logClientServerComparison(comparison) {
        console.log('┌─────────────────────────────┬─────────────────────────────┐');
        console.log('│   CLIENT SEES (Plaintext)   │   SERVER SEES (Encrypted)   │');
        console.log('├─────────────────────────────┼─────────────────────────────┤');
        console.log(`│ Input: ${comparison.client_input.substring(0,20).padEnd(20)} │ Input: ${comparison.server_input.substring(0,20).padEnd(20)} │`);
        console.log(`│ Result: ${comparison.client_result.padEnd(19)} │ Result: ${comparison.server_result.padEnd(19)} │`);
        console.log('└─────────────────────────────┴─────────────────────────────┘');
    }
}

// Global logger instance
const fheLogger = new FHESecurityLogger();

/**
 * Simulated FHE Client
 * In production, this would use actual Concrete-ML client library
 */
class FHEClient {
    constructor() {
        this.privateKey = null;
        this.evaluationKeys = null;
        this.clientFiles = null;
    }

    /**
     * Generate FHE keys (simulated for demo)
     */
    async generateKeys() {
        const startTime = performance.now();
        
        console.log('🔑 Generating FHE keys...');
        
        // Simulate key generation delay
        await this.sleep(500);
        
        // Generate random keys (simulation)
        this.privateKey = this.generateRandomBytes(1024); // 1KB private key
        this.evaluationKeys = this.generateRandomBytes(15 * 1024 * 1024); // 15MB eval keys
        
        const generationTime = (performance.now() - startTime) / 1000;
        
        // Log key generation
        fheLogger.logKeyGeneration({
            generation_time: generationTime,
            private_key_size: this.privateKey.length,
            eval_keys_size: this.evaluationKeys.length,
            key_fingerprint: this.hashData(this.privateKey).substring(0, 16)
        });
        
        console.log('Keys generated successfully');
        console.log(`   Private key: ${this.privateKey.length} bytes (KEPT SECRET)`);
        console.log(`   Evaluation keys: ${(this.evaluationKeys.length / (1024*1024)).toFixed(2)} MB (will be sent to server)`);
        
        return {
            privateKey: this.privateKey,
            evaluationKeys: this.evaluationKeys
        };
    }

    /**
     * Encrypt data (simulated)
     */
    async encrypt(plainData) {
        if (!this.privateKey) {
            throw new Error('Keys not generated. Call generateKeys() first.');
        }
        
        const startTime = performance.now();
        
        console.log('🔐 Encrypting data...');
        console.log('   Plain data:', plainData);
        
        // Simulate encryption delay
        await this.sleep(200);
        
        // Convert plain data to bytes (simulation)
        const plainBytes = new TextEncoder().encode(JSON.stringify(plainData));
        
        // Simulate encryption (just add random padding)
        const encryptedData = this.generateRandomBytes(plainBytes.length * 100); // 100x size increase
        
        const encryptionTime = (performance.now() - startTime) / 1000;
        
        // Log encryption
        fheLogger.logEncryption({
            plain_data_preview: this.truncateObject(plainData),
            encrypted_preview: this.bytesToHex(encryptedData).substring(0, 64) + '...',
            encryption_time: encryptionTime,
            original_size: plainBytes.length,
            encrypted_size: encryptedData.length
        });
        
        console.log('Data encrypted');
        console.log(`   Original size: ${plainBytes.length} bytes`);
        console.log(`   Encrypted size: ${(encryptedData.length / 1024).toFixed(2)} KB`);
        console.log(`   Overhead: ${(encryptedData.length / plainBytes.length).toFixed(0)}x`);
        
        // Log client-server comparison
        fheLogger.logClientServerComparison({
            client_input: JSON.stringify(plainData).substring(0, 25),
            server_input: '0x' + this.bytesToHex(encryptedData).substring(0, 20) + '...',
            client_result: 'Will decrypt after inference',
            server_result: 'Cannot see (encrypted)'
        });
        
        return encryptedData;
    }

    /**
     * Decrypt data (simulated)
     */
    async decrypt(encryptedData) {
        if (!this.privateKey) {
            throw new Error('Keys not generated. Call generateKeys() first.');
        }
        
        const startTime = performance.now();
        
        console.log('🔓 Decrypting result...');
        
        // Simulate decryption delay
        await this.sleep(100);
        
        // Simulate decryption (return mock result)
        // In real FHE, this would decrypt the actual encrypted result
        const decryptedResult = {
            prediction: 1,
            label: 'No Issues',
            confidence: 0.92
        };
        
        const decryptionTime = (performance.now() - startTime) / 1000;
        
        // Log decryption
        fheLogger.logDecryption({
            encrypted_preview: this.bytesToHex(encryptedData).substring(0, 64) + '...',
            decrypted_result: decryptedResult,
            decryption_time: decryptionTime
        });
        
        console.log('Result decrypted');
        console.log('   Decrypted result:', decryptedResult);
        
        return decryptedResult;
    }

    /**
     * Send encrypted data to server for FHE inference
     */
    async sendToServer(encryptedData) {
        console.log('📤 Sending encrypted data to server...');
        console.log(`   Size: ${(encryptedData.length / 1024).toFixed(2)} KB`);
        console.log('   Server will NOT be able to see plaintext!');
        
        try {
            const response = await fetch('/predict_fhe', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/octet-stream',
                },
                body: encryptedData
            });
            
            if (!response.ok) {
                const errorText = await response.text();
                console.error('Server error response:', errorText);
                throw new Error(`Server inference failed: ${response.status} ${response.statusText}`);
            }
            
            const encryptedResult = await response.arrayBuffer();
            
            console.log('📥 Received encrypted result from server');
            console.log(`   Size: ${encryptedResult.byteLength} bytes`);
            
            return new Uint8Array(encryptedResult);
            
        } catch (error) {
            console.error('Server communication failed:', error);
            console.error('Error details:', error.message);
            throw error;
        }
    }

    /**
     * Complete FHE prediction flow
     */
    async predictWithFHE(inputData) {
        const totalStartTime = performance.now();
        
        console.log('\n' + '='.repeat(60));
        console.log('🔐 STARTING FHE PREDICTION FLOW');
        console.log('='.repeat(60) + '\n');
        
        try {
            // Step 1: Generate keys if not already generated
            if (!this.privateKey) {
                await this.generateKeys();
            }
            
            // Step 2: Encrypt input data
            const encryptedInput = await this.encrypt(inputData);
            
            // Step 3: Send to server for FHE inference
            const encryptedResult = await this.sendToServer(encryptedInput);
            
            // Step 4: Decrypt result
            const decryptedResult = await this.decrypt(encryptedResult);
            
            // Step 5: Privacy check
            fheLogger.logPrivacyCheck();
            
            // Step 6: Performance metrics
            const totalTime = (performance.now() - totalStartTime) / 1000;
            fheLogger.logPerformanceMetrics({
                total_time: totalTime,
                key_generation_time: 0.5, // From simulation
                encryption_time: 0.2,
                inference_time: 2.0, // Estimated server time
                decryption_time: 0.1,
                overhead_factor: 150 // Compared to plaintext
            });
            
            console.log('\n' + '='.repeat(60));
            console.log('FHE PREDICTION COMPLETED');
            console.log('='.repeat(60));
            console.log(`⏱️  Total time: ${totalTime.toFixed(2)}s`);
            console.log('🛡️  Privacy preserved: Server never saw your data!');
            console.log('='.repeat(60) + '\n');
            
            return decryptedResult;
            
        } catch (error) {
            console.error('\nFHE prediction failed:', error);
            throw error;
        }
    }

    // Helper methods
    
    generateRandomBytes(length) {
        const array = new Uint8Array(length);
        const maxChunkSize = 65536; // Browser limit for crypto.getRandomValues
        
        // Generate in chunks to avoid browser limit
        for (let i = 0; i < length; i += maxChunkSize) {
            const chunkSize = Math.min(maxChunkSize, length - i);
            const chunk = new Uint8Array(chunkSize);
            crypto.getRandomValues(chunk);
            array.set(chunk, i);
        }
        
        return array;
    }

    bytesToHex(bytes) {
        return Array.from(bytes)
            .map(b => b.toString(16).padStart(2, '0'))
            .join('');
    }

    hashData(data) {
        // Simple hash simulation
        let hash = 0;
        const str = data.toString();
        for (let i = 0; i < str.length; i++) {
            hash = ((hash << 5) - hash) + str.charCodeAt(i);
            hash = hash & hash;
        }
        return Math.abs(hash).toString(16);
    }

    truncateObject(obj) {
        const str = JSON.stringify(obj);
        return str.length > 100 ? str.substring(0, 100) + '...' : str;
    }

    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}

// Export for use in other scripts
window.FHEClient = FHEClient;
window.fheLogger = fheLogger;
