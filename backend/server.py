# -*- coding: utf-8 -*-
"""学搭子后端服务 - Flask API"""
import os
import json
from datetime import datetime, date
from functools import wraps

from flask import Flask, request, jsonify, g
from db import get_db, init_db, REPORT_REASONS

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

# ============ 工具函数 ============

def ok(data=None, msg='ok'):
    return jsonify({'code': 0, 'msg': msg, 'data': data})


def err(msg, code=1):
    return jsonify({'code': code, 'msg': msg, 'data': None})


def db_conn():
    if 'db' not in g:
        g.db = get_db()
    return g.db


@app.teardown_appcontext
def close_db(exception):
    db = g.pop('db', None)
    if db is not None:
        db.close()


def get_user(openid):
    db = db_conn()
    return db.execute('SELECT * FROM users WHERE openid = ?', (openid,)).fetchone()


def require_auth(f):
    """已登录且通过学生认证"""
    @wraps(f)
    def wrapper(*args, **kwargs):
        openid = request.headers.get('X-OpenID') or request.args.get('openid') or (request.get_json(silent=True) or {}).get('openid')
        if not openid:
            return err('Not logged in', 401)
        user = get_user(openid)
        if not user:
            return err('User not found', 401)
        if user['banned']:
            return err('Account banned', 403)
        if user['auth_status'] != 'approved':
            return err('Please complete student verification first', 403)
        g.user = user
        g.openid = openid
        return f(*args, **kwargs)
    return wrapper


def require_login(f):
    """已登录（允许访客浏览）"""
    @wraps(f)
    def wrapper(*args, **kwargs):
        openid = request.headers.get('X-OpenID') or request.args.get('openid') or (request.get_json(silent=True) or {}).get('openid')
        if not openid:
            return err('Not logged in', 401)
        user = get_user(openid)
        if not user:
            return err('User not found', 401)
        g.user = user
        g.openid = openid
        return f(*args, **kwargs)
    return wrapper


def require_admin(f):
    """管理员权限"""
    @wraps(f)
    def wrapper(*args, **kwargs):
        openid = request.headers.get('X-OpenID') or request.args.get('openid') or (request.get_json(silent=True) or {}).get('openid')
        if not openid:
            return err('Not logged in', 401)
        user = get_user(openid)
        if not user or user['role'] != 1:
            return err('Admin permission required', 403)
        g.user = user
        g.openid = openid
        return f(*args, **kwargs)
    return wrapper


def check_content(text):
    """内容安全检测占位：接入微信 msgSecCheck / imgSecCheck"""
    # TODO: 生产环境调用微信内容安全接口
    return True


def today_str():
    return date.today().isoformat()


def now_str():
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def row_to_dict(row):
    return dict(row) if row else None


# ============ 认证与用户 ============

@app.route('/api/login', methods=['POST'])
def login():
    """微信一键登录，首次自动注册"""
    data = request.get_json(silent=True) or {}
    openid = data.get('openid')
    if not openid:
        return err('Missing openid')
    nickname = data.get('nickname', '')
    avatar = data.get('avatar', '')
    db = db_conn()
    user = db.execute('SELECT * FROM users WHERE openid = ?', (openid,)).fetchone()
    if user:
        return ok({'openid': openid, 'nickname': user['nickname'], 'avatar': user['avatar'],
                   'school': user['school'], 'auth_status': user['auth_status'], 'role': user['role']})
    db.execute('INSERT INTO users (openid, nickname, avatar) VALUES (?,?,?)',
               (openid, nickname, avatar))
    db.commit()
    return ok({'openid': openid, 'nickname': nickname, 'avatar': avatar,
               'school': '', 'auth_status': 'none', 'role': 0})


@app.route('/api/user/profile', methods=['GET'])
@require_login
def get_profile():
    return ok(row_to_dict(g.user))


@app.route('/api/user/school', methods=['POST'])
@require_login
def set_school():
    data = request.get_json(silent=True) or {}
    school = data.get('school', '')
    db = db_conn()
    exists = db.execute('SELECT id FROM schools WHERE name = ?', (school,)).fetchone()
    if not exists:
        return err('Your school is not open yet; you can submit a request to open it')
    if g.user['auth_status'] == 'approved' and g.user['school'] != school:
        return err('School cannot be changed after verification; please resubmit verification to change it')
    db.execute('UPDATE users SET school = ? WHERE openid = ?', (school, g.openid))
    db.commit()
    return ok({'school': school})


