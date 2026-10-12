# -*- coding: utf-8 -*-
"""初始化数据库并创建管理员账号"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from db import init_db, get_db, DB_PATH

if os.path.exists(DB_PATH):
    os.remove(DB_PATH)
init_db()
conn = get_db()
conn.execute(
    "INSERT OR REPLACE INTO users (openid, nickname, role, school, auth_status) VALUES (?, ?, 1, ?, 'approved')",
    ('admin_openid', '管理员', 'SUSTECH'),
)
conn.commit()
print('admin:', [dict(r) for r in conn.execute('SELECT openid, nickname, role FROM users').fetchall()])
conn.close()
