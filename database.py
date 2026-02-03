
import mysql.connector
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
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", ""),
            database=os.getenv("DB_NAME", "chatbot_db"),
            connect_timeout=5
        )
    except Exception as e:
        print(f"DATABASE CONNECTION ERROR: {e}")
        return None


# ============================================
# STORE MESSAGE
# ============================================

def store_message(user_id: str, role: str, content: str, conversation_id: int = None):
    """
    Insert a message into chat_history
    conversation_id is now passed directly - no more timestamp guessing
    """
    conn = get_db_connection()
    if not conn:
        print("Skipping store_message: No database connection.")
        return None

    try:
        cursor = conn.cursor()
        query = """
            INSERT INTO chat_history (user_id, role, content, conversation_id)
            VALUES (%s, %s, %s, %s)
        """
        cursor.execute(query, (user_id, role, content, conversation_id))
        conn.commit()
        message_id = cursor.lastrowid
        cursor.close()
        return message_id  # Return the new message id
    except Exception as e:
        print(f"Error storing message: {e}")
        return None
    finally:
        conn.close()


# ============================================
# GET CHAT HISTORY
# ============================================

def get_chat_history(user_id: str, conversation_id: int = None, limit: int = 15):
    """
    Get chat history for AI context
    If conversation_id is passed → get messages from THAT conversation only
    If not → fallback to user_id (old behavior for safety)
    """
    conn = get_db_connection()
    if not conn:
        return []

    try:
        cursor = conn.cursor(dictionary=True)

        if conversation_id:
            query = """
                SELECT role, content FROM chat_history
                WHERE user_id = %s AND conversation_id = %s
                ORDER BY id DESC
                LIMIT %s
            """
            cursor.execute(query, (user_id, conversation_id, limit))
        else:
            query = """
                SELECT role, content FROM chat_history
                WHERE user_id = %s
                ORDER BY id DESC
                LIMIT %s
            """
            cursor.execute(query, (user_id, limit))

        history = cursor.fetchall()
        cursor.close()
        return history[::-1]  # Reverse → chronological order for AI
    except Exception as e:
        print(f"Error fetching chat history: {e}")
        return []
    finally:
        conn.close()


# ============================================
# GET MESSAGES BY CONVERSATION (for sidebar load)
# ============================================

def get_messages_by_conversation(conversation_id: int, limit: int = 100):
    """
    Get all messages of a specific conversation
    Used when user clicks a chat in sidebar
    """
    conn = get_db_connection()
    if not conn:
        return []

    try:
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT id, user_id, role, content, conversation_id, created_at
            FROM chat_history
            WHERE conversation_id = %s
            ORDER BY id ASC
            LIMIT %s
        """
        cursor.execute(query, (conversation_id, limit))
        messages = cursor.fetchall()
        cursor.close()
        return messages
    except Exception as e:
        print(f"Error fetching messages: {e}")
        return []
    finally:
        conn.close()


# ============================================
# DELETE OPERATIONS
# ============================================

def delete_message_by_id(message_id: int):
    """Delete a single message by its id (admin use)"""
    conn = get_db_connection()
    if not conn:
        return False

    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM chat_history WHERE id = %s", (message_id,))
        conn.commit()
        success = cursor.rowcount > 0
        cursor.close()
        return success
    except Exception as e:
        print(f"Error deleting message: {e}")
        return False
    finally:
        conn.close()


def delete_messages_by_conversation(conversation_id: int):
    """Delete ALL messages of a conversation (used when deleting a chat)"""
    conn = get_db_connection()
    if not conn:
        return False

    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM chat_history WHERE conversation_id = %s", (conversation_id,))
        conn.commit()
        deleted_count = cursor.rowcount
        cursor.close()
        return deleted_count
    except Exception as e:
        print(f"Error deleting conversation messages: {e}")
        return False
    finally:
        conn.close()


# ============================================
# ADMIN: GET ALL MESSAGES (with filters)
# ============================================

def get_all_messages(user_id: str = None, role: str = None, conversation_id: int = None, page: int = 1, limit: int = 20):
    """
    Admin use: get messages with optional filters + pagination
    """
    conn = get_db_connection()
    if not conn:
        return [], 0

    try:
        cursor = conn.cursor(dictionary=True)

        # Build dynamic WHERE clause
        conditions = []
        params = []

        if user_id:
            conditions.append("user_id = %s")
            params.append(user_id)
        if role:
            conditions.append("role = %s")
            params.append(role)
        if conversation_id:
            conditions.append("conversation_id = %s")
            params.append(conversation_id)

        where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""

        # Get total count
        count_query = f"SELECT COUNT(*) as total FROM chat_history{where_clause}"
        cursor.execute(count_query, params)
        total = cursor.fetchone()['total']

        # Get paginated data
        offset = (page - 1) * limit
        data_query = f"""
            SELECT id, user_id, role, content, conversation_id, created_at
            FROM chat_history{where_clause}
            ORDER BY id DESC
            LIMIT %s OFFSET %s
        """
        cursor.execute(data_query, params + [limit, offset])
        messages = cursor.fetchall()

        cursor.close()
        return messages, total
    except Exception as e:
        print(f"Error fetching all messages: {e}")
        return [], 0
    finally:
        conn.close()