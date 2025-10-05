import sqlite3
import hashlib
from datetime import datetime

class Database:
    def __init__(self, db_name='learning_buddy.db'):
        self.db_name = db_name
        self.init_database()
    
    def get_connection(self):
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_database(self):
        """初始化数据库表"""
        conn = self.get_connection()
        try:
            # 用户表（已存在）
            conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 聊天记录表（已存在）
            conn.execute('''
                CREATE TABLE IF NOT EXISTS chat_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    user_message TEXT NOT NULL,
                    ai_response TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            # 学习目标表 - 增强版
            conn.execute('''
                CREATE TABLE IF NOT EXISTS learning_goals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    category TEXT DEFAULT 'general',
                    priority INTEGER DEFAULT 1, -- 1:低, 2:中, 3:高
                    status TEXT DEFAULT 'active', -- active, completed, cancelled
                    target_date DATE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            # 学习记录表（新增）
            conn.execute('''
                CREATE TABLE IF NOT EXISTS study_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    goal_id INTEGER,
                    subject TEXT NOT NULL,
                    duration_minutes INTEGER NOT NULL,
                    notes TEXT,
                    session_date DATE DEFAULT CURRENT_DATE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    FOREIGN KEY (goal_id) REFERENCES learning_goals (id)
                )
            ''')
            
            conn.commit()
            print("✅ 数据库表初始化完成")
            
        except Exception as e:
            print(f"❌ 数据库初始化失败: {e}")
        finally:
            conn.close()
    
    # 已有的用户和聊天方法保持不变...
    def hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()
    
    def create_user(self, username, password):
        conn = self.get_connection()
        try:
            password_hash = self.hash_password(password)
            cursor = conn.execute(
                'INSERT INTO users (username, password_hash) VALUES (?, ?)',
                (username, password_hash)
            )
            conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            return None
        finally:
            conn.close()
    
    def verify_user(self, username, password):
        conn = self.get_connection()
        try:
            password_hash = self.hash_password(password)
            user = conn.execute(
                'SELECT id, username FROM users WHERE username = ? AND password_hash = ?',
                (username, password_hash)
            ).fetchone()
            return dict(user) if user else None
        finally:
            conn.close()
    
    def add_chat_message(self, user_id, user_message, ai_response):
        conn = self.get_connection()
        try:
            conn.execute(
                'INSERT INTO chat_history (user_id, user_message, ai_response) VALUES (?, ?, ?)',
                (user_id, user_message, ai_response)
            )
            conn.commit()
        finally:
            conn.close()
    
    def get_chat_history(self, user_id, limit=10):
        conn = self.get_connection()
        try:
            cursor = conn.execute(
                '''SELECT user_message, ai_response, timestamp 
                   FROM chat_history 
                   WHERE user_id = ? 
                   ORDER BY timestamp DESC LIMIT ?''',
                (user_id, limit)
            )
            history = [dict(row) for row in cursor.fetchall()]
            return history[::-1]
        finally:
            conn.close()
    
    # 学习目标管理方法
    def create_learning_goal(self, user_id, title, description="", category="general", priority=2, target_date=None):
        """创建学习目标"""
        conn = self.get_connection()
        try:
            cursor = conn.execute(
                '''INSERT INTO learning_goals 
                   (user_id, title, description, category, priority, target_date) 
                   VALUES (?, ?, ?, ?, ?, ?)''',
                (user_id, title, description, category, priority, target_date)
            )
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()
    
    def get_user_goals(self, user_id, status=None):
        """获取用户的学习目标"""
        conn = self.get_connection()
        try:
            if status:
                cursor = conn.execute(
                    '''SELECT * FROM learning_goals 
                       WHERE user_id = ? AND status = ? 
                       ORDER BY priority DESC, created_at DESC''',
                    (user_id, status)
                )
            else:
                cursor = conn.execute(
                    '''SELECT * FROM learning_goals 
                       WHERE user_id = ? 
                       ORDER BY priority DESC, created_at DESC''',
                    (user_id,)
                )
            goals = [dict(row) for row in cursor.fetchall()]
            return goals
        finally:
            conn.close()
    
    def update_goal_status(self, goal_id, status):
        """更新目标状态"""
        conn = self.get_connection()
        try:
            conn.execute(
                'UPDATE learning_goals SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
                (status, goal_id)
            )
            conn.commit()
            return True
        except Exception as e:
            print(f"更新目标状态失败: {e}")
            return False
        finally:
            conn.close()
    
    def delete_goal(self, goal_id):
        """删除学习目标"""
        conn = self.get_connection()
        try:
            conn.execute('DELETE FROM learning_goals WHERE id = ?', (goal_id,))
            conn.commit()
            return True
        except Exception as e:
            print(f"删除目标失败: {e}")
            return False
        finally:
            conn.close()
    
    def get_goal_progress(self, user_id):
        """获取用户目标进度统计"""
        conn = self.get_connection()
        try:
            cursor = conn.execute(
                '''SELECT 
                    COUNT(*) as total_goals,
                    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_goals,
                    SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) as active_goals
                   FROM learning_goals 
                   WHERE user_id = ?''',
                (user_id,)
            )
            progress = dict(cursor.fetchone())
            return progress
        finally:
            conn.close()
    
    # 学习记录管理方法
    def add_study_session(self, user_id, subject, duration_minutes, goal_id=None, notes=""):
        """添加学习记录"""
        conn = self.get_connection()
        try:
            cursor = conn.execute(
                '''INSERT INTO study_sessions 
                   (user_id, goal_id, subject, duration_minutes, notes) 
                   VALUES (?, ?, ?, ?, ?)''',
                (user_id, goal_id, subject, duration_minutes, notes)
            )
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()
    
    def get_study_sessions(self, user_id, days=7):
        """获取用户的学习记录"""
        conn = self.get_connection()
        try:
            cursor = conn.execute(
                '''SELECT * FROM study_sessions 
                   WHERE user_id = ? AND session_date >= date('now', ?) 
                   ORDER BY session_date DESC, created_at DESC''',
                (user_id, f'-{days} days')
            )
            sessions = [dict(row) for row in cursor.fetchall()]
            return sessions
        finally:
            conn.close()
    
    def get_study_statistics(self, user_id, days=30):
        """获取学习统计"""
        conn = self.get_connection()
        try:
            # 总学习时间
            cursor = conn.execute(
                '''SELECT SUM(duration_minutes) as total_minutes 
                   FROM study_sessions 
                   WHERE user_id = ? AND session_date >= date('now', ?)''',
                (user_id, f'-{days} days')
            )
            total_stats = dict(cursor.fetchone())
            
            # 按科目统计
            cursor = conn.execute(
                '''SELECT subject, SUM(duration_minutes) as total_minutes 
                   FROM study_sessions 
                   WHERE user_id = ? AND session_date >= date('now', ?)
                   GROUP BY subject 
                   ORDER BY total_minutes DESC''',
                (user_id, f'-{days} days')
            )
            subject_stats = [dict(row) for row in cursor.fetchall()]
            
            return {
                "total_minutes": total_stats["total_minutes"] or 0,
                "subject_breakdown": subject_stats
            }
        finally:
            conn.close()

# 创建全局数据库实例
db = Database()