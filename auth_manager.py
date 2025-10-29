import sqlite3
import hashlib
import secrets
from typing import Optional, Dict
from datetime import datetime, timedelta


class AuthManager:
    """Manages user authentication and session management"""

    def __init__(self, db_path: str = "eduai_users.db"):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """Initialize authentication database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create users table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_login DATETIME
            )
        """
        )

        # Create sessions table for managing login sessions
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS user_sessions (
                session_token TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                expires_at DATETIME NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """
        )

        conn.commit()
        conn.close()

    def _hash_password(self, password: str, salt: str) -> str:
        """Hash password with salt using SHA-256"""
        return hashlib.sha256((password + salt).encode()).hexdigest()

    def _generate_salt(self) -> str:
        """Generate a random salt for password hashing"""
        return secrets.token_hex(16)

    def create_user(self, username: str, email: str, password: str) -> Dict:
        """Create a new user account"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Check if username or email already exists
            cursor.execute(
                "SELECT id FROM users WHERE username = ? OR email = ?",
                (username, email),
            )
            if cursor.fetchone():
                return {
                    "success": False,
                    "error": "Username or email already exists",
                }

            # Validate inputs
            if len(username) < 3:
                return {
                    "success": False,
                    "error": "Username must be at least 3 characters",
                }
            if len(password) < 6:
                return {
                    "success": False,
                    "error": "Password must be at least 6 characters",
                }
            if "@" not in email:
                return {"success": False, "error": "Invalid email format"}

            # Create user
            salt = self._generate_salt()
            password_hash = self._hash_password(password, salt)

            cursor.execute(
                """
                INSERT INTO users (username, email, password_hash, salt)
                VALUES (?, ?, ?, ?)
            """,
                (username, email, password_hash, salt),
            )

            user_id = cursor.lastrowid
            conn.commit()

            return {
                "success": True,
                "user_id": user_id,
                "username": username,
                "email": email,
            }

        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            conn.close()

    def authenticate_user(self, username: str, password: str) -> Dict:
        """Authenticate user and create session"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Get user by username or email
            cursor.execute(
                """
                SELECT id, username, email, password_hash, salt
                FROM users
                WHERE username = ? OR email = ?
            """,
                (username, username),
            )

            user = cursor.fetchone()

            if not user:
                return {"success": False, "error": "Invalid username or password"}

            user_id, username, email, stored_hash, salt = user

            # Verify password
            password_hash = self._hash_password(password, salt)
            if password_hash != stored_hash:
                return {"success": False, "error": "Invalid username or password"}

            # Update last login
            cursor.execute(
                "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?",
                (user_id,),
            )

            # Create session token
            session_token = secrets.token_urlsafe(32)
            expires_at = datetime.now() + timedelta(days=7)

            cursor.execute(
                """
                INSERT INTO user_sessions (session_token, user_id, expires_at)
                VALUES (?, ?, ?)
            """,
                (session_token, user_id, expires_at),
            )

            conn.commit()

            return {
                "success": True,
                "user_id": user_id,
                "username": username,
                "email": email,
                "session_token": session_token,
            }

        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            conn.close()

    def verify_session(self, session_token: str) -> Optional[Dict]:
        """Verify if session token is valid and not expired"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                SELECT us.user_id, u.username, u.email, us.expires_at
                FROM user_sessions us
                JOIN users u ON us.user_id = u.id
                WHERE us.session_token = ?
            """,
                (session_token,),
            )

            result = cursor.fetchone()

            if not result:
                return None

            user_id, username, email, expires_at = result

            # Check if session expired
            expires_at_dt = datetime.fromisoformat(expires_at)
            if expires_at_dt < datetime.now():
                # Clean up expired session
                cursor.execute(
                    "DELETE FROM user_sessions WHERE session_token = ?",
                    (session_token,),
                )
                conn.commit()
                return None

            return {
                "user_id": user_id,
                "username": username,
                "email": email,
                "session_token": session_token,
            }

        finally:
            conn.close()

    def logout(self, session_token: str):
        """Logout user by deleting session token"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            "DELETE FROM user_sessions WHERE session_token = ?", (session_token,)
        )

        conn.commit()
        conn.close()

    def cleanup_expired_sessions(self):
        """Remove all expired sessions from database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            "DELETE FROM user_sessions WHERE expires_at < CURRENT_TIMESTAMP"
        )

        conn.commit()
        conn.close()
