"""
Database management for local SQLite authentication.
Handles user registration, login, and password hashing.
"""

import sqlite3
import hashlib
import secrets
import os
from datetime import datetime
from pathlib import Path


class Database:
    """SQLite database manager for user authentication."""
    
    def __init__(self, db_path='data/users.db'):
        """Initialize database connection."""
        self.db_path = db_path
        
        # Ensure data directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize database
        self._init_db()
    
    def _init_db(self):
        """Create tables if they don't exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                full_name TEXT,
                auth_provider TEXT DEFAULT 'local',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                is_active BOOLEAN DEFAULT 1
            )
        ''')
        
        # Login attempts table (for security)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS login_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL,
                success BOOLEAN NOT NULL,
                ip_address TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        
        print("SQLite database initialized")
    
    def _hash_password(self, password, salt=None):
        """
        Hash password using SHA-256 with salt.
        
        Args:
            password: Plain text password
            salt: Salt for hashing (generated if None)
            
        Returns:
            Tuple of (hash, salt)
        """
        if salt is None:
            salt = secrets.token_hex(32)  # 64 character hex string
        
        # Use SHA-256 with salt
        password_salt = (password + salt).encode('utf-8')
        password_hash = hashlib.sha256(password_salt).hexdigest()
        
        return password_hash, salt
    
    def register_user(self, email, password, full_name=None):
        """
        Register a new user.
        
        Args:
            email: User email
            password: Plain text password
            full_name: Optional full name
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # Validate email
            if not email or '@' not in email:
                return False, "Invalid email address"
            
            # Validate password
            if not password or len(password) < 6:
                return False, "Password must be at least 6 characters"
            
            # Hash password
            password_hash, salt = self._hash_password(password)
            
            # Insert user
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO users (email, password_hash, salt, full_name, auth_provider)
                VALUES (?, ?, ?, ?, 'local')
            ''', (email, password_hash, salt, full_name))
            
            conn.commit()
            conn.close()
            
            return True, "User registered successfully"
            
        except sqlite3.IntegrityError:
            return False, "Email already registered"
        except Exception as e:
            return False, f"Registration failed: {str(e)}"
    
    def verify_user(self, email, password, ip_address=None):
        """
        Verify user credentials.
        
        Args:
            email: User email
            password: Plain text password
            ip_address: Optional IP address for logging
            
        Returns:
            Tuple of (success: bool, user_data: dict or None)
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get user
            cursor.execute('''
                SELECT id, email, password_hash, salt, full_name, auth_provider, created_at
                FROM users
                WHERE email = ? AND is_active = 1
            ''', (email,))
            
            user = cursor.fetchone()
            
            if not user:
                # Log failed attempt
                self._log_login_attempt(cursor, email, False, ip_address)
                conn.commit()
                conn.close()
                return False, None
            
            user_id, email, stored_hash, salt, full_name, auth_provider, created_at = user
            
            # Verify password
            password_hash, _ = self._hash_password(password, salt)
            
            if password_hash == stored_hash:
                # Update last login
                cursor.execute('''
                    UPDATE users
                    SET last_login = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (user_id,))
                
                # Log successful attempt
                self._log_login_attempt(cursor, email, True, ip_address)
                
                conn.commit()
                conn.close()
                
                # Return user data
                user_data = {
                    'id': user_id,
                    'email': email,
                    'full_name': full_name,
                    'auth_provider': auth_provider,
                    'created_at': created_at
                }
                
                return True, user_data
            else:
                # Log failed attempt
                self._log_login_attempt(cursor, email, False, ip_address)
                conn.commit()
                conn.close()
                return False, None
                
        except Exception as e:
            print(f"Error verifying user: {e}")
            return False, None
    
    def _log_login_attempt(self, cursor, email, success, ip_address):
        """Log login attempt for security monitoring."""
        cursor.execute('''
            INSERT INTO login_attempts (email, success, ip_address)
            VALUES (?, ?, ?)
        ''', (email, success, ip_address))
    
    def get_user_by_email(self, email):
        """
        Get user by email.
        
        Args:
            email: User email
            
        Returns:
            User data dict or None
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, email, full_name, auth_provider, created_at, last_login
                FROM users
                WHERE email = ? AND is_active = 1
            ''', (email,))
            
            user = cursor.fetchone()
            conn.close()
            
            if user:
                return {
                    'id': user[0],
                    'email': user[1],
                    'full_name': user[2],
                    'auth_provider': user[3],
                    'created_at': user[4],
                    'last_login': user[5]
                }
            return None
            
        except Exception as e:
            print(f"Error getting user: {e}")
            return None
    
    def get_login_attempts(self, email, hours=24):
        """
        Get recent login attempts for an email.
        
        Args:
            email: User email
            hours: Number of hours to look back
            
        Returns:
            List of login attempts
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT email, success, ip_address, timestamp
                FROM login_attempts
                WHERE email = ? AND timestamp > datetime('now', '-' || ? || ' hours')
                ORDER BY timestamp DESC
            ''', (email, hours))
            
            attempts = cursor.fetchall()
            conn.close()
            
            return [
                {
                    'email': a[0],
                    'success': bool(a[1]),
                    'ip_address': a[2],
                    'timestamp': a[3]
                }
                for a in attempts
            ]
            
        except Exception as e:
            print(f"Error getting login attempts: {e}")
            return []
    
    def register_firebase_user(self, email, full_name=None):
        """
        Register a user who logged in via Firebase.
        
        Args:
            email: User email
            full_name: Optional full name
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if user exists
            cursor.execute('SELECT id FROM users WHERE email = ?', (email,))
            existing = cursor.fetchone()
            
            if existing:
                # Update last login
                cursor.execute('''
                    UPDATE users
                    SET last_login = CURRENT_TIMESTAMP
                    WHERE email = ?
                ''', (email,))
                conn.commit()
                conn.close()
                return True, "User logged in"
            
            # Create new user with Firebase auth
            cursor.execute('''
                INSERT INTO users (email, password_hash, salt, full_name, auth_provider)
                VALUES (?, 'firebase', 'firebase', ?, 'firebase')
            ''', (email, full_name))
            
            conn.commit()
            conn.close()
            
            return True, "Firebase user registered"
            
        except Exception as e:
            return False, f"Firebase registration failed: {str(e)}"
    
    def get_stats(self):
        """Get database statistics."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Total users
            cursor.execute('SELECT COUNT(*) FROM users WHERE is_active = 1')
            total_users = cursor.fetchone()[0]
            
            # Users by provider
            cursor.execute('''
                SELECT auth_provider, COUNT(*) 
                FROM users 
                WHERE is_active = 1 
                GROUP BY auth_provider
            ''')
            users_by_provider = dict(cursor.fetchall())
            
            # Recent logins (24h)
            cursor.execute('''
                SELECT COUNT(*) 
                FROM login_attempts 
                WHERE success = 1 AND timestamp > datetime('now', '-24 hours')
            ''')
            recent_logins = cursor.fetchone()[0]
            
            # Failed attempts (24h)
            cursor.execute('''
                SELECT COUNT(*) 
                FROM login_attempts 
                WHERE success = 0 AND timestamp > datetime('now', '-24 hours')
            ''')
            failed_attempts = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                'total_users': total_users,
                'users_by_provider': users_by_provider,
                'recent_logins_24h': recent_logins,
                'failed_attempts_24h': failed_attempts
            }
            
        except Exception as e:
            print(f"Error getting stats: {e}")
            return {
                'total_users': 0,
                'users_by_provider': {},
                'recent_logins_24h': 0,
                'failed_attempts_24h': 0
            }


# Global database instance
db = Database()


if __name__ == "__main__":
    """Test database functionality."""
    print("Testing database...")
    
    # Test registration
    success, msg = db.register_user("test@example.com", "password123", "Test User")
    print(f"Registration: {msg}")
    
    # Test login
    success, user = db.verify_user("test@example.com", "password123")
    if success:
        print(f"Login successful: {user}")
    else:
        print("Login failed")
    
    # Test wrong password
    success, user = db.verify_user("test@example.com", "wrongpassword")
    print(f"Wrong password test: {'Failed (correct)' if not success else 'Passed (incorrect)'}")
    
    # Get stats
    stats = db.get_stats()
    print(f"Stats: {stats}")
