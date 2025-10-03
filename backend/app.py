from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime
import uuid

app = Flask(__name__)
CORS(app)
app.config['JSON_AS_ASCII'] = False  # 确保中文正常显示

print("=" * 50)
print("🚀 AI学习搭子MVP启动")
print("📍 后端地址: http://localhost:5000")
print("=" * 50)

# 内存存储
users = {}
chat_sessions = {}

# 预定义回复
RESPONSES = {
    "hello": "👋 你好！我是你的AI学习搭子，有什么我可以帮你的吗？",
    "学习": "📚 学习需要持之以恒！我可以帮你：\n• 制定学习计划\n• 解答学习问题\n• 跟踪学习进度",
    "计划": "🎯 让我们制定学习计划吧！请告诉我：\n1. 你的学习目标\n2. 可用时间\n3. 当前水平",
    "帮助": "🤔 我可以帮助你：\n• 学习规划\n• 问题解答\n• 进度跟踪\n• 情感支持",
    "数学": "🧮 数学学习建议：\n• 每天练习基础题\n• 理解概念而非死记\n• 定期复习错题",
    "编程": "💻 编程学习建议：\n• 多写代码实践\n• 阅读优秀源码\n• 参与开源项目",
    "英语": "🔤 英语学习建议：\n• 每天背单词\n• 多听多说\n• 阅读英文文章"
}

@app.route('/')
def home():
    return jsonify({
        "message": "AI学习搭子服务运行正常",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/health')
def health():
    return jsonify({"status": "healthy"})

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    
    if not username or not password:
        return jsonify({"success": False, "error": "用户名和密码不能为空"})
    
    if username in users:
        return jsonify({"success": False, "error": "用户名已存在"})
    
    user_id = str(uuid.uuid4())
    users[username] = {
        "id": user_id,
        "password": password,
        "created_at": datetime.now().isoformat()
    }
    
    # 初始化聊天会话
    chat_sessions[user_id] = []
    
    return jsonify({
        "success": True,
        "message": "注册成功",
        "user_id": user_id
    })

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    
    if not username or not password:
        return jsonify({"success": False, "error": "用户名和密码不能为空"})
    
    user = users.get(username)
    if user and user['password'] == password:
        return jsonify({
            "success": True,
            "message": "登录成功",
            "user": {
                "id": user["id"],
                "username": username
            }
        })
    else:
        return jsonify({"success": False, "error": "用户名或密码错误"})

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    user_id = data.get('user_id')
    message = data.get('message', '').strip()
    
    if not user_id or not message:
        return jsonify({"success": False, "error": "参数不完整"})
    
    # 生成AI回复
    ai_response = "🤖 我理解你的问题了！在完整版本中，我会调用AI模型提供更精准的回答。"
    
    # 关键词匹配
    message_lower = message.lower()
    for key in RESPONSES:
        if key in message_lower:
            ai_response = RESPONSES[key]
            break
    
    # 存储聊天记录
    chat_record = {
        "user_message": message,
        "ai_response": ai_response,
        "timestamp": datetime.now().strftime("%H:%M:%S")
    }
    
    if user_id not in chat_sessions:
        chat_sessions[user_id] = []
    
    chat_sessions[user_id].append(chat_record)
    
    return jsonify({
        "success": True,
        "response": ai_response,
        "history": chat_sessions[user_id][-10:]  # 返回最近10条
    })

@app.route('/api/chat/history', methods=['GET'])
def get_chat_history():
    user_id = request.args.get('user_id')
    
    if not user_id:
        return jsonify({"success": False, "error": "需要用户ID"})
    
    history = chat_sessions.get(user_id, [])
    return jsonify({
        "success": True,
        "history": history[-10:]
    })

@app.route('/api/users/count', methods=['GET'])
def get_users_count():
    return jsonify({
        "success": True,
        "count": len(users)
    })

if __name__ == '__main__':
    # 添加演示用户
    users["demo"] = {
        "id": "demo-user-id",
        "password": "demo123",
        "created_at": datetime.now().isoformat()
    }
    chat_sessions["demo-user-id"] = [
        {
            "user_message": "你好",
            "ai_response": "👋 你好！我是AI学习搭子，很高兴为你服务！",
            "timestamp": datetime.now().strftime("%H:%M:%S")
        }
    ]
    
    print("👤 演示账号: demo / demo123")
    app.run(debug=True, port=5000, host='127.0.0.1')