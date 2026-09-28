import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:root123@localhost:5432/collab_editor"
)


class DBUnavailable(Exception):
    pass


def get_conn():
    try:
        return psycopg2.connect(
            DATABASE_URL,
            cursor_factory=RealDictCursor
        )
    except Exception as e:
        raise DBUnavailable(f"Database connection failed.\n{e}")


# ---------------------------------------------------
# ROOMS
# ---------------------------------------------------

def ensure_room(room_id, language="python"):
    conn = get_conn()

    try:
        with conn.cursor() as cur:

            cur.execute("""
                INSERT INTO rooms(room_id, language)
                VALUES(%s,%s)
                ON CONFLICT(room_id)
                DO NOTHING
            """, (room_id, language))

            cur.execute("""
                INSERT INTO documents(room_id,content)
                VALUES(%s,'')
                ON CONFLICT(room_id)
                DO NOTHING
            """, (room_id,))

        conn.commit()

    except Exception as e:
        conn.rollback()
        print(e)

    finally:
        conn.close()


def room_exists(room_id):

    conn = get_conn()

    try:

        with conn.cursor() as cur:

            cur.execute("""
            SELECT room_id
            FROM rooms
            WHERE room_id=%s
            """, (room_id,))

            return cur.fetchone() is not None

    finally:
        conn.close()


def delete_room(room_id):

    conn = get_conn()

    try:

        with conn.cursor() as cur:

            cur.execute("""
            DELETE FROM rooms
            WHERE room_id=%s
            """, (room_id,))

        conn.commit()

    finally:

        conn.close()


# ---------------------------------------------------
# DOCUMENT
# ---------------------------------------------------

def get_document_content(room_id):

    ensure_room(room_id)

    conn = get_conn()

    try:

        with conn.cursor() as cur:

            cur.execute("""
            SELECT content
            FROM documents
            WHERE room_id=%s
            """, (room_id,))

            row = cur.fetchone()

            if row:

                return row["content"]

            return ""

    finally:

        conn.close()


def save_document_content(room_id, content):

    ensure_room(room_id)

    conn = get_conn()

    try:

        with conn.cursor() as cur:

            cur.execute("""
            UPDATE documents
            SET content=%s,
                updated_at=NOW()
            WHERE room_id=%s
            """, (content, room_id))

        conn.commit()

    finally:

        conn.close()


# ---------------------------------------------------
# LANGUAGE
# ---------------------------------------------------

def get_room_language(room_id):

    ensure_room(room_id)

    conn = get_conn()

    try:

        with conn.cursor() as cur:

            cur.execute("""
            SELECT language
            FROM rooms
            WHERE room_id=%s
            """, (room_id,))

            row = cur.fetchone()

            if row:

                return row["language"]

            return "python"

    finally:

        conn.close()


def set_room_language(room_id, language):

    ensure_room(room_id)

    conn = get_conn()

    try:

        with conn.cursor() as cur:

            cur.execute("""
            UPDATE rooms
            SET language=%s
            WHERE room_id=%s
            """, (language, room_id))

        conn.commit()

    finally:

        conn.close()


# ---------------------------------------------------
# USER SESSION
# ---------------------------------------------------

def user_join(room_id, username):

    ensure_room(room_id)

    conn = get_conn()

    try:

        with conn.cursor() as cur:

            cur.execute("""
            INSERT INTO room_sessions(
            room_id,
            username
            )
            VALUES(%s,%s)
            """, (room_id, username))

        conn.commit()

    finally:

        conn.close()


def user_leave(room_id, username):

    conn = get_conn()

    try:

        with conn.cursor() as cur:

            cur.execute("""
            UPDATE room_sessions
            SET left_at=NOW()
            WHERE room_id=%s
            AND username=%s
            AND left_at IS NULL
            """, (room_id, username))

        conn.commit()

    finally:

        conn.close()


# ---------------------------------------------------
# DEBUG
# ---------------------------------------------------

def test_connection():

    try:

        conn = get_conn()

        print("✅ PostgreSQL Connected Successfully")

        conn.close()

        return True

    except Exception as e:

        print(e)

        return False


if __name__ == "__main__":

    test_connection()