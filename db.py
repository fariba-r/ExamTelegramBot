import sqlite3

def setup_database():
    conn = sqlite3.connect('quiz_bot.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS user (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tel_id VARCHAR(20) NOT NULL,
            firstname TEXT NOT NULL,
            lastname TEXT NOT NULL,
            username TEXT
        )
    ''')
    c.execute('''
    CREATE TABLE IF NOT EXISTS exam (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        time INTEGER NOT NULL,
        status BOOLEAN DEFAULT TRUE
    )
    ''')
    c.execute('''
    CREATE TABLE IF NOT EXISTS questions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        text_question TEXT NOT NULL,
        case1 TEXT NOT NULL,
        case2 TEXT NOT NULL,
        case3 TEXT NOT NULL,
        case4 TEXT NOT NULL,
        answer INTEGER NOT NULL,
        image BLOB,
        exam_id INTEGER,
        FOREIGN KEY (exam_id) REFERENCES exam (id)
    )
    ''')
    c.execute('''
    CREATE TABLE IF NOT EXISTS result (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        exam_id INTEGER,
        correct INTEGER,
        falsee INTEGER,
        nulll INTEGER,
        percentt INTEGER,
        FOREIGN KEY (user_id) REFERENCES user (id),
        FOREIGN KEY (exam_id) REFERENCES exam (id)
    )
    ''')
    conn.commit()
    conn.close()