@app.route('/api/user/profile', methods=['POST'])
@require_login
def update_profile():
    """更新昵称/头像"""
    data = request.get_json(silent=True) or {}
    nickname = (data.get('nickname') or '').strip()
    avatar = data.get('avatar', '')
    if nickname and len(nickname) > 20:
        return err('Nickname cannot exceed 20 characters')
    db = db_conn()
    if nickname:
        db.execute('UPDATE users SET nickname = ? WHERE openid = ?', (nickname, g.openid))
    if avatar:
        db.execute('UPDATE users SET avatar = ? WHERE openid = ?', (avatar, g.openid))
    db.commit()
    return ok()


@app.route('/api/schools', methods=['GET'])
def list_schools():
    db = db_conn()
    rows = db.execute('SELECT name FROM schools ORDER BY id').fetchall()
    return ok([r['name'] for r in rows])


@app.route('/api/user/auth', methods=['POST'])
@require_login
def submit_auth():
    """提交学生认证（模拟上传证件照）"""
    data = request.get_json(silent=True) or {}
    # MVP: 不做真实图片上传，记录模拟提交
    db = db_conn()
    db.execute("UPDATE users SET auth_status = 'pending', auth_reason = '' WHERE openid = ?", (g.openid,))
    db.commit()
    return ok({'auth_status': 'pending'})


@app.route('/api/user/auth/status', methods=['GET'])
@require_login
def auth_status():
    return ok({'auth_status': g.user['auth_status'], 'auth_reason': g.user['auth_reason']})


# ============ 搭子卡片 ============

@app.route('/api/cards', methods=['GET'])
@require_login
def list_cards():
    school = request.args.get('school') or g.user['school']
    if not school:
        return err('Please select a school first')
    category = request.args.get('category')
    slots = request.args.get('slots')  # comma separated
    db = db_conn()

    sql = """SELECT c.*, u.nickname as creator_nickname, u.avatar as creator_avatar,
                    (SELECT COUNT(*) FROM card_members cm WHERE cm.card_id = c.id) as joined_count
             FROM cards c JOIN users u ON c.creator_openid = u.openid
             WHERE c.school = ? AND c.status = 'recruiting'"""
    args = [school]
    if category:
        sql += ' AND c.category = ?'
        args.append(category)
    sql += ' ORDER BY c.created_at DESC'
    rows = db.execute(sql, args).fetchall()

    # 时段过滤：卡片需包含全部所选时段
    if slots:
        wanted = set(slots.split(','))
        rows = [r for r in rows if wanted.issubset(set(json.loads(r['slots'])))]
    return ok([dict(r) for r in rows])


@app.route('/api/cards', methods=['POST'])
@require_auth
def create_card():
    data = request.get_json(silent=True) or {}
    title = (data.get('title') or '').strip()
    card_type = data.get('type')
    category = data.get('category')
    description = (data.get('description') or '').strip()
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    slots = data.get('slots') or []
    place = (data.get('place') or '').strip()
    target_count = data.get('target_count')

    if not title or len(title) > 20:
        return err('Please enter a title within 20 characters')
    if card_type not in ('goal', 'place'):
        return err('Invalid type')
    if not category:
        return err('Please select a category')
    if not start_date or not end_date:
        return err('Please select a date range')
    try:
        d1 = datetime.strptime(start_date, '%Y-%m-%d').date()
        d2 = datetime.strptime(end_date, '%Y-%m-%d').date()
    except ValueError:
        return err('Invalid date format')
    if d1 < date.today():
        return err('Start date cannot be earlier than today')
    if d2 <= d1:
        return err('End date must be later than start date')
    if (d2 - d1).days > 180:
        return err('Date range cannot exceed 180 days')
    if not slots:
        return err('Please select at least one time slot')
    for s in slots:
        if s not in ('Early morning', 'Morning', 'Afternoon', 'Evening'):
            return err('Invalid time slot')
    if not place:
        return err('Please enter an on-campus location')
    if not isinstance(target_count, int) or target_count < 1 or target_count > 10:
        return err('Partner count must be a number between 1 and 10')

    if not check_content(title) or not check_content(description):
        return err('Content contains prohibited information; please revise and try again')

    db = db_conn()
    # 数量限制
    recruiting = db.execute(
        "SELECT COUNT(*) as c FROM cards WHERE creator_openid = ? AND status = 'recruiting'",
        (g.openid,)).fetchone()['c']
    if recruiting >= 2:
        return err('You can publish at most 2 recruiting cards at the same time')

    cur = db.execute('''INSERT INTO cards
        (creator_openid, type, title, category, description, start_date, end_date, slots, place, target_count, school)
        VALUES (?,?,?,?,?,?,?,?,?,?,?)''',
        (g.openid, card_type, title, category, description, start_date, end_date,
         json.dumps(slots, ensure_ascii=False), place, target_count, g.user['school']))
    card_id = cur.lastrowid
    # 队长自动入队
    db.execute('INSERT INTO card_members (card_id, openid) VALUES (?,?)', (card_id, g.openid))
    db.commit()
    return ok({'card_id': card_id})


