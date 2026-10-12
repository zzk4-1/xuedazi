"""端到端 API 测试：模拟多用户完整闭环"""
import urllib.request
import urllib.parse
import json

BASE = 'http://127.0.0.1:5000/api'

def req(method, path, data=None, openid=None):
    url = BASE + path
    if '?' in url:
        base_part, qs = url.split('?', 1)
        url = base_part + '?' + urllib.parse.quote(qs, safe='=&')
    if openid:
        sep = '&' if '?' in url else '?'
        url += f'{sep}openid={openid}'
    body = json.dumps(data).encode('utf-8') if data else None
    r = urllib.request.Request(url, data=body, method=method)
    r.add_header('Content-Type', 'application/json')
    with urllib.request.urlopen(r) as resp:
        return json.loads(resp.read().decode('utf-8'))

# 1. 两个用户注册
print('=== 1. 用户注册 ===')
u1 = req('POST', '/login', {'openid': 'user_alice', 'nickname': '林一', 'avatar': ''})
u2 = req('POST', '/login', {'openid': 'user_bob', 'nickname': '阿橙', 'avatar': ''})
print('Alice:', u1['data']['openid'])
print('Bob:', u2['data']['openid'])

# 2. 选择学校
print('\n=== 2. 选择学校 ===')
print(req('POST', '/user/school', {'school': 'SUSTECH'}, 'user_alice')['msg'])
print(req('POST', '/user/school', {'school': 'SUSTECH'}, 'user_bob')['msg'])

# 3. 提交认证
print('\n=== 3. 提交认证 ===')
print(req('POST', '/user/auth', {}, 'user_alice')['msg'])
print(req('POST', '/user/auth', {}, 'user_bob')['msg'])

# 4. 管理员通过认证
print('\n=== 4. 管理员审批认证 ===')
pending = req('GET', '/admin/auth/pending', None, 'admin_openid')
print('待审批:', [p['nickname'] for p in pending['data']])
for p in pending['data']:
    print(req('POST', f'/admin/auth/{p["openid"]}', {'action': 'approve'}, 'admin_openid')['msg'])

# 5. Alice 发布卡片
print('\n=== 5. 发布卡片 ===')
card = req('POST', '/cards', {
    'type': 'goal',
    'title': '考研数学 daily 打卡搭子',
    'category': '考研',
    'description': '每天上午+晚上一起学数学，互相监督',
    'start_date': '2026-10-12',
    'end_date': '2026-12-20',
    'slots': ['Morning', 'Evening'],
    'place': '东图书馆三楼',
    'target_count': 3
}, 'user_alice')
print('发布:', card['msg'], 'card_id=', card['data']['card_id'])
card_id = card['data']['card_id']

# 6. Bob 浏览广场
print('\n=== 6. 浏览广场 ===')
cards = req('GET', '/cards?school=SUSTECH', None, 'user_bob')
print('广场卡片数:', len(cards['data']))
for c in cards['data']:
    print(' -', c['title'], c['joined_count'], '/', c['target_count'] + 1)

# 7. Bob 申请加入
print('\n=== 7. 申请加入 ===')
apply = req('POST', f'/cards/{card_id}/apply', {'message': '我也考数三，节奏一致，求带！'}, 'user_bob')
print('申请:', apply['msg'])

# 8. Alice 审批通过
print('\n=== 8. 队长审批 ===')
apps = req('GET', '/applications', None, 'user_alice')
print('收到申请:', len(apps['data']['received']))
app_id = apps['data']['received'][0]['id']
print('通过:', req('POST', f'/applications/{app_id}/handle', {'action': 'approve'}, 'user_alice')['msg'])

# 9. 双方打卡
print('\n=== 9. 打卡 ===')
print('Alice:', req('POST', f'/cards/{card_id}/checkin', {'text': '今天刷完高数第二章'}, 'user_alice')['msg'])
print('Bob:', req('POST', f'/cards/{card_id}/checkin', {'text': '线代第三章错题整理完毕'}, 'user_bob')['msg'])
ci = req('GET', f'/cards/{card_id}/checkins', None, 'user_alice')
print('今日打卡数:', len(ci['data']['checkins']), '连续天数:', ci['data']['streaks'])

# 10. 私聊
print('\n=== 10. 私聊 ===')
chats_alice = req('GET', '/chats', None, 'user_alice')
print('Alice 会话数:', len(chats_alice['data']))
chat_id = chats_alice['data'][0]['id']
print('Bob 发消息:', req('POST', f'/chats/{chat_id}/send', {'content': '今天数学学到哪了？'}, 'user_bob')['msg'])
msgs = req('GET', f'/chats/{chat_id}', None, 'user_alice')
print('Alice 收到消息数:', len(msgs['data']['messages']), '内容:', msgs['data']['messages'][-1]['content'])

# 11. 举报
print('\n=== 11. 举报 ===')
print(req('POST', '/reports', {'target_type': 'card', 'target_id': card_id, 'reason': 'Spam / ads'}, 'user_bob')['msg'])
reports = req('GET', '/admin/reports', None, 'admin_openid')
print('待处理举报:', len(reports['data']))
if reports['data']:
    rid = reports['data'][0]['id']
    print('处理举报:', req('POST', f'/admin/reports/{rid}', {'action': 'offline_card', 'result': '违规卡片已下架'}, 'admin_openid')['msg'])

print('\n=== 全部通过 ===')
