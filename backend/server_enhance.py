from http.server import HTTPServer, BaseHTTPRequestHandler
from openai import OpenAI
import os
import json
from urllib.parse import urlparse, parse_qs
import time
from database import db
from github_ai_service import github_ai_service 

class EnhancedAIHandler(BaseHTTPRequestHandler):
    
    def do_OPTIONS(self):
        """处理CORS预检请求"""
        self.send_cors_headers(200)
    
    def do_GET(self):
        """处理GET请求"""
        parsed_path = urlparse(self.path)
        query_params = parse_qs(parsed_path.query)
        
        # 提取用户ID（如果存在）
        user_id = query_params.get('user_id', [None])[0]
        
        if parsed_path.path == '/api/health':
            self.handle_health_check()
        elif parsed_path.path == '/api/goals' and user_id:
            self.handle_get_goals(user_id, query_params.get('status', [None])[0])
        elif parsed_path.path == '/api/goals/progress' and user_id:
            self.handle_get_goals_progress(user_id)
        elif parsed_path.path == '/api/study/sessions' and user_id:
            self.handle_get_study_sessions(user_id)
        elif parsed_path.path == '/api/study/statistics' and user_id:
            self.handle_get_study_statistics(user_id)
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
            elif parsed_path.path == '/api/goals':
                self.handle_create_goal(data)
            elif parsed_path.path == '/api/study/session':
                self.handle_add_study_session(data)
            else:
                self.send_error(404, "接口不存在")
                
        except Exception as e:
            self.send_json_response({"success": False, "error": str(e)}, 400)
    
    def do_PUT(self):
        """处理PUT请求 - 更新目标状态"""
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        try:
            data = json.loads(post_data.decode('utf-8'))
            parsed_path = urlparse(self.path)
            
            if parsed_path.path == '/api/goals/status':
                self.handle_update_goal_status(data)
            else:
                self.send_error(404, "接口不存在")
                
        except Exception as e:
            self.send_json_response({"success": False, "error": str(e)}, 400)
    
    def do_DELETE(self):
        """处理DELETE请求 - 删除目标"""
        parsed_path = urlparse(self.path)
        query_params = parse_qs(parsed_path.query)
        
        goal_id = query_params.get('goal_id', [None])[0]
        
        if parsed_path.path == '/api/goals' and goal_id:
            self.handle_delete_goal(goal_id)
        else:
            self.send_error(404, "接口不存在")
    
    # 原有的基础方法保持不变
    def handle_health_check(self):
        self.send_json_response({
            "status": "healthy", 
            "service": "AI学习搭子增强版",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        })
    
    def handle_home(self):
        self.send_json_response({
            "message": "AI学习搭子增强版服务运行正常",
            "version": "2.0.0",
            "features": ["用户管理", "智能对话", "学习目标管理", "学习进度跟踪"]
        })
    
    def handle_login(self, data):
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
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        
        if not username or not password:
            self.send_json_response({"success": False, "error": "用户名和密码不能为空"})
            return
        
        user_id = db.create_user(username, password)
        if user_id:
            db.add_chat_message(user_id, "系统", "👋 欢迎使用AI学习搭子！我是你的学习助手。")
            self.send_json_response({
                "success": True,
                "message": "注册成功",
                "user_id": user_id
            })
        else:
            self.send_json_response({"success": False, "error": "用户名已存在"})
    
    def handle_chat(self, data):
        """处理聊天 - 使用GitHub AI服务"""
        user_id = data.get('user_id')
        message = data.get('message', '').strip()
        
        if not user_id or not message:
            self.send_json_response({"success": False, "error": "参数不完整"})
            return
        
        print(f"💬 用户消息: {message}")
        
        # 使用GitHub AI服务生成回复
        ai_response = github_ai_service.generate_response(message)
        
        # 保存到数据库
        db.add_chat_message(user_id, message, ai_response)
        
        # 获取更新后的聊天记录
        history = db.get_chat_history(user_id)
        
        self.send_json_response({
            "success": True,
            "response": ai_response,
            "history": history
        })


    # 新增的学习目标管理方法
    def handle_create_goal(self, data):
        """创建学习目标"""
        user_id = data.get('user_id')
        title = data.get('title', '').strip()
        description = data.get('description', '').strip()
        category = data.get('category', 'general')
        priority = data.get('priority', 2)
        target_date = data.get('target_date')
        
        if not user_id or not title:
            self.send_json_response({"success": False, "error": "用户ID和目标标题不能为空"})
            return
        
        goal_id = db.create_learning_goal(user_id, title, description, category, priority, target_date)
        
        if goal_id:
            self.send_json_response({
                "success": True,
                "message": "学习目标创建成功",
                "goal_id": goal_id
            })
        else:
            self.send_json_response({"success": False, "error": "创建学习目标失败"})
    
    def handle_get_goals(self, user_id, status=None):
        """获取用户的学习目标"""
        goals = db.get_user_goals(user_id, status)
        self.send_json_response({
            "success": True,
            "goals": goals
        })
    
    def handle_get_goals_progress(self, user_id):
        """获取目标进度统计"""
        progress = db.get_goal_progress(user_id)
        self.send_json_response({
            "success": True,
            "progress": progress
        })
    
    def handle_update_goal_status(self, data):
        """更新目标状态"""
        goal_id = data.get('goal_id')
        status = data.get('status')
        
        if not goal_id or not status:
            self.send_json_response({"success": False, "error": "目标ID和状态不能为空"})
            return
        
        success = db.update_goal_status(goal_id, status)
        if success:
            self.send_json_response({
                "success": True,
                "message": "目标状态更新成功"
            })
        else:
            self.send_json_response({"success": False, "error": "更新目标状态失败"})
    
    def handle_delete_goal(self, goal_id):
        """删除学习目标"""
        success = db.delete_goal(goal_id)
        if success:
            self.send_json_response({
                "success": True,
                "message": "学习目标删除成功"
            })
        else:
            self.send_json_response({"success": False, "error": "删除学习目标失败"})
    
    # 学习记录管理方法
    def handle_add_study_session(self, data):
        """添加学习记录"""
        user_id = data.get('user_id')
        subject = data.get('subject', '').strip()
        duration_minutes = data.get('duration_minutes', 0)
        goal_id = data.get('goal_id')
        notes = data.get('notes', '').strip()
        
        if not user_id or not subject or duration_minutes <= 0:
            self.send_json_response({"success": False, "error": "参数不完整或无效"})
            return
        
        session_id = db.add_study_session(user_id, subject, duration_minutes, goal_id, notes)
        
        if session_id:
            self.send_json_response({
                "success": True,
                "message": "学习记录添加成功",
                "session_id": session_id
            })
        else:
            self.send_json_response({"success": False, "error": "添加学习记录失败"})
    
    def handle_get_study_sessions(self, user_id):
        """获取学习记录"""
        sessions = db.get_study_sessions(user_id)
        self.send_json_response({
            "success": True,
            "sessions": sessions
        })
    
    def handle_get_study_statistics(self, user_id):
        """获取学习统计"""
        stats = db.get_study_statistics(user_id)
        self.send_json_response({
            "success": True,
            "statistics": stats
        })
    
    def send_cors_headers(self, status_code=200):
        """发送CORS头部"""
        self.send_response(status_code)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
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
def run_enhanced_server():
    port = 5000
    server_address = ('', port)
    
    print("=" * 60)
    print("🚀 AI学习搭子 v2.2 - GitHub AI集成版")
    print(f"📍 服务地址: http://localhost:{port}")
    print("🤖 AI功能: GitHub Models API")
    print("💡 提示: 请在 .env 文件中配置 GITHUB_PAT")
    print("=" * 60)
    
    # 检查AI服务状态
    if github_ai_service.github_pat:
        print("✅ GitHub PAT: 已配置")
        print("🔗 API端点: https://models.github.ai/inference/chat/completions")
    else:
        print("⚠️ GitHub PAT: 未配置 (运行在模拟模式)")
    
    httpd = HTTPServer(server_address, EnhancedAIHandler)
    
    try:
        print("✅ 服务启动成功！")
        print("💡 提示: 按 Ctrl+C 停止服务")
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 服务停止")

if __name__ == '__main__':
    run_enhanced_server()