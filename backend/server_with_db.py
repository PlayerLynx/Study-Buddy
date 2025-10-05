from http.server import HTTPServer, BaseHTTPRequestHandler
import json
from urllib.parse import urlparse
import time
from database import db  # 导入数据库模块

class AIHandler(BaseHTTPRequestHandler):
    
    def do_OPTIONS(self):
        """处理CORS预检请求"""
        self.send_cors_headers(200)
    
    def do_GET(self):
        """处理GET请求"""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/api/health':
            self.handle_health_check()
        elif parsed_path.path == '/':
            self.handle_home()
        else:
            self.send_error(404, "接口不存在")
    
    def do_POST(self):
        """处理POST请求"""
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        try:
            data = json.loads(post_data.decode('utf-8'))
            parsed_path = urlparse(self.path)
            
            if parsed_path.path == '/api/login':
                self.handle_login(data)
            elif parsed_path.path == '/api/register':
                self.handle_register(data)
            elif parsed_path.path == '/api/chat':
                self.handle_chat(data)
            else:
                self.send_error(404, "接口不存在")
                
        except Exception as e:
            self.send_json_response({"success": False, "error": str(e)}, 400)
    
    def handle_health_check(self):
        """健康检查"""
        self.send_json_response({
            "status": "healthy", 
            "service": "AI学习搭子",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        })
    
    def handle_home(self):
        """首页"""
        self.send_json_response({
            "message": "AI学习搭子服务运行正常",
            "version": "1.1.0",
            "feature": "支持数据库持久化"
        })
    
    def handle_login(self, data):
        """处理登录"""
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        
        print(f"登录尝试: {username}")
        
        if not username or not password:
            self.send_json_response({"success": False, "error": "用户名和密码不能为空"})
            return
        
        user = db.verify_user(username, password)
        if user:
            print(f"登录成功: {username}")
            self.send_json_response({
                "success": True,
                "message": "登录成功",
                "user": user
            })
        else:
            self.send_json_response({"success": False, "error": "用户名或密码错误"})
    
    def handle_register(self, data):
        """处理注册"""
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        
        if not username or not password:
            self.send_json_response({"success": False, "error": "用户名和密码不能为空"})
            return
        
        user_id = db.create_user(username, password)
        if user_id:
            # 创建默认欢迎消息
            db.add_chat_message(user_id, "系统", "👋 欢迎使用AI学习搭子！我是你的学习助手。")
            
            self.send_json_response({
                "success": True,
                "message": "注册成功",
                "user_id": user_id
            })
        else:
            self.send_json_response({"success": False, "error": "用户名已存在"})
    
    def handle_chat(self, data):
        """处理聊天"""
        user_id = data.get('user_id')
        message = data.get('message', '').strip()
        
        if not user_id or not message:
            self.send_json_response({"success": False, "error": "参数不完整"})
            return
        
        # 智能回复逻辑
        ai_response = self.generate_ai_response(message)
        
        # 保存到数据库
        db.add_chat_message(user_id, message, ai_response)
        
        # 获取更新后的聊天记录
        history = db.get_chat_history(user_id)
        
        self.send_json_response({
            "success": True,
            "response": ai_response,
            "history": history
        })
    
    def generate_ai_response(self, message):
        """生成AI回复（教学版本）"""
        message_lower = message.lower()
        
        # 学习相关的回复
        if any(word in message_lower for word in ['学习', 'study', 'learn']):
            return "📚 学习是一个持续的过程！我建议：\n1. 制定明确目标\n2. 每天坚持学习\n3. 定期复习\n需要我帮你制定学习计划吗？"
        
        elif any(word in message_lower for word in ['数学', 'math']):
            return "🧮 数学学习建议：\n• 理解概念而非死记硬背\n• 多做练习题\n• 建立错题本\n• 寻求实际应用场景"
        
        elif any(word in message_lower for word in ['编程', 'code', 'programming']):
            return "💻 编程学习路径：\n1. 学习基础语法\n2. 完成小项目\n3. 阅读优秀代码\n4. 参与开源项目\n你想学习哪种编程语言？"
        
        elif any(word in message_lower for word in ['英语', 'english']):
            return "🔤 英语学习方法：\n• 每天背10个单词\n• 看英文电影/视频\n• 尝试用英语思考\n• 找语言伙伴练习"
        
        elif any(word in message_lower for word in ['计划', '规划', 'schedule']):
            return "🎯 学习计划制定：\n1. 设定明确目标\n2. 分解为小任务\n3. 安排每日学习时间\n4. 定期检查进度\n告诉我你的目标，我来帮你规划！"
        
        elif any(word in message_lower for word in ['你好', 'hello', 'hi']):
            return "👋 你好！我是AI学习搭子，你的智能学习助手。我可以帮你：\n• 解答学习问题\n• 制定学习计划\n• 跟踪学习进度\n• 提供学习建议"
        
        elif any(word in message_lower for word in ['帮助', 'help']):
            return "💡 我可以帮助你：\n• 学习问题解答\n• 学习计划制定\n• 学科专项指导\n• 学习进度跟踪\n• 学习方法建议\n请告诉我你需要什么帮助？"
        
        else:
            return "🤔 我理解你的问题了！在完整版本中，我会连接AI模型提供更精准的回答。目前我可以帮你制定学习计划、解答学科问题。"
    
    def send_cors_headers(self, status_code=200):
        """发送CORS头部"""
        self.send_response(status_code)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def send_json_response(self, data, status_code=200):
        """发送JSON响应"""
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        response_data = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.wfile.write(response_data)
    
    def log_message(self, format, *args):
        """自定义日志格式"""
        print(f"[{time.strftime('%H:%M:%S')}] {format % args}")

def run_server():
    port = 5000
    server_address = ('', port)
    
    print("=" * 50)
    print("🚀 AI学习搭子 v1.1 - 数据库版本")
    print(f"📍 服务地址: http://localhost:{port}")
    print("💾 数据存储: SQLite数据库")
    print("👤 功能: 用户注册/登录, 聊天记录持久化")
    print("=" * 50)
    
    httpd = HTTPServer(server_address, AIHandler)
    
    try:
        print("✅ 服务启动成功！")
        print("💡 提示: 按 Ctrl+C 停止服务")
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 服务停止")

if __name__ == '__main__':
    run_server()