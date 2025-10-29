import sqlite3
import json
import time
from typing import Optional, Dict, List
from datetime import datetime


class DatabaseManager:
    """Manages all database operations with user isolation"""

    def __init__(self, db_path: str = "eduai_sessions.db", user_id: Optional[int] = None):
        self.db_path = db_path
        self.user_id = user_id
        self.session_id = None
        self.init_database()
        
        # Create or load session for this user
        if self.user_id:
            self._init_user_session()

    def init_database(self):
        """Initialize all database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Sessions table - now includes user_id
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                session_name TEXT DEFAULT 'Untitled Session',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_accessed DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """
        )

        # App state table (vectorstore status, chat state, etc.)
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS app_state (
                session_id TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                vectorstore_ready BOOLEAN DEFAULT 0,
                chat_state TEXT,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES sessions (session_id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """
        )

        # Conversation history table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS conversation_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES sessions (session_id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """
        )

        # Documents table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                filename TEXT NOT NULL,
                file_size INTEGER,
                uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES sessions (session_id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """
        )

        # Generated content table (notes, MCQs, etc.)
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS generated_content (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                content_type TEXT NOT NULL,
                content TEXT NOT NULL,
                generated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES sessions (session_id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """
        )

        # Create indexes for better performance
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_sessions_user_id 
            ON sessions(user_id)
        """
        )
        
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_conversation_session 
            ON conversation_history(session_id, user_id)
        """
        )
        
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_documents_session 
            ON documents(session_id, user_id)
        """
        )
        
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_generated_content_session 
            ON generated_content(session_id, user_id)
        """
        )

        conn.commit()
        conn.close()

    def _init_user_session(self):
        """Initialize or load the most recent session for current user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Try to get the most recent session for this user
        cursor.execute(
            """
            SELECT session_id FROM sessions 
            WHERE user_id = ?
            ORDER BY last_accessed DESC 
            LIMIT 1
        """,
            (self.user_id,),
        )

        result = cursor.fetchone()

        if result:
            self.session_id = result[0]
            # Update last accessed time
            cursor.execute(
                """
                UPDATE sessions 
                SET last_accessed = CURRENT_TIMESTAMP 
                WHERE session_id = ? AND user_id = ?
            """,
                (self.session_id, self.user_id),
            )
        else:
            # Create a new session for this user
            self.session_id = f"session_{int(time.time() * 1000000)}"
            cursor.execute(
                """
                INSERT INTO sessions (session_id, user_id, session_name)
                VALUES (?, ?, ?)
            """,
                (self.session_id, self.user_id, "New Session"),
            )

        conn.commit()
        conn.close()

    def get_session_id(self) -> str:
        """Get current session ID"""
        return self.session_id

    def create_session(self, session_id: str, session_name: str = "Untitled Session"):
        """Create a new session for current user"""
        if not self.user_id:
            raise ValueError("User ID is required to create a session")
            
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO sessions (session_id, user_id, session_name)
            VALUES (?, ?, ?)
        """,
            (session_id, self.user_id, session_name),
        )

        conn.commit()
        conn.close()

        self.session_id = session_id

    def rename_session(self, session_id: str, new_name: str):
        """Rename a session (only if it belongs to current user)"""
        if not self.user_id:
            return
            
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE sessions 
            SET session_name = ? 
            WHERE session_id = ? AND user_id = ?
        """,
            (new_name, session_id, self.user_id),
        )

        conn.commit()
        conn.close()

    def get_all_sessions(self) -> List[Dict]:
        """Get all sessions for current user"""
        if not self.user_id:
            return []
            
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT 
                s.session_id,
                s.session_name,
                s.created_at,
                s.last_accessed,
                COUNT(DISTINCT ch.id) as message_count
            FROM sessions s
            LEFT JOIN conversation_history ch 
                ON s.session_id = ch.session_id AND ch.user_id = s.user_id
            WHERE s.user_id = ?
            GROUP BY s.session_id
            ORDER BY s.last_accessed DESC
        """,
            (self.user_id,),
        )

        sessions = []
        for row in cursor.fetchall():
            sessions.append(
                {
                    "session_id": row[0],
                    "session_name": row[1],
                    "created_at": row[2],
                    "last_accessed": row[3],
                    "message_count": row[4],
                }
            )

        conn.close()
        return sessions

    def delete_session(self, session_id: Optional[str] = None):
        """Delete a session and all its data (only if it belongs to current user)"""
        if not self.user_id:
            return
            
        if session_id is None:
            session_id = self.session_id

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Delete session (CASCADE will handle related records)
        cursor.execute(
            """
            DELETE FROM sessions 
            WHERE session_id = ? AND user_id = ?
        """,
            (session_id, self.user_id),
        )

        conn.commit()
        conn.close()

        # If we deleted the current session, create a new one
        if session_id == self.session_id:
            self._init_user_session()

    def save_app_state(
        self, vectorstore_ready: bool = False, chat_state: Optional[str] = None
    ):
        """Save application state for current session"""
        if not self.user_id or not self.session_id:
            return
            
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT OR REPLACE INTO app_state 
            (session_id, user_id, vectorstore_ready, chat_state, updated_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        """,
            (self.session_id, self.user_id, vectorstore_ready, chat_state),
        )

        conn.commit()
        conn.close()

    def get_app_state(self, session_id: Optional[str] = None) -> Optional[Dict]:
        """Get application state for a session"""
        if not self.user_id:
            return None
            
        if session_id is None:
            session_id = self.session_id

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT vectorstore_ready, chat_state 
            FROM app_state 
            WHERE session_id = ? AND user_id = ?
        """,
            (session_id, self.user_id),
        )

        result = cursor.fetchone()
        conn.close()

        if result:
            return {"vectorstore_ready": bool(result[0]), "chat_state": result[1]}
        return None

    def save_message(self, role: str, content: str):
        """Save a message to conversation history"""
        if not self.user_id or not self.session_id:
            return
            
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO conversation_history 
            (session_id, user_id, role, content)
            VALUES (?, ?, ?, ?)
        """,
            (self.session_id, self.user_id, role, content),
        )

        # Update session last accessed time
        cursor.execute(
            """
            UPDATE sessions 
            SET last_accessed = CURRENT_TIMESTAMP 
            WHERE session_id = ? AND user_id = ?
        """,
            (self.session_id, self.user_id),
        )

        conn.commit()
        conn.close()

    def get_conversation_history(
        self, session_id: Optional[str] = None, limit: Optional[int] = None
    ) -> List[Dict]:
        """Get conversation history for a session"""
        if not self.user_id:
            return []
            
        if session_id is None:
            session_id = self.session_id

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        query = """
            SELECT role, content, timestamp 
            FROM conversation_history 
            WHERE session_id = ? AND user_id = ?
            ORDER BY timestamp ASC
        """

        if limit:
            query += f" LIMIT {limit}"

        cursor.execute(query, (session_id, self.user_id))

        history = []
        for row in cursor.fetchall():
            history.append(
                {"role": row[0], "content": row[1], "timestamp": row[2]}
            )

        conn.close()
        return history

    def clear_conversation(self, session_id: Optional[str] = None):
        """Clear conversation history for a session"""
        if not self.user_id:
            return
            
        if session_id is None:
            session_id = self.session_id

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            DELETE FROM conversation_history 
            WHERE session_id = ? AND user_id = ?
        """,
            (session_id, self.user_id),
        )

        conn.commit()
        conn.close()

    def save_document(self, filename: str, file_size: int):
        """Save document metadata"""
        if not self.user_id or not self.session_id:
            return
            
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO documents 
            (session_id, user_id, filename, file_size)
            VALUES (?, ?, ?, ?)
        """,
            (self.session_id, self.user_id, filename, file_size),
        )

        conn.commit()
        conn.close()

    def get_documents(self, session_id: Optional[str] = None) -> List[Dict]:
        """Get all documents for a session"""
        if not self.user_id:
            return []
            
        if session_id is None:
            session_id = self.session_id

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT filename, file_size, uploaded_at 
            FROM documents 
            WHERE session_id = ? AND user_id = ?
            ORDER BY uploaded_at DESC
        """,
            (session_id, self.user_id),
        )

        documents = []
        for row in cursor.fetchall():
            documents.append(
                {
                    "filename": row[0],
                    "file_size": row[1],
                    "uploaded_at": row[2],
                }
            )

        conn.close()
        return documents

    def save_generated_content(self, content_type: str, content: str):
        """Save generated content (notes, MCQs, etc.)"""
        if not self.user_id or not self.session_id:
            return
            
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Delete existing content of same type for this session
        cursor.execute(
            """
            DELETE FROM generated_content 
            WHERE session_id = ? AND user_id = ? AND content_type = ?
        """,
            (self.session_id, self.user_id, content_type),
        )

        # Insert new content
        cursor.execute(
            """
            INSERT INTO generated_content 
            (session_id, user_id, content_type, content)
            VALUES (?, ?, ?, ?)
        """,
            (self.session_id, self.user_id, content_type, content),
        )

        conn.commit()
        conn.close()

    def get_generated_content(
        self, content_type: str, session_id: Optional[str] = None
    ) -> Optional[str]:
        """Get generated content of a specific type"""
        if not self.user_id:
            return None
            
        if session_id is None:
            session_id = self.session_id

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT content 
            FROM generated_content 
            WHERE session_id = ? AND user_id = ? AND content_type = ?
            ORDER BY generated_at DESC 
            LIMIT 1
        """,
            (session_id, self.user_id, content_type),
        )

        result = cursor.fetchone()
        conn.close()

        return result[0] if result else None

    def get_all_generated_content(
        self, session_id: Optional[str] = None
    ) -> List[Dict]:
        """Get all generated content for a session"""
        if not self.user_id:
            return []
            
        if session_id is None:
            session_id = self.session_id

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT content_type, content, generated_at 
            FROM generated_content 
            WHERE session_id = ? AND user_id = ?
            ORDER BY generated_at DESC
        """,
            (session_id, self.user_id),
        )

        contents = []
        for row in cursor.fetchall():
            contents.append(
                {
                    "content_type": row[0],
                    "content": row[1],
                    "generated_at": row[2],
                }
            )

        conn.close()
        return contents

    def cleanup_old_sessions(self, days_old: int = 30):
        """Delete sessions older than specified days for current user"""
        if not self.user_id:
            return
            
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            DELETE FROM sessions 
            WHERE user_id = ? 
            AND last_accessed < datetime('now', '-' || ? || ' days')
        """,
            (self.user_id, days_old),
        )

        deleted_count = cursor.rowcount
        conn.commit()
        conn.close()

        return deleted_count

    def get_user_statistics(self) -> Dict:
        """Get statistics for current user"""
        if not self.user_id:
            return {}
            
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        stats = {}

        # Total sessions
        cursor.execute(
            "SELECT COUNT(*) FROM sessions WHERE user_id = ?", 
            (self.user_id,)
        )
        stats["total_sessions"] = cursor.fetchone()[0]

        # Total messages
        cursor.execute(
            "SELECT COUNT(*) FROM conversation_history WHERE user_id = ?",
            (self.user_id,)
        )
        stats["total_messages"] = cursor.fetchone()[0]

        # Total documents
        cursor.execute(
            "SELECT COUNT(*) FROM documents WHERE user_id = ?", 
            (self.user_id,)
        )
        stats["total_documents"] = cursor.fetchone()[0]

        # Total generated content
        cursor.execute(
            "SELECT COUNT(*) FROM generated_content WHERE user_id = ?",
            (self.user_id,)
        )
        stats["total_generated_content"] = cursor.fetchone()[0]

        conn.close()
        return stats
