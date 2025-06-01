from dataBase.postgreSQL import db
import uuid

def generate_default_title():
    conn = db.get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT COUNT(*) FROM chat_sessions
            WHERE title LIKE '新對話 %'
        """)
        count = cur.fetchone()[0]
        return f"新對話 {count + 1}"
    finally:
        cur.close()
        db.release_connection(conn)


def create_session(title=None):
    conn = db.get_connection()
    cur = conn.cursor()
    try:
        session_id = str(uuid.uuid4())
        cur.execute("""
            INSERT INTO chat_sessions (id, title) VALUES (%s, %s)
        """, (session_id, title))
        conn.commit()
        return session_id
    finally:
        cur.close()
        db.release_connection(conn)


def insert_message(session_id, sender, message):
    conn = db.get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO chat_messages (session_id, sender, message)
            VALUES (%s, %s, %s)
        """, (session_id, sender, message))
        conn.commit()
    finally:
        cur.close()
        db.release_connection(conn)


def get_session_messages(session_id):
    conn = db.get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT sender, message, created_at FROM chat_messages
            WHERE session_id = %s
            ORDER BY created_at ASC
        """, (session_id,))
        return cur.fetchall()
    finally:
        cur.close()
        db.release_connection(conn)


def get_all_sessions():
    conn = db.get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT id, title, created_at
            FROM chat_sessions
            ORDER BY created_at DESC
        """)
        return cur.fetchall()
    finally:
        cur.close()
        db.release_connection(conn)


def update_session_title(session_id, new_title):
    conn = db.get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            UPDATE chat_sessions
            SET title = %s
            WHERE id = %s
        """, (new_title, session_id))
        conn.commit()
    finally:
        cur.close()
        db.release_connection(conn)


def delete_session(session_id):
    conn = db.get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            DELETE FROM chat_messages
            WHERE session_id = %s
        """, (session_id,))
        cur.execute("""
            DELETE FROM chat_sessions
            WHERE id = %s
        """, (session_id,))
        conn.commit()
    finally:
        cur.close()
        db.release_connection(conn)