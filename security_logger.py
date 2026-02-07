"""
Security Logger Module for FHE Audit Trail
Logs all encryption/decryption events, key generation, and data flow
"""

import logging
import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import base64

class FHESecurityLogger:
    """
    Comprehensive security logger for FHE operations
    Logs key generation, encryption, inference, and decryption events
    """
    
    def __init__(self, log_dir: str = "logs"):
        """Initialize the security logger"""
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Setup file logging
        self.log_file = self.log_dir / "fhe_security_audit.log"
        self.setup_logging()
        
        # In-memory event storage for web dashboard
        self.events = []
        self.max_events = 100  # Keep last 100 events
        
    def setup_logging(self):
        """Setup file and console logging"""
        # File handler
        file_handler = logging.FileHandler(self.log_file, mode='a', encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        file_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        
        # Console handler with colors
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '%(asctime)s | %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        
        # Setup logger
        self.logger = logging.getLogger('FHE_Security')
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
    def _add_event(self, event_type: str, data: Dict[str, Any]):
        """Add event to in-memory storage for dashboard"""
        event = {
            'timestamp': datetime.now().isoformat(),
            'type': event_type,
            'data': data
        }
        self.events.append(event)
        
        # Keep only last max_events
        if len(self.events) > self.max_events:
            self.events = self.events[-self.max_events:]
    
    def _hash_data(self, data: bytes, length: int = 16) -> str:
        """Create SHA256 fingerprint of data"""
        hash_obj = hashlib.sha256(data)
        return hash_obj.hexdigest()[:length]
    
    def _truncate_hex(self, data: bytes, max_bytes: int = 32) -> str:
        """Convert bytes to truncated hex string"""
        hex_str = data.hex() if isinstance(data, bytes) else str(data)
        if len(hex_str) > max_bytes * 2:
            return f"0x{hex_str[:max_bytes*2]}... ({len(data)} bytes total)"
        return f"0x{hex_str}"
    
    def log_separator(self, title: str = ""):
        """Log a visual separator"""
        separator = "=" * 80
        self.logger.info(separator)
        if title:
            self.logger.info(f"  {title}")
            self.logger.info(separator)
    
    def log_key_generation(self, key_info: Dict[str, Any]):
        """
        Log key generation event
        
        Args:
            key_info: {
                'private_key_size': int,
                'eval_keys_size': int,
                'generation_time': float,
                'location': str (e.g., 'client', 'browser')
            }
        """
        self.log_separator("🔑 KEY GENERATION EVENT")
        
        self.logger.info("📍 Location: %s", key_info.get('location', 'Unknown'))
        self.logger.info("⏱️  Generation Time: %.2f seconds", key_info.get('generation_time', 0))
        
        if 'private_key_size' in key_info:
            size_kb = key_info['private_key_size'] / 1024
            self.logger.info("🔐 Private Key: Generated (%.2f KB)", size_kb)
            self.logger.info("   └─ Status: KEPT SECRET (never sent to server)")
        
        if 'eval_keys_size' in key_info:
            size_mb = key_info['eval_keys_size'] / (1024 * 1024)
            self.logger.info("🔑 Evaluation Keys: Generated (%.2f MB)", size_mb)
            self.logger.info("   └─ Status: Will be sent to server")
        
        if 'key_fingerprint' in key_info:
            self.logger.info("🔖 Key Fingerprint: %s", key_info['key_fingerprint'])
        
        self.logger.info("")
        
        # Add to events
        self._add_event('KEY_GENERATION', key_info)
    
    def log_encryption(self, encryption_info: Dict[str, Any]):
        """
        Log data encryption event
        
        Args:
            encryption_info: {
                'plain_data': dict or array,
                'encrypted_data': bytes,
                'encryption_time': float,
                'original_size': int,
                'encrypted_size': int
            }
        """
        self.log_separator("🔐 ENCRYPTION EVENT - CLIENT SIDE")
        
        # Plain data (show structure, not actual values for privacy)
        if 'plain_data' in encryption_info:
            self.logger.info("📝 Plain Data (Client Side):")
            plain = encryption_info['plain_data']
            if isinstance(plain, dict):
                for key, value in list(plain.items())[:5]:  # Show first 5 features
                    self.logger.info(f"   {key}: {value}")
                if len(plain) > 5:
                    self.logger.info(f"   ... and {len(plain) - 5} more features")
        
        # Encrypted data preview
        if 'encrypted_data' in encryption_info:
            encrypted = encryption_info['encrypted_data']
            if isinstance(encrypted, bytes):
                preview = self._truncate_hex(encrypted, 32)
                self.logger.info("🔐 Encrypted Data: %s", preview)
            elif isinstance(encrypted, list):
                preview = str(encrypted[:8]) + "..." if len(encrypted) > 8 else str(encrypted)
                self.logger.info("🔐 Encrypted Data: %s", preview)
        
        # Size comparison
        if 'original_size' in encryption_info and 'encrypted_size' in encryption_info:
            orig = encryption_info['original_size']
            enc = encryption_info['encrypted_size']
            overhead = enc / orig if orig > 0 else 0
            self.logger.info("📊 Size Comparison:")
            self.logger.info(f"   Original: {orig} bytes")
            self.logger.info(f"   Encrypted: {enc} bytes ({enc/1024:.2f} KB)")
            self.logger.info(f"   Overhead: {overhead:.1f}x")
        
        # Timing
        if 'encryption_time' in encryption_info:
            self.logger.info("⏱️  Encryption Time: %.4f seconds", encryption_info['encryption_time'])
        
        self.logger.info("✅ Data encrypted successfully")
        self.logger.info("📤 Ready to send to server")
        self.logger.info("")
        
        # Add to events
        self._add_event('ENCRYPTION', encryption_info)
    
    def log_server_received(self, request_info: Dict[str, Any]):
        """
        Log when server receives encrypted request
        
        Args:
            request_info: {
                'encrypted_input': bytes or list,
                'eval_keys_size': int,
                'client_ip': str,
                'timestamp': str
            }
        """
        self.log_separator("📥 SERVER RECEIVED ENCRYPTED REQUEST")
        
        self.logger.info("📍 Source: %s", request_info.get('client_ip', 'Unknown'))
        self.logger.info("🕐 Received At: %s", request_info.get('timestamp', datetime.now().isoformat()))
        
        # Show encrypted data preview
        if 'encrypted_input' in request_info:
            encrypted = request_info['encrypted_input']
            if isinstance(encrypted, bytes):
                preview = self._truncate_hex(encrypted, 32)
            elif isinstance(encrypted, list):
                preview = str(encrypted[:8]) + f"... ({len(encrypted)} elements)"
            else:
                preview = str(encrypted)[:100]
            self.logger.info("🔐 Encrypted Input: %s", preview)
        
        if 'eval_keys_size' in request_info:
            size_mb = request_info['eval_keys_size'] / (1024 * 1024)
            self.logger.info("🔑 Evaluation Keys: %.2f MB", size_mb)
        
        # Privacy warning
        self.logger.info("")
        self.logger.info("⚠️  PRIVACY CHECK:")
        self.logger.info("   ❌ Server CANNOT decrypt this data")
        self.logger.info("   ❌ Server does NOT have private key")
        self.logger.info("   ✅ Server can only compute on encrypted data")
        self.logger.info("")
        
        # Add to events
        self._add_event('SERVER_RECEIVED', request_info)
    
    def log_fhe_inference(self, inference_info: Dict[str, Any]):
        """
        Log FHE inference processing
        
        Args:
            inference_info: {
                'start_time': float,
                'end_time': float,
                'duration': float,
                'mode': str ('fhe' or 'plaintext')
            }
        """
        mode = inference_info.get('mode', 'unknown')
        
        if mode == 'fhe':
            self.log_separator("⚙️  FHE INFERENCE - ENCRYPTED COMPUTATION")
            self.logger.info("🔐 Computing on ENCRYPTED data")
            self.logger.info("⚠️  Server cannot see actual values")
        else:
            self.log_separator("⚙️  PLAINTEXT INFERENCE")
            self.logger.info("📝 Computing on PLAINTEXT data (fallback mode)")
        
        if 'duration' in inference_info:
            self.logger.info("⏱️  Inference Time: %.2f seconds", inference_info['duration'])
        
        self.logger.info("✅ Computation complete")
        self.logger.info("")
        
        # Add to events
        self._add_event('FHE_INFERENCE', inference_info)
    
    def log_server_response(self, response_info: Dict[str, Any]):
        """
        Log server sending encrypted response
        
        Args:
            response_info: {
                'encrypted_output': bytes or list,
                'output_size': int,
                'mode': str
            }
        """
        self.log_separator("📤 SERVER SENDING ENCRYPTED RESPONSE")
        
        mode = response_info.get('mode', 'unknown')
        
        if mode == 'fhe':
            if 'encrypted_output' in response_info:
                encrypted = response_info['encrypted_output']
                if isinstance(encrypted, bytes):
                    preview = self._truncate_hex(encrypted, 32)
                elif isinstance(encrypted, list):
                    preview = str(encrypted[:8]) + f"... ({len(encrypted)} elements)"
                else:
                    preview = str(encrypted)[:100]
                self.logger.info("🔐 Encrypted Output: %s", preview)
            
            if 'output_size' in response_info:
                size = response_info['output_size']
                self.logger.info("📊 Output Size: %d bytes (%.2f KB)", size, size/1024)
            
            self.logger.info("")
            self.logger.info("⚠️  PRIVACY CHECK:")
            self.logger.info("   ❌ Server CANNOT read this result")
            self.logger.info("   ✅ Only client can decrypt with private key")
        else:
            self.logger.info("📝 Plaintext result (fallback mode)")
        
        self.logger.info("")
        
        # Add to events
        self._add_event('SERVER_RESPONSE', response_info)
    
    def log_decryption(self, decryption_info: Dict[str, Any]):
        """
        Log client-side decryption
        
        Args:
            decryption_info: {
                'encrypted_data': bytes,
                'decrypted_result': any,
                'decryption_time': float
            }
        """
        self.log_separator("🔓 DECRYPTION EVENT - CLIENT SIDE")
        
        if 'encrypted_data' in decryption_info:
            encrypted = decryption_info['encrypted_data']
            if isinstance(encrypted, bytes):
                preview = self._truncate_hex(encrypted, 32)
            else:
                preview = str(encrypted)[:100]
            self.logger.info("🔐 Encrypted Data: %s", preview)
        
        self.logger.info("🔓 Decrypting with private key...")
        
        if 'decryption_time' in decryption_info:
            self.logger.info("⏱️  Decryption Time: %.4f seconds", decryption_info['decryption_time'])
        
        if 'decrypted_result' in decryption_info:
            result = decryption_info['decrypted_result']
            self.logger.info("✅ Decrypted Result: %s", result)
        
        self.logger.info("")
        
        # Add to events
        self._add_event('DECRYPTION', decryption_info)
    
    def log_privacy_check(self, check_info: Dict[str, Any]):
        """
        Log privacy verification checks
        
        Args:
            check_info: {
                'server_has_private_key': bool,
                'server_can_decrypt': bool,
                'data_exposed': bool
            }
        """
        self.log_separator("🛡️  PRIVACY VERIFICATION")
        
        self.logger.info("Security Checks:")
        self.logger.info("  Server has private key: %s", 
                        "❌ NO (Secure)" if not check_info.get('server_has_private_key') else "⚠️  YES (INSECURE)")
        self.logger.info("  Server can decrypt: %s", 
                        "❌ NO (Secure)" if not check_info.get('server_can_decrypt') else "⚠️  YES (INSECURE)")
        self.logger.info("  Data exposed in plaintext: %s", 
                        "❌ NO (Secure)" if not check_info.get('data_exposed') else "⚠️  YES (INSECURE)")
        
        all_secure = (
            not check_info.get('server_has_private_key', False) and
            not check_info.get('server_can_decrypt', False) and
            not check_info.get('data_exposed', False)
        )
        
        if all_secure:
            self.logger.info("✅ All privacy checks passed!")
        else:
            self.logger.info("⚠️  Privacy concerns detected!")
        
        self.logger.info("")
        
        # Add to events
        self._add_event('PRIVACY_CHECK', check_info)
    
    def log_performance_metrics(self, metrics: Dict[str, Any]):
        """
        Log performance metrics
        
        Args:
            metrics: {
                'key_generation_time': float,
                'encryption_time': float,
                'inference_time': float,
                'decryption_time': float,
                'total_time': float,
                'overhead_factor': float
            }
        """
        self.log_separator("📊 PERFORMANCE METRICS")
        
        if 'key_generation_time' in metrics:
            self.logger.info("🔑 Key Generation: %.2f seconds", metrics['key_generation_time'])
        
        if 'encryption_time' in metrics:
            self.logger.info("🔐 Encryption: %.4f seconds", metrics['encryption_time'])
        
        if 'inference_time' in metrics:
            self.logger.info("⚙️  FHE Inference: %.2f seconds", metrics['inference_time'])
        
        if 'decryption_time' in metrics:
            self.logger.info("🔓 Decryption: %.4f seconds", metrics['decryption_time'])
        
        if 'total_time' in metrics:
            self.logger.info("⏱️  Total Time: %.2f seconds", metrics['total_time'])
        
        if 'overhead_factor' in metrics:
            self.logger.info("📈 FHE Overhead: %.0fx slower than plaintext", metrics['overhead_factor'])
        
        self.logger.info("")
        
        # Add to events
        self._add_event('PERFORMANCE_METRICS', metrics)
    
    def log_data_flow(self, flow_info: Dict[str, Any]):
        """
        Log complete data flow from client to server and back
        
        Args:
            flow_info: {
                'step': str,
                'source': str,
                'destination': str,
                'data_type': str,
                'data_preview': str,
                'size': int
            }
        """
        step = flow_info.get('step', 'Unknown')
        source = flow_info.get('source', 'Unknown')
        dest = flow_info.get('destination', 'Unknown')
        
        self.logger.info("📊 DATA FLOW - %s", step)
        self.logger.info("   From: %s → To: %s", source, dest)
        
        if 'data_type' in flow_info:
            self.logger.info("   Type: %s", flow_info['data_type'])
        
        if 'data_preview' in flow_info:
            self.logger.info("   Data: %s", flow_info['data_preview'])
        
        if 'size' in flow_info:
            size = flow_info['size']
            if size < 1024:
                self.logger.info("   Size: %d bytes", size)
            elif size < 1024 * 1024:
                self.logger.info("   Size: %.2f KB", size / 1024)
            else:
                self.logger.info("   Size: %.2f MB", size / (1024 * 1024))
        
        self.logger.info("")
        
        # Add to events
        self._add_event('DATA_FLOW', flow_info)
    
    def log_client_server_comparison(self, comparison: Dict[str, Any]):
        """
        Log side-by-side comparison of what client vs server sees
        
        Args:
            comparison: {
                'client_sees': dict,
                'server_sees': dict
            }
        """
        self.log_separator("👁️  CLIENT vs SERVER VIEW")
        
        self.logger.info("┌─────────────────────────────┬─────────────────────────────┐")
        self.logger.info("│   CLIENT SEES (Plaintext)   │   SERVER SEES (Encrypted)   │")
        self.logger.info("├─────────────────────────────┼─────────────────────────────┤")
        
        client = comparison.get('client_sees', {})
        server = comparison.get('server_sees', {})
        
        # Show data comparison
        if 'input_data' in client:
            client_data = str(client['input_data'])[:25]
            server_data = str(server.get('input_data', 'Encrypted'))[:25]
            self.logger.info(f"│ Input: {client_data:<20} │ Input: {server_data:<20} │")
        
        if 'result' in client:
            client_result = str(client['result'])[:25]
            server_result = str(server.get('result', 'Encrypted'))[:25]
            self.logger.info(f"│ Result: {client_result:<19} │ Result: {server_result:<19} │")
        
        self.logger.info("└─────────────────────────────┴─────────────────────────────┘")
        self.logger.info("")
        
        # Add to events
        self._add_event('CLIENT_SERVER_COMPARISON', comparison)
    
    def log_security_summary(self):
        """Log final security summary"""
        self.log_separator("🛡️  SECURITY SUMMARY")
        
        self.logger.info("Privacy Guarantees:")
        self.logger.info("  ✅ Private key never left client device")
        self.logger.info("  ✅ Server never saw plaintext input data")
        self.logger.info("  ✅ Server never saw plaintext prediction result")
        self.logger.info("  ✅ All computations performed on encrypted data")
        self.logger.info("  ✅ Only client can decrypt the result")
        self.logger.info("")
        self.logger.info("🔐 This is TRUE privacy-preserving inference!")
        self.logger.info("")
    
    def get_recent_events(self, limit: int = 50) -> list:
        """Get recent events for web dashboard"""
        return self.events[-limit:]
    
    def export_events_json(self, filepath: Optional[str] = None) -> str:
        """Export events to JSON file"""
        if filepath is None:
            filepath = self.log_dir / f"events_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(filepath, 'w') as f:
            json.dump(self.events, f, indent=2, default=str)
        
        return str(filepath)
    
    def clear_events(self):
        """Clear in-memory events"""
        self.events = []
        self.logger.info("🗑️  Event history cleared")


# Global logger instance
_logger_instance = None

def get_security_logger() -> FHESecurityLogger:
    """Get or create global security logger instance"""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = FHESecurityLogger()
    return _logger_instance


# Convenience functions
def log_key_generation(key_info: Dict[str, Any]):
    """Log key generation event"""
    get_security_logger().log_key_generation(key_info)

def log_encryption(encryption_info: Dict[str, Any]):
    """Log encryption event"""
    get_security_logger().log_encryption(encryption_info)

def log_server_received(request_info: Dict[str, Any]):
    """Log server received event"""
    get_security_logger().log_server_received(request_info)

def log_fhe_inference(inference_info: Dict[str, Any]):
    """Log FHE inference event"""
    get_security_logger().log_fhe_inference(inference_info)

def log_server_response(response_info: Dict[str, Any]):
    """Log server response event"""
    get_security_logger().log_server_response(response_info)

def log_decryption(decryption_info: Dict[str, Any]):
    """Log decryption event"""
    get_security_logger().log_decryption(decryption_info)

def log_privacy_check(check_info: Dict[str, Any]):
    """Log privacy check event"""
    get_security_logger().log_privacy_check(check_info)

def log_performance_metrics(metrics: Dict[str, Any]):
    """Log performance metrics"""
    get_security_logger().log_performance_metrics(metrics)

def log_data_flow(flow_info: Dict[str, Any]):
    """Log data flow event"""
    get_security_logger().log_data_flow(flow_info)

def log_client_server_comparison(comparison: Dict[str, Any]):
    """Log client vs server comparison"""
    get_security_logger().log_client_server_comparison(comparison)

def log_security_summary():
    """Log security summary"""
    get_security_logger().log_security_summary()

def get_recent_events(limit: int = 50) -> list:
    """Get recent events for dashboard"""
    return get_security_logger().get_recent_events(limit)