@app.route('/api/cards/<int:card_id>', methods=['GET'])
@require_login
def get_card(card_id):
    db = db_conn()
    card = db.execute('''SELECT c.*, u.nickname as creator_nickname, u.avatar as creator_avatar
                         FROM cards c JOIN users u ON c.creator_openid = u.openid
                         WHERE c.id = ?''', (card_id,)).fetchone()
    if not card:
        return err('Card not found', 404)
    card = dict(card)
    card['slots'] = json.loads(card['slots'])
    members = db.execute('''SELECT u.openid, u.nickname, u.avatar, cm.joined_at
                            FROM card_members cm JOIN users u ON cm.openid = u.openid
                            WHERE cm.card_id = ? ORDER BY cm.joined_at''', (card_id,)).fetchall()
    card['members'] = [dict(m) for m in members]
    card['joined_count'] = len(members)
    # 当前用户是否已申请
    app_row = db.execute('''SELECT id, status FROM applications
                            WHERE card_id = ? AND applicant_openid = ? AND status IN ('pending','approved')''',
                         (card_id, g.openid)).fetchone()
    card['my_application'] = row_to_dict(app_row)
    card['is_creator'] = card['creator_openid'] == g.openid
    return ok(card)


@app.route('/api/cards/<int:card_id>/apply', methods=['POST'])
@require_auth
def apply_card(card_id):
    data = request.get_json(silent=True) or {}
    message = (data.get('message') or '').strip()
    if not message or len(message) > 50:
        return err('Please enter an application message within 50 characters')
    if not check_content(message):
        return err('The message contains prohibited information')
    db = db_conn()
    card = db.execute('SELECT * FROM cards WHERE id = ?', (card_id,)).fetchone()
    if not card:
        return err('Card not found', 404)
    if card['status'] != 'recruiting':
        return err('This card is not accepting applications')
    if card['creator_openid'] == g.openid:
        return err('You cannot apply to your own card')
    existing = db.execute('''SELECT id FROM applications
                             WHERE card_id = ? AND applicant_openid = ? AND status IN ('pending','approved')''',
                          (card_id, g.openid)).fetchone()
    if existing:
        return err('You have already applied to this card')
    db.execute('INSERT INTO applications (card_id, applicant_openid, message) VALUES (?,?,?)',
               (card_id, g.openid, message))
    db.commit()
    return ok()


# ============ 申请审批 ============

@app.route('/api/applications', methods=['GET'])
@require_auth
def list_applications():
    """我发起的申请 + 我收到的申请（队长）"""
    db = db_conn()
    sent = db.execute('''SELECT a.*, c.title as card_title, c.status as card_status
                         FROM applications a JOIN cards c ON a.card_id = c.id
                         WHERE a.applicant_openid = ? ORDER BY a.created_at DESC''',
                      (g.openid,)).fetchall()
    received = db.execute('''SELECT a.*, c.title as card_title, u.nickname as applicant_nickname, u.avatar as applicant_avatar
                             FROM applications a
                             JOIN cards c ON a.card_id = c.id
                             JOIN users u ON a.applicant_openid = u.openid
                             WHERE c.creator_openid = ? ORDER BY a.created_at DESC''',
                          (g.openid,)).fetchall()
    return ok({'sent': [dict(r) for r in sent], 'received': [dict(r) for r in received]})


