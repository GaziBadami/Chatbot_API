"""
database_Conv.py
Handles ALL conversations table operations ONLY
"""

import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv

load_dotenv()

# ============================================
# CONNECTION
# ============================================

def get_db_connection():
    try:
        return mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=24253,
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", ""),
            database=os.getenv("DB_NAME", "chatbot_db"),
            connect_timeout=5
        )
    except Exception as e:
        print(f"DATABASE CONNECTION ERROR: {e}")
        return None


# ============================================
# GET ACTIVE CONVERSATION
# ============================================

def get_active_conversation(user_id: str):
    """
    Get the current active conversation for a user
    Returns None if no active conversation exists
    """
    conn = get_db_connection()
    if not conn:
        return None

    try:
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT * FROM conversations
            WHERE user_id = %s AND is_active = TRUE
            ORDER BY created_at DESC
            LIMIT 1
        """
        cursor.execute(query, (user_id,))
        conversation = cursor.fetchone()
        cursor.close()
        return conversation
    except Error as e:
        print(f"Error fetching active conversation: {e}")
        return None
    finally:
        conn.close()


# ============================================
# ENSURE ACTIVE CONVERSATION
# ============================================

def ensure_active_conversation(user_id: str):
    """
    Makes sure user always has an active conversation
    If none exists → creates one automatically
    Called before every /chat and /upload request
    """
    active = get_active_conversation(user_id)

    if not active:
        active = create_conversation(user_id=user_id, label="New Chat")

    return active


# ============================================
# CREATE CONVERSATION
# ============================================

def create_conversation(user_id: str, label: str = "New Chat"):
    """
    Creates a new conversation
    Deactivates ALL other conversations for this user first
    """
    conn = get_db_connection()
    if not conn:
        return None

    try:
        cursor = conn.cursor(dictionary=True)

        # Deactivate all existing conversations for this user
        cursor.execute(
            "UPDATE conversations SET is_active = FALSE, updated_at = NOW() WHERE user_id = %s AND is_active = TRUE",
            (user_id,)
        )

        # Insert new conversation
        cursor.execute(
            "INSERT INTO conversations (user_id, label, is_active) VALUES (%s, %s, TRUE)",
            (user_id, label)
        )
        conn.commit()

        # Fetch and return the new conversation
        new_id = cursor.lastrowid
        cursor.execute("SELECT * FROM conversations WHERE id = %s", (new_id,))
        new_conversation = cursor.fetchone()

        cursor.close()
        return new_conversation
    except Error as e:
        print(f"Error creating conversation: {e}")
        return None
    finally:
        conn.close()


# ============================================
# GET ALL CONVERSATIONS (for sidebar)
# ============================================

def get_all_conversations(user_id: str, limit: int = 50):
    """
    Get all conversations for a user
    Includes last message preview and message count
    Sorted by updated_at DESC (most recent first)
    """
    conn = get_db_connection()
    if not conn:
        return []

    try:
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT
                c.id,
                c.user_id,
                c.label,
                c.is_active,
                c.created_at,
                c.updated_at,
                COUNT(ch.id) as message_count,
                (
                    SELECT SUBSTRING(ch2.content, 1, 80)
                    FROM chat_history ch2
                    WHERE ch2.conversation_id = c.id
                    ORDER BY ch2.id DESC
                    LIMIT 1
                ) as last_message
            FROM conversations c
            LEFT JOIN chat_history ch ON ch.conversation_id = c.id
            WHERE c.user_id = %s
            GROUP BY c.id
            ORDER BY c.updated_at DESC
            LIMIT %s
        """
        cursor.execute(query, (user_id, limit))
        conversations = cursor.fetchall()
        cursor.close()
        return conversations
    except Error as e:
        print(f"Error fetching conversations: {e}")
        return []
    finally:
        conn.close()


# ============================================
# GET CONVERSATION BY ID
# ============================================

def get_conversation_by_id(conversation_id: int):
    """Get a single conversation by id"""
    conn = get_db_connection()
    if not conn:
        return None

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM conversations WHERE id = %s", (conversation_id,))
        conversation = cursor.fetchone()
        cursor.close()
        return conversation
    except Error as e:
        print(f"Error fetching conversation: {e}")
        return None
    finally:
        conn.close()


# ============================================
# SWITCH CONVERSATION (sidebar click)
# ============================================

def switch_conversation(user_id: str, conversation_id: int):
    """
    User clicks an old chat in sidebar
    → Deactivates all other conversations
    → Sets this one as active
    """
    conn = get_db_connection()
    if not conn:
        return False

    try:
        cursor = conn.cursor()

        # Deactivate all for this user
        cursor.execute(
            "UPDATE conversations SET is_active = FALSE, updated_at = NOW() WHERE user_id = %s",
            (user_id,)
        )

        # Activate the selected one
        cursor.execute(
            "UPDATE conversations SET is_active = TRUE, updated_at = NOW() WHERE id = %s AND user_id = %s",
            (conversation_id, user_id)
        )
        conn.commit()

        success = cursor.rowcount > 0
        cursor.close()
        return success
    except Error as e:
        print(f"Error switching conversation: {e}")
        return False
    finally:
        conn.close()


# ============================================
# RENAME CONVERSATION
# ============================================

