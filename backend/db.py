"""SQLite 数据库连接与初始化"""
import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'xuedazi.db')

# 学校白名单（首期手动维护，按需扩充）
SCHOOL_WHITELIST = [
    'SUSTECH',
]

# 预设举报理由
REPORT_REASONS = ['Fake identity', 'Harassment', 'Spam / ads', 'Inappropriate content', 'Other']


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON')
    return conn


def init_db():
    conn = get_db()
    c = conn.cursor()

    # 用户表
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        openid TEXT PRIMARY KEY,
        nickname TEXT DEFAULT '',
        avatar TEXT DEFAULT '',
        school TEXT DEFAULT '',
        auth_status TEXT DEFAULT 'none',
        auth_reason TEXT DEFAULT '',
        role INTEGER DEFAULT 0,
        banned INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    # 学校白名单表
    c.execute('''CREATE TABLE IF NOT EXISTS schools (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL
    )''')

    # 搭子卡片
    c.execute('''CREATE TABLE IF NOT EXISTS cards (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        creator_openid TEXT NOT NULL,
        type TEXT NOT NULL,
        title TEXT NOT NULL,
        category TEXT NOT NULL,
        description TEXT DEFAULT '',
        start_date TEXT NOT NULL,
        end_date TEXT NOT NULL,
        slots TEXT NOT NULL,
        place TEXT NOT NULL,
        target_count INTEGER NOT NULL,
        school TEXT NOT NULL,
        status TEXT DEFAULT 'recruiting',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (creator_openid) REFERENCES users(openid)
    )''')

    # 卡片成员（含队长）
    c.execute('''CREATE TABLE IF NOT EXISTS card_members (
        card_id INTEGER NOT NULL,
        openid TEXT NOT NULL,
        joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (card_id, openid),
        FOREIGN KEY (card_id) REFERENCES cards(id),
        FOREIGN KEY (openid) REFERENCES users(openid)
    )''')

    # 报名申请
    c.execute('''CREATE TABLE IF NOT EXISTS applications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        card_id INTEGER NOT NULL,
        applicant_openid TEXT NOT NULL,
        message TEXT NOT NULL,
        status TEXT DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        handled_at TIMESTAMP,
        FOREIGN KEY (card_id) REFERENCES cards(id),
        FOREIGN KEY (applicant_openid) REFERENCES users(openid)
    )''')

    # 打卡记录
    c.execute('''CREATE TABLE IF NOT EXISTS checkins (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        card_id INTEGER NOT NULL,
        openid TEXT NOT NULL,
        date TEXT NOT NULL,
        text TEXT NOT NULL,
        image_url TEXT DEFAULT '',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE (card_id, openid, date),
        FOREIGN KEY (card_id) REFERENCES cards(id),
        FOREIGN KEY (openid) REFERENCES users(openid)
    )''')

    # 私聊会话
    c.execute('''CREATE TABLE IF NOT EXISTS chats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user1_openid TEXT NOT NULL,
        user2_openid TEXT NOT NULL,
        last_message TEXT DEFAULT '',
        last_time TIMESTAMP,
        unread_user1 INTEGER DEFAULT 0,
        unread_user2 INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE (user1_openid, user2_openid),
        FOREIGN KEY (user1_openid) REFERENCES users(openid),
        FOREIGN KEY (user2_openid) REFERENCES users(openid)
    )''')

    # 私聊消息
    c.execute('''CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chat_id INTEGER NOT NULL,
        sender_openid TEXT NOT NULL,
        content TEXT NOT NULL,
        image_url TEXT DEFAULT '',
        is_read INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (chat_id) REFERENCES chats(id),
        FOREIGN KEY (sender_openid) REFERENCES users(openid)
    )''')

    # 举报
    c.execute('''CREATE TABLE IF NOT EXISTS reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        reporter_openid TEXT NOT NULL,
        target_type TEXT NOT NULL,
        target_id TEXT NOT NULL,
        reason TEXT NOT NULL,
        detail TEXT DEFAULT '',
        status TEXT DEFAULT 'pending',
        result TEXT DEFAULT '',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        handled_at TIMESTAMP,
        FOREIGN KEY (reporter_openid) REFERENCES users(openid)
    )''')

    # 初始化学校白名单
    for name in SCHOOL_WHITELIST:
        c.execute('INSERT OR IGNORE INTO schools (name) VALUES (?)', (name,))

    conn.commit()
    conn.close()


if __name__ == '__main__':
    init_db()
    print('数据库初始化完成:', DB_PATH)
