# --- postgres_client.py ---

import psycopg2

class PostgresClient:
    def __init__(self):
        self.conn = psycopg2.connect(
            dbname="postgres",
            user="postgres",
            password="123",
            host="localhost",
            port="5432"
        )
        self.cursor = self.conn.cursor()
        self.create_table()

    def create_table(self):
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS tracking (
            id SERIAL PRIMARY KEY,
            person_id INT,
            enter_time TIMESTAMP,
            exit_time TIMESTAMP,
            video_name TEXT,
            mongo_document_id TEXT
        );''')
        self.conn.commit()

    def log_id(self, pid, enter_time, exit_time, video_name,mongo_document_id):
        self.cursor.execute(
            "INSERT INTO tracking (person_id, enter_time, exit_time, video_name,mongo_document_id) VALUES (%s, %s, %s, %s,%s)",
            (pid, enter_time, exit_time, video_name,mongo_document_id)
        )
        self.conn.commit()