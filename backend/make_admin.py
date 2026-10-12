import sqlite3
conn = sqlite3.connect(r'xuedazi/backend/xuedazi.db')
conn.execute("INSERT OR REPLACE INTO users (openid, nickname, role, auth_status, school) VALUES ('admin_openid', '管理员', 1, 'approved', '武汉大学')")
conn.commit()
print('管理员已创建')
conn.close()