@app.route('/api/applications/<int:app_id>/handle', methods=['POST'])
@require_auth
def handle_application(app_id):
    data = request.get_json(silent=True) or {}
    action = data.get('action')  # approve / reject
    if action not in ('approve', 'reject'):
        return err('Invalid action')
    db = db_conn()
    app_row = db.execute('''SELECT a.*, c.creator_openid, c.status as card_status, c.target_count, c.title as card_title
                            FROM applications a JOIN cards c ON a.card_id = c.id
                            WHERE a.id = ?''', (app_id,)).fetchone()
    if not app_row:
        return err('Application not found', 404)
    if app_row['creator_openid'] != g.openid:
        return err('Only the team leader can handle applications', 403)
    if app_row['status'] != 'pending':
        return err('This application has already been handled')
    if app_row['card_status'] != 'recruiting':
        return err('This card has stopped recruiting')

    now = now_str()
    if action == 'approve':
        db.execute("UPDATE applications SET status = 'approved', handled_at = ? WHERE id = ?", (now, app_id))
        db.execute('INSERT OR IGNORE INTO card_members (card_id, openid) VALUES (?,?)',
                   (app_row['card_id'], app_row['applicant_openid']))
        # 检查是否满员
        joined = db.execute('SELECT COUNT(*) as c FROM card_members WHERE card_id = ?',
                            (app_row['card_id'],)).fetchone()['c']
        target = app_row['target_count'] + 1  # 含队长
        if joined >= target:
            db.execute("UPDATE cards SET status = 'full' WHERE id = ?", (app_row['card_id'],))
            # 其余待处理申请自动失效
            db.execute("UPDATE applications SET status = 'expired', handled_at = ? WHERE card_id = ? AND status = 'pending'",
                       (now, app_row['card_id']))
        # 自动建立私聊会话
        create_chat_if_not_exists(g.openid, app_row['applicant_openid'])
    else:
        db.execute("UPDATE applications SET status = 'rejected', handled_at = ? WHERE id = ?", (now, app_id))
    db.commit()
    return ok()


# ============ 打卡 ============

@app.route('/api/cards/<int:card_id>/checkin', methods=['POST'])
@require_auth
def checkin(card_id):
    data = request.get_json(silent=True) or {}
    text = (data.get('text') or '').strip()
    image_url = data.get('image_url', '')
    if not text or len(text) > 100:
        return err('Please enter check-in content within 100 characters')
    if not check_content(text):
        return err('Check-in content contains prohibited information')
    db = db_conn()
    member = db.execute('SELECT 1 FROM card_members WHERE card_id = ? AND openid = ?',
                        (card_id, g.openid)).fetchone()
    if not member:
        return err('You are not a member of this team yet', 403)
    card = db.execute('SELECT status FROM cards WHERE id = ?', (card_id,)).fetchone()
    if not card or card['status'] == 'finished':
        return err('This team has ended')
    today = today_str()
    exists = db.execute('SELECT id FROM checkins WHERE card_id = ? AND openid = ? AND date = ?',
                        (card_id, g.openid, today)).fetchone()
    if exists:
        return err('Already checked in today')
    db.execute('INSERT INTO checkins (card_id, openid, date, text, image_url) VALUES (?,?,?,?,?)',
               (card_id, g.openid, today, text, image_url))
    db.commit()
    return ok()


@app.route('/api/cards/<int:card_id>/checkins', methods=['GET'])
@require_auth
def list_checkins(card_id):
    db = db_conn()
    member = db.execute('SELECT 1 FROM card_members WHERE card_id = ? AND openid = ?',
                        (card_id, g.openid)).fetchone()
    if not member:
        return err('You are not a member of this team yet', 403)
    date_filter = request.args.get('date') or today_str()
    rows = db.execute('''SELECT ch.*, u.nickname, u.avatar FROM checkins ch
                         JOIN users u ON ch.openid = u.openid
                         WHERE ch.card_id = ? AND ch.date = ? ORDER BY ch.created_at''',
                      (card_id, date_filter)).fetchall()
    # 计算每个成员的连续天数
    members = db.execute('SELECT openid FROM card_members WHERE card_id = ?', (card_id,)).fetchall()
    streaks = {}
    for m in members:
        openid = m['openid']
        dates = db.execute('''SELECT DISTINCT date FROM checkins
                              WHERE card_id = ? AND openid = ? ORDER BY date DESC''',
                           (card_id, openid)).fetchall()
        streak = 0
        d = date.today()
        date_set = {r['date'] for r in dates}
        while d.isoformat() in date_set:
            streak += 1
            d = date.fromordinal(d.toordinal() - 1)
        streaks[openid] = streak
    return ok({'date': date_filter, 'checkins': [dict(r) for r in rows], 'streaks': streaks})