def update_conversation_label(conversation_id: int, new_label: str):
    """Update label/title of a conversation"""
    conn = get_db_connection()
    if not conn:
        return False

    try:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE conversations SET label = %s, updated_at = NOW() WHERE id = %s",
            (new_label, conversation_id)
        )
        conn.commit()
        success = cursor.rowcount > 0
        cursor.close()
        return success
    except Error as e:
        print(f"Error updating label: {e}")
        return False
    finally:
        conn.close()


# ============================================
# ARCHIVE CONVERSATION
# ============================================

def archive_conversation(conversation_id: int):
    """Archive/close a conversation → sets is_active = FALSE"""
    conn = get_db_connection()
    if not conn:
        return False

    try:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE conversations SET is_active = FALSE, updated_at = NOW() WHERE id = %s",
            (conversation_id,)
        )
        conn.commit()
        success = cursor.rowcount > 0
        cursor.close()
        return success
    except Error as e:
        print(f"Error archiving conversation: {e}")
        return False
    finally:
        conn.close()


# ============================================
# DELETE CONVERSATION
# ============================================

def delete_conversation(conversation_id: int):
    """
    Delete a conversation record only
    Messages are deleted separately via ON DELETE CASCADE
    or explicitly in the API layer
    """
    conn = get_db_connection()
    if not conn:
        return False

    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM conversations WHERE id = %s", (conversation_id,))
        conn.commit()
        success = cursor.rowcount > 0
        cursor.close()
        return success
    except Error as e:
        print(f"Error deleting conversation: {e}")
        return False
    finally:
        conn.close()


# ============================================
# AUTO LABEL GENERATION
# ============================================

def update_label_if_default(conversation_id: int, new_label: str):
    """
    Only updates label if it's still the default 'New Chat'
    Called after first AI reply to auto-name the chat
    """
    conn = get_db_connection()
    if not conn:
        return False

    try:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE conversations SET label = %s, updated_at = NOW() WHERE id = %s AND label = 'New Chat'",
            (new_label, conversation_id)
        )
        conn.commit()
        updated = cursor.rowcount > 0
        cursor.close()
        return updated
    except Error as e:
        print(f"Error updating default label: {e}")
        return False
    finally:
        conn.close()


# ============================================
# ADMIN: GET ALL CONVERSATIONS (all users)
# ============================================

def get_all_conversations_admin(user_id: str = None, is_active: bool = None, page: int = 1, limit: int = 20):
    """
    Admin: get all conversations across all users
    Optional filters: user_id, is_active
    Paginated
    """
    conn = get_db_connection()
    if not conn:
        return [], 0

    try:
        cursor = conn.cursor(dictionary=True)

        conditions = []
        params = []

        if user_id:
            conditions.append("c.user_id = %s")
            params.append(user_id)
        if is_active is not None:
            conditions.append("c.is_active = %s")
            params.append(is_active)

        where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""

        # Total count
        cursor.execute(f"SELECT COUNT(*) as total FROM conversations c{where_clause}", params)
        total = cursor.fetchone()['total']

        # Paginated data with message count + last message
        offset = (page - 1) * limit
        query = f"""
            SELECT
                c.id,
                c.user_id,
                c.label,
                c.is_active,
                c.created_at,
                c.updated_at,
                COUNT(ch.id) as message_count,
                (
                    SELECT SUBSTRING(ch2.content, 1, 80)
                    FROM chat_history ch2
                    WHERE ch2.conversation_id = c.id
                    ORDER BY ch2.id DESC
                    LIMIT 1
                ) as last_message
            FROM conversations c
            LEFT JOIN chat_history ch ON ch.conversation_id = c.id
            {where_clause}
            GROUP BY c.id
            ORDER BY c.updated_at DESC
            LIMIT %s OFFSET %s
        """
        cursor.execute(query, params + [limit, offset])
        conversations = cursor.fetchall()

        cursor.close()
        return conversations, total
    except Error as e:
        print(f"Error fetching admin conversations: {e}")
        return [], 0
    finally:
        conn.close()


# ============================================
# ADMIN: SEARCH CONVERSATIONS BY LABEL
# ============================================

def search_conversations_by_label(keyword: str, page: int = 1, limit: int = 20):
    """Admin: search conversations by label keyword"""
    conn = get_db_connection()
    if not conn:
        return [], 0

    try:
        cursor = conn.cursor(dictionary=True)

        search_pattern = f"%{keyword}%"

        # Total count
        cursor.execute(
            "SELECT COUNT(*) as total FROM conversations WHERE label LIKE %s",
            (search_pattern,)
        )
        total = cursor.fetchone()['total']

        # Paginated results
        offset = (page - 1) * limit
        query = """
            SELECT
                c.id,
                c.user_id,
                c.label,
                c.is_active,
                c.created_at,
                c.updated_at,
                COUNT(ch.id) as message_count
            FROM conversations c
            LEFT JOIN chat_history ch ON ch.conversation_id = c.id
            WHERE c.label LIKE %s
            GROUP BY c.id
            ORDER BY c.updated_at DESC
            LIMIT %s OFFSET %s
        """
        cursor.execute(query, (search_pattern, limit, offset))
        conversations = cursor.fetchall()

        cursor.close()
        return conversations, total
    except Error as e:
        print(f"Error searching conversations: {e}")
        return [], 0
    finally:
        conn.close()