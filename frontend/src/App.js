import React, { useState, useEffect } from 'react';
import { Layout, Card, Input, Button, message, Form, Tabs, List, Avatar } from 'antd';
import { UserOutlined, MessageOutlined, RobotOutlined } from '@ant-design/icons';
import axios from 'axios';
import './App.css';

const { Header, Content } = Layout;
const { TextArea } = Input;
const { TabPane } = Tabs;

const API_BASE = 'http://localhost:5000/api';

function App() {
  const [currentUser, setCurrentUser] = useState(null);
  const [activeTab, setActiveTab] = useState('chat');
  const [messageInput, setMessageInput] = useState('');
  const [chatHistory, setChatHistory] = useState([]);
  const [loading, setLoading] = useState(false);

  // 检查后端连接
  useEffect(() => {
    checkBackend();
  }, []);

  const checkBackend = async () => {
    try {
      await axios.get(`${API_BASE}/health`);
      message.success('后端服务连接正常');
    } catch (error) {
      message.error('后端服务连接失败');
    }
  };

  const handleLogin = async (values) => {
    try {
      const response = await axios.post(`${API_BASE}/login`, values);
      if (response.data.success) {
        setCurrentUser(response.data.user);
        message.success('登录成功');
        // 加载聊天记录
        loadChatHistory(response.data.user.id);
      }
    } catch (error) {
      message.error(error.response?.data?.error || '登录失败');
    }
  };

  const handleRegister = async (values) => {
    try {
      const response = await axios.post(`${API_BASE}/register`, values);
      if (response.data.success) {
        message.success('注册成功，请登录');
      }
    } catch (error) {
      message.error(error.response?.data?.error || '注册失败');
    }
  };

  const loadChatHistory = async (userId) => {
    try {
      const response = await axios.get(`${API_BASE}/chat/history?user_id=${userId}`);
      if (response.data.success) {
        setChatHistory(response.data.history || []);
      }
    } catch (error) {
      console.error('加载聊天记录失败:', error);
    }
  };

  const sendMessage = async () => {
    if (!messageInput.trim()) {
      message.warning('请输入消息');
      return;
    }

    if (!currentUser) {
      message.warning('请先登录');
      return;
    }

    setLoading(true);
    try {
      const response = await axios.post(`${API_BASE}/chat`, {
        user_id: currentUser.id,
        message: messageInput
      });

      if (response.data.success) {
        setChatHistory(response.data.history);
        setMessageInput('');
      }
    } catch (error) {
      message.error('发送失败');
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  if (!currentUser) {
    return (
      <Layout className="layout">
        <Content className="content">
          <div className="login-container">
            <Card title="🤖 AI学习搭子" className="login-card">
              <Tabs defaultActiveKey="login">
                <TabPane tab="登录" key="login">
                  <Form onFinish={handleLogin}>
                    <Form.Item name="username" rules={[{ required: true, message: '请输入用户名' }]}>
                      <Input prefix={<UserOutlined />} placeholder="用户名" />
                    </Form.Item>
                    <Form.Item name="password" rules={[{ required: true, message: '请输入密码' }]}>
                      <Input.Password placeholder="密码" />
                    </Form.Item>
                    <Form.Item>
                      <Button type="primary" htmlType="submit" block>
                        登录
                      </Button>
                    </Form.Item>
                  </Form>
                  <div style={{ textAlign: 'center', color: '#666' }}>
                    演示账号: demo / demo123
                  </div>
                </TabPane>
                
                <TabPane tab="注册" key="register">
                  <Form onFinish={handleRegister}>
                    <Form.Item name="username" rules={[{ required: true, message: '请输入用户名' }]}>
                      <Input prefix={<UserOutlined />} placeholder="用户名" />
                    </Form.Item>
                    <Form.Item name="password" rules={[{ required: true, message: '请输入密码' }]}>
                      <Input.Password placeholder="密码" />
                    </Form.Item>
                    <Form.Item>
                      <Button type="primary" htmlType="submit" block>
                        注册
                      </Button>
                    </Form.Item>
                  </Form>
                </TabPane>
              </Tabs>
            </Card>
          </div>
        </Content>
      </Layout>
    );
  }

  return (
    <Layout className="layout">
      <Header className="header">
        <div className="header-content">
          <h1>🤖 AI学习搭子</h1>
          <div className="user-info">
            <span>欢迎，{currentUser.username}</span>
            <Button 
              size="small" 
              onClick={() => setCurrentUser(null)}
              style={{ marginLeft: 10 }}
            >
              退出
            </Button>
          </div>
        </div>
      </Header>
      
      <Content className="content">
        <div className="chat-container">
          <Card 
            title={
              <div>
                <MessageOutlined /> 智能对话
                <span style={{ fontSize: 12, color: '#666', marginLeft: 10 }}>
                  试试输入: 学习、计划、数学、编程、英语
                </span>
              </div>
            }
            className="chat-card"
          >
            <div className="chat-messages">
              <List
                dataSource={chatHistory}
                renderItem={(item, index) => (
                  <List.Item className="message-item">
                    <List.Item.Meta
                      avatar={<Avatar icon={<UserOutlined />} />}
                      title="你"
                      description={item.user_message}
                    />
                    <div className="ai-response">
                      <Avatar icon={<RobotOutlined />} style={{ backgroundColor: '#87d068' }} />
                      <div className="response-content">
                        <div className="response-header">AI学习搭子</div>
                        <div>{item.ai_response}</div>
                      </div>
                    </div>
                  </List.Item>
                )}
                locale={{ emptyText: '还没有对话记录，开始聊天吧！' }}
              />
            </div>
            
            <div className="chat-input">
              <TextArea
                rows={3}
                value={messageInput}
                onChange={(e) => setMessageInput(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="输入你的问题或想法... (按Enter发送)"
                disabled={loading}
              />
              <Button 
                type="primary" 
                onClick={sendMessage}
                loading={loading}
                style={{ marginTop: 10 }}
                block
              >
                发送消息
              </Button>
            </div>
          </Card>
        </div>
      </Content>
    </Layout>
  );
}

export default App;