# ============ 我的小队 ============

@app.route('/api/teams', methods=['GET'])
@require_login
def my_teams():
    """我加入的小队（含我创建的）"""
    db = db_conn()
    rows = db.execute('''SELECT c.*, u.nickname as creator_nickname, u.avatar as creator_avatar,
                                (SELECT COUNT(*) FROM card_members cm WHERE cm.card_id = c.id) as joined_count
                         FROM cards c
                         JOIN card_members m ON m.card_id = c.id AND m.openid = ?
                         JOIN users u ON c.creator_openid = u.openid
                         ORDER BY c.created_at DESC''', (g.openid,)).fetchall()
    return ok([dict(r) for r in rows])


# ============ 私聊 ============

def create_chat_if_not_exists(a, b):
    db = db_conn()
    u1, u2 = sorted([a, b])
    row = db.execute('SELECT id FROM chats WHERE user1_openid = ? AND user2_openid = ?', (u1, u2)).fetchone()
    if row:
        return row['id']
    cur = db.execute('INSERT INTO chats (user1_openid, user2_openid) VALUES (?,?)', (u1, u2))
    return cur.lastrowid


@app.route('/api/chats', methods=['GET'])
@require_auth
def list_chats():
    db = db_conn()
    rows = db.execute('''SELECT c.*, u.nickname as peer_nickname, u.avatar as peer_avatar
                         FROM chats c
                         JOIN users u ON u.openid = CASE WHEN c.user1_openid = ? THEN c.user2_openid ELSE c.user1_openid END
                         WHERE c.user1_openid = ? OR c.user2_openid = ?
                         ORDER BY c.last_time DESC NULLS LAST''',
                      (g.openid, g.openid, g.openid)).fetchall()
    result = []
    for r in rows:
        r = dict(r)
        r['peer_openid'] = r['user2_openid'] if r['user1_openid'] == g.openid else r['user1_openid']
        r['unread'] = r['unread_user1'] if r['user1_openid'] == g.openid else r['unread_user2']
        result.append(r)
    return ok(result)


@app.route('/api/chats/<int:chat_id>', methods=['GET'])
@require_auth
def get_chat(chat_id):
    db = db_conn()
    chat = db.execute('SELECT * FROM chats WHERE id = ?', (chat_id,)).fetchone()
    if not chat:
        return err('Chat not found', 404)
    if g.openid not in (chat['user1_openid'], chat['user2_openid']):
        return err('Access denied', 403)
    # 标记已读
    if chat['user1_openid'] == g.openid:
        db.execute('UPDATE chats SET unread_user1 = 0 WHERE id = ?', (chat_id,))
    else:
        db.execute('UPDATE chats SET unread_user2 = 0 WHERE id = ?', (chat_id,))
    db.execute('UPDATE messages SET is_read = 1 WHERE chat_id = ? AND sender_openid != ?', (chat_id, g.openid))
    db.commit()
    messages = db.execute('''SELECT m.*, u.nickname as sender_nickname, u.avatar as sender_avatar
                             FROM messages m JOIN users u ON m.sender_openid = u.openid
                             WHERE m.chat_id = ? ORDER BY m.created_at''', (chat_id,)).fetchall()
    return ok({'chat': dict(chat), 'messages': [dict(m) for m in messages]})


