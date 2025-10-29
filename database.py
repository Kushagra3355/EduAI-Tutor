import sqlite3
import json
import time
from typing import List, Dict, Optional
from pathlib import Path


class DatabaseManager:
    """Manages SQLite database for storing conversation history and application state with user isolation"""

    def __init__(self, db_path: str = "eduai_data.db", user_id: Optional[int] = None):
        self.db_path = db_path
        self.user_id = user_id
        self.init_database()

    def init_database(self):
        """Initialize database tables if they don't exist"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create conversations table with user_id
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # Create app_state table for storing application state with user_id
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS app_state (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                vectorstore_ready BOOLEAN DEFAULT 0,
                chat_state TEXT,
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(session_id, user_id)
            )
        """
        )

        # Create documents table to track uploaded documents with user_id
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                filename TEXT NOT NULL,
                file_size INTEGER,
                upload_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # Create generated_content table for notes and MCQs with user_id
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS generated_content (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                content_type TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # Create sessions table for session management with user_id
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                session_name TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_accessed DATETIME DEFAULT CURRENT_TIMESTAMP,
                message_count INTEGER DEFAULT 0,
                PRIMARY KEY (session_id, user_id)
            )
        """
        )

        # Create indexes for better performance
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_conversations_session_user 
            ON conversations(session_id, user_id)
        """
        )
        
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_sessions_user 
            ON sessions(user_id, last_accessed DESC)
        """
        )
        
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_documents_session_user 
            ON documents(session_id, user_id)
        """
        )
        
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_generated_content_session_user 
            ON generated_content(session_id, user_id)
        """
        )

        conn.commit()
        conn.close()

    def get_session_id(self) -> str:
        """Generate or retrieve session ID"""
        import streamlit as st

        if "db_session_id" not in st.session_state:
            # Try to load most recent session for this user
            if self.user_id:
                sessions = self.get_all_sessions()
                if sessions:
                    st.session_state.db_session_id = sessions[0]["session_id"]
                else:
                    # Create new session
                    st.session_state.db_session_id = f"session_{self.user_id}_{int(time.time() * 1000000)}"
                    self.create_session(st.session_state.db_session_id)
            else:
                # Should not happen in normal flow
                raise ValueError("Cannot create session without user_id")
                
        return st.session_state.db_session_id

    def create_session(self, session_id: str, session_name: Optional[str] = None):
        """Create a new session entry for current user"""
        if session_name is None:
            session_name = "New Session"

        if not self.user_id:
            raise ValueError("Cannot create session without user_id")

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                INSERT OR IGNORE INTO sessions (session_id, user_id, session_name, created_at, last_accessed)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """,
                (session_id, self.user_id, session_name),
            )
            conn.commit()
        except Exception as e:
            print(f"Error creating session: {e}")
            raise
        finally:
            conn.close()

    def update_session_access(self, session_id: Optional[str] = None):
        """Update last accessed time for a session"""
        if session_id is None:
            session_id = self.get_session_id()

        if not self.user_id:
            return

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE sessions 
            SET last_accessed = CURRENT_TIMESTAMP
            WHERE session_id = ? AND user_id = ?
        """,
            (session_id, self.user_id),
        )

        conn.commit()
        conn.close()

    def get_all_sessions(self) -> List[Dict]:
        """Get list of all sessions for current user with metadata"""
        if not self.user_id:
            return []

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT s.session_id, s.session_name, s.created_at, s.last_accessed,
                   COUNT(c.id) as message_count
            FROM sessions s
            LEFT JOIN conversations c ON s.session_id = c.session_id AND c.user_id = s.user_id
            WHERE s.user_id = ?
            GROUP BY s.session_id
            ORDER BY s.last_accessed DESC
        """,
            (self.user_id,),
        )

        rows = cursor.fetchall()
        conn.close()

        return [
            {
                "session_id": row[0],
                "session_name": row[1],
                "created_at": row[2],
                "last_accessed": row[3],
                "message_count": row[4],
            }
            for row in rows
        ]

    def rename_session(self, session_id: str, new_name: str):
        """Rename a session (only if it belongs to current user)"""
        if not self.user_id:
            return

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            "UPDATE sessions SET session_name = ? WHERE session_id = ? AND user_id = ?",
            (new_name, session_id, self.user_id),
        )

        conn.commit()
        conn.close()

    def save_message(self, role: str, content: str, session_id: Optional[str] = None):
        """Save a chat message to the database"""
        if session_id is None:
            session_id = self.get_session_id()

        if not self.user_id:
            raise ValueError("Cannot save message without user_id")

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO conversations (session_id, user_id, role, content)
            VALUES (?, ?, ?, ?)
        """,
            (session_id, self.user_id, role, content),
        )

        conn.commit()
        conn.close()

        self.update_session_access(session_id)

    def get_conversation_history(
        self, session_id: Optional[str] = None, limit: Optional[int] = None
    ) -> List[Dict[str, str]]:
        """Retrieve conversation history from the database for current user"""
        if session_id is None:
            session_id = self.get_session_id()

        if not self.user_id:
            return []

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if limit:
            cursor.execute(
                """
                SELECT role, content, timestamp
                FROM conversations
                WHERE session_id = ? AND user_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """,
                (session_id, self.user_id, limit),
            )
            rows = cursor.fetchall()
            rows.reverse()
        else:
            cursor.execute(
                """
                SELECT role, content, timestamp
                FROM conversations
                WHERE session_id = ? AND user_id = ?
                ORDER BY timestamp ASC
            """,
                (session_id, self.user_id),
            )
            rows = cursor.fetchall()

        conn.close()

        return [
            {"role": row[0], "content": row[1], "timestamp": row[2]} for row in rows
        ]

    def clear_conversation(self, session_id: Optional[str] = None):
        """Clear conversation history for a session (only for current user)"""
        if session_id is None:
            session_id = self.get_session_id()

        if not self.user_id:
            return

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            "DELETE FROM conversations WHERE session_id = ? AND user_id = ?", 
            (session_id, self.user_id)
        )

        conn.commit()
        conn.close()

    def save_app_state(
        self,
        vectorstore_ready: bool,
        chat_state: Optional[Dict] = None,
        session_id: Optional[str] = None,
    ):
        """Save application state to the database"""
        if session_id is None:
            session_id = self.get_session_id()

        if not self.user_id:
            raise ValueError("Cannot save app state without user_id")

        # Serialize chat state properly, handling LangChain message objects
        chat_state_json = None
        if chat_state:
            try:
                serialized_state = self._serialize_chat_state(chat_state)
                chat_state_json = json.dumps(serialized_state)
            except Exception as e:
                print(f"Warning: Could not serialize chat state: {e}")
                chat_state_json = None

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Use INSERT OR REPLACE with composite key
            cursor.execute(
                """
                INSERT OR REPLACE INTO app_state (session_id, user_id, vectorstore_ready, chat_state, last_updated)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
                (session_id, self.user_id, vectorstore_ready, chat_state_json),
            )
            conn.commit()
        finally:
            conn.close()

    def _serialize_chat_state(self, chat_state: Dict) -> Dict:
        """Serialize chat state, handling LangChain message objects"""
        from langchain_core.messages import (
            BaseMessage,
            SystemMessage,
            AIMessage,
            HumanMessage,
        )

        serialized = {}
        for key, value in chat_state.items():
            if key == "messages" and isinstance(value, list):
                # Serialize message objects
                serialized_messages = []
                for msg in value:
                    if isinstance(msg, BaseMessage):
                        if isinstance(msg, SystemMessage):
                            serialized_messages.append(
                                {"type": "system", "content": msg.content}
                            )
                        elif isinstance(msg, AIMessage):
                            serialized_messages.append(
                                {"type": "ai", "content": msg.content}
                            )
                        elif isinstance(msg, HumanMessage):
                            serialized_messages.append(
                                {"type": "human", "content": msg.content}
                            )
                        else:
                            serialized_messages.append(
                                {"type": "human", "content": str(msg.content)}
                            )
                    else:
                        serialized_messages.append(msg)
                serialized[key] = serialized_messages
            else:
                serialized[key] = value
        return serialized

    def get_app_state(self, session_id: Optional[str] = None) -> Optional[Dict]:
        """Retrieve application state from the database for current user"""
        if session_id is None:
            session_id = self.get_session_id()

        if not self.user_id:
            return None

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

        row = cursor.fetchone()
        conn.close()

        if row:
            chat_state = None
            if row[1]:
                try:
                    chat_state = json.loads(row[1])
                except Exception as e:
                    print(f"Warning: Could not deserialize chat state: {e}")
                    chat_state = None

            return {
                "vectorstore_ready": bool(row[0]),
                "chat_state": chat_state,
            }
        return None

    def save_generated_content(
        self,
        content_type: str,
        content: str,
        session_id: Optional[str] = None,
    ):
        """Save generated content (notes or MCQs) to the database"""
        if session_id is None:
            session_id = self.get_session_id()

        if not self.user_id:
            raise ValueError("Cannot save generated content without user_id")

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Delete old content of the same type for this session and user
        cursor.execute(
            "DELETE FROM generated_content WHERE session_id = ? AND user_id = ? AND content_type = ?",
            (session_id, self.user_id, content_type),
        )

        # Insert new content
        cursor.execute(
            """
            INSERT INTO generated_content (session_id, user_id, content_type, content)
            VALUES (?, ?, ?, ?)
        """,
            (session_id, self.user_id, content_type, content),
        )

        conn.commit()
        conn.close()

    def get_generated_content(
        self, content_type: str, session_id: Optional[str] = None
    ) -> Optional[str]:
        """Retrieve generated content from the database for current user"""
        if session_id is None:
            session_id = self.get_session_id()

        if not self.user_id:
            return None

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT content
            FROM generated_content
            WHERE session_id = ? AND user_id = ? AND content_type = ?
            ORDER BY timestamp DESC
            LIMIT 1
        """,
            (session_id, self.user_id, content_type),
        )

        row = cursor.fetchone()
        conn.close()

        return row[0] if row else None

    def save_document(
        self,
        filename: str,
        file_size: int,
        session_id: Optional[str] = None,
    ):
        """Save document metadata to the database"""
        if session_id is None:
            session_id = self.get_session_id()

        if not self.user_id:
            raise ValueError("Cannot save document without user_id")

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO documents (session_id, user_id, filename, file_size)
            VALUES (?, ?, ?, ?)
        """,
            (session_id, self.user_id, filename, file_size),
        )

        conn.commit()
        conn.close()

    def get_documents(self, session_id: Optional[str] = None) -> List[Dict]:
        """Retrieve document metadata from the database for current user"""
        if session_id is None:
            session_id = self.get_session_id()

        if not self.user_id:
            return []

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT filename, file_size, upload_timestamp
            FROM documents
            WHERE session_id = ? AND user_id = ?
            ORDER BY upload_timestamp DESC
        """,
            (session_id, self.user_id),
        )

        rows = cursor.fetchall()
        conn.close()

        return [
            {"filename": row[0], "file_size": row[1], "upload_timestamp": row[2]}
            for row in rows
        ]

    def delete_session(self, session_id: Optional[str] = None):
        """Delete all data for a session (only for current user)"""
        if session_id is None:
            session_id = self.get_session_id()

        if not self.user_id:
            return

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            "DELETE FROM conversations WHERE session_id = ? AND user_id = ?", 
            (session_id, self.user_id)
        )
        cursor.execute(
            "DELETE FROM app_state WHERE session_id = ? AND user_id = ?", 
            (session_id, self.user_id)
        )
        cursor.execute(
            "DELETE FROM documents WHERE session_id = ? AND user_id = ?", 
            (session_id, self.user_id)
        )
        cursor.execute(
            "DELETE FROM generated_content WHERE session_id = ? AND user_id = ?", 
            (session_id, self.user_id)
        )
        cursor.execute(
            "DELETE FROM sessions WHERE session_id = ? AND user_id = ?", 
            (session_id, self.user_id)
        )

        conn.commit()
        conn.close()

        # If current session was deleted, clear from session state
        import streamlit as st
        if "db_session_id" in st.session_state and st.session_state.db_session_id == session_id:
            del st.session_state.db_session_id
            # Will be recreated on next get_session_id() call
