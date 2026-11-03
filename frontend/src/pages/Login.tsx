import { useState } from 'react';
import { Form, Input, Button, Card, message, Typography } from 'antd';
import { UserOutlined, LockOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useMutation } from '@tanstack/react-query';
import { authApi } from '../api/auth';
import { useAuth } from '../context/AuthContext';
import { setToken } from '../utils/auth';

const { Title } = Typography;

export const Login = () => {
  const navigate = useNavigate();
  const { t } = useTranslation();
  const { setUser } = useAuth();
  const [form] = Form.useForm();

  const loginMutation = useMutation({
    mutationFn: authApi.login,
    onSuccess: async (data) => {
      setToken(data.access_token);

      // Get user info
      try {
        const user = await authApi.getCurrentUser();
        setUser(user);
        message.success(t('common.success'));
        navigate('/today');
      } catch (error) {
        message.error(t('common.error'));
      }
    },
    onError: () => {
      message.error('Неверный email или пароль');
    },
  });

  const onFinish = (values: { email: string; password: string }) => {
    loginMutation.mutate(values);
  };

  return (
    <div
      style={{
        minHeight: '100vh',
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        background: '#f0f2f5',
      }}
    >
      <Card style={{ width: 400, boxShadow: '0 2px 8px rgba(0,0,0,0.1)' }}>
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <Title level={2} style={{ color: '#004598', marginBottom: 8 }}>
            EMBICO
          </Title>
          <Title level={4} style={{ color: '#5d707d', fontWeight: 400 }}>
            {t('auth.login')}
          </Title>
        </div>

        <Form
          form={form}
          name="login"
          onFinish={onFinish}
          layout="vertical"
          size="large"
        >
          <Form.Item
            name="email"
            label={t('auth.email')}
            rules={[
              { required: true, message: 'Введите email' },
              { type: 'email', message: 'Введите корректный email' },
            ]}
          >
            <Input
              prefix={<UserOutlined />}
              placeholder="admin@embico.kz"
            />
          </Form.Item>

          <Form.Item
            name="password"
            label={t('auth.password')}
            rules={[{ required: true, message: 'Введите пароль' }]}
          >
            <Input.Password
              prefix={<LockOutlined />}
              placeholder="••••••••"
            />
          </Form.Item>

          <Form.Item style={{ marginBottom: 0 }}>
            <Button
              type="primary"
              htmlType="submit"
              block
              loading={loginMutation.isPending}
            >
              {t('auth.signIn')}
            </Button>
          </Form.Item>
        </Form>

        <div style={{ marginTop: 16, textAlign: 'center', fontSize: 12, color: '#999' }}>
          Демо версия для разработки
        </div>
      </Card>
    </div>
  );
};