@app.route('/api/chats/<int:chat_id>/send', methods=['POST'])
@require_auth
def send_message(chat_id):
    data = request.get_json(silent=True) or {}
    content = (data.get('content') or '').strip()
    image_url = data.get('image_url', '')
    if not content and not image_url:
        return err('Message cannot be empty')
    if content and len(content) > 200:
        return err('Message cannot exceed 200 characters')
    if content and not check_content(content):
        return err('Message contains prohibited information')
    db = db_conn()
    chat = db.execute('SELECT * FROM chats WHERE id = ?', (chat_id,)).fetchone()
    if not chat:
        return err('Chat not found', 404)
    if g.openid not in (chat['user1_openid'], chat['user2_openid']):
        return err('Access denied', 403)
    cur = db.execute('INSERT INTO messages (chat_id, sender_openid, content, image_url) VALUES (?,?,?,?)',
                     (chat_id, g.openid, content, image_url))
    # 更新会话最后消息与未读
    last_msg = content or '[Image]'
    if chat['user1_openid'] == g.openid:
        db.execute('UPDATE chats SET last_message = ?, last_time = ?, unread_user2 = unread_user2 + 1 WHERE id = ?',
                   (last_msg, now_str(), chat_id))
    else:
        db.execute('UPDATE chats SET last_message = ?, last_time = ?, unread_user1 = unread_user1 + 1 WHERE id = ?',
                   (last_msg, now_str(), chat_id))
    db.commit()
    return ok({'message_id': cur.lastrowid})


# ============ 举报 ============

@app.route('/api/reports', methods=['POST'])
@require_auth
def create_report():
    data = request.get_json(silent=True) or {}
    target_type = data.get('target_type')
    target_id = data.get('target_id')
    reason = data.get('reason')
    detail = (data.get('detail') or '').strip()
    if target_type not in ('card', 'user', 'message'):
        return err('Invalid report target type')
    if not reason or reason not in REPORT_REASONS:
        return err('Please select a report reason')
    if detail and len(detail) > 200:
        return err('Additional details cannot exceed 200 characters')
    db = db_conn()
    db.execute('INSERT INTO reports (reporter_openid, target_type, target_id, reason, detail) VALUES (?,?,?,?,?)',
               (g.openid, target_type, str(target_id), reason, detail))
    db.commit()
    return ok()


# ============ 管理端 ============

@app.route('/api/admin/auth/pending', methods=['GET'])
@require_admin
def admin_pending_auth():
    db = db_conn()
    rows = db.execute("SELECT openid, nickname, school, created_at FROM users WHERE auth_status = 'pending'").fetchall()
    return ok([dict(r) for r in rows])


@app.route('/api/admin/auth/<openid>', methods=['POST'])
@require_admin
def admin_handle_auth(openid):
    data = request.get_json(silent=True) or {}
    action = data.get('action')
    reason = data.get('reason', '')
    if action not in ('approve', 'reject'):
        return err('Invalid action')
    db = db_conn()
    status = 'approved' if action == 'approve' else 'rejected'
    db.execute('UPDATE users SET auth_status = ?, auth_reason = ? WHERE openid = ?',
               (status, reason, openid))
    db.commit()
    return ok()


@app.route('/api/admin/reports', methods=['GET'])
@require_admin
def admin_reports():
    db = db_conn()
    rows = db.execute('SELECT * FROM reports WHERE status = ? ORDER BY created_at DESC', ('pending',)).fetchall()
    return ok([dict(r) for r in rows])


@app.route('/api/admin/reports/<int:report_id>', methods=['POST'])
@require_admin
def admin_handle_report(report_id):
    data = request.get_json(silent=True) or {}
    action = data.get('action')  # offline_card / ban_user / reject
    result = data.get('result', '')
    db = db_conn()
    report = db.execute('SELECT * FROM reports WHERE id = ?', (report_id,)).fetchone()
    if not report:
        return err('Report not found', 404)
    if action == 'offline_card' and report['target_type'] == 'card':
        db.execute("UPDATE cards SET status = 'offline' WHERE id = ?", (report['target_id'],))
    elif action == 'ban_user' and report['target_type'] == 'user':
        db.execute('UPDATE users SET banned = 1 WHERE openid = ?', (report['target_id'],))
    elif action != 'reject':
        return err('Action does not match the report type')
    db.execute("UPDATE reports SET status = 'handled', result = ?, handled_at = ? WHERE id = ?",
               (result, now_str(), report_id))
    db.commit()
    return ok()


# ============ 启动 ============

if __name__ == '__main__':
    init_db()
    host = os.environ.get('HOST', '127.0.0.1')
    port = int(os.environ.get('PORT', 5000))
    print(f'学搭子后端启动: http://{host}:{port}')
    app.run(host=host, port=port, debug=False)
