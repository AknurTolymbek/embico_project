import { useState } from "react";
import { Alert, Button, Form, Input, Spin, Tabs } from "antd";
import {
  ArrowRightOutlined,
  LockOutlined,
  SafetyCertificateOutlined,
  UserOutlined,
} from "@ant-design/icons";
import { Navigate, useLocation, useNavigate } from "react-router-dom";
import axios from "axios";
import { useAuth } from "../context/AuthContext";
import { authApi } from "../api/auth";
import type { RegisterRequest } from "../types";
import "./auth.css";

export const Login = () => {
  const { acceptSession, isAuthenticated, isLoading } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [mode, setMode] = useState("login");
  const [pending, setPending] = useState(false);
  const [error, setError] = useState("");
  const [form] = Form.useForm<RegisterRequest>();
  const previous = location.state?.from;
  const destination =
    typeof previous === "string" &&
    previous.startsWith("/") &&
    !previous.startsWith("//") &&
    !previous.startsWith("/login")
      ? previous
      : "/patients";
  if (isLoading)
    return (
      <div className="session-loading">
        <Spin size="large" />
      </div>
    );
  if (isAuthenticated) return <Navigate to={destination} replace />;
  const submit = async (values: RegisterRequest) => {
    setPending(true);
    setError("");
    try {
      const response =
        mode === "login"
          ? await authApi.login({
              username: values.username,
              password: values.password,
            })
          : await authApi.register(values);
      acceptSession(response);
      navigate(destination, { replace: true });
    } catch (failure) {
      const detail: unknown = axios.isAxiosError(failure)
        ? failure.response?.data?.detail
        : undefined;
      setError(
        typeof detail === "string"
          ? detail
          : Array.isArray(detail)
            ? detail.map((item) => item.msg).join("; ")
            : "Не удалось подключиться к серверу. Попробуйте ещё раз.",
      );
    } finally {
      setPending(false);
    }
  };
  return (
    <main className="auth-page">
      <section className="auth-story">
        <div className="brand">
          <span className="brand-symbol">
            <i />
            <i />
            <i />
          </span>
          <span>
            embico<span className="brand-dot">.</span>
            <small>FERTILITY CARE PLATFORM</small>
          </span>
        </div>
        <div className="auth-story-content">
          <span className="eyebrow">ПРОСТРАНСТВО РЕПРОДУКТИВНОЙ МЕДИЦИНЫ</span>
          <h1>
            Каждая история
            <br />
            начинается с заботы<span>.</span>
          </h1>
          <p>
            Пациенты, медицинские данные и анализ эмбрионов — в одном рабочем
            пространстве вашей клиники.
          </p>
          <div className="auth-orbits" aria-hidden="true">
            <i />
            <i />
            <i />
          </div>
        </div>
        <div className="auth-story-footer">
          <SafetyCertificateOutlined /> Доступ только для авторизованных
          пользователей
        </div>
      </section>
      <section className="auth-form-side">
        <div className="auth-form-card">
          <div className="eyebrow">ДОБРО ПОЖАЛОВАТЬ В EMBICO</div>
          <h2>
            {mode === "login" ? "Вход в пространство" : "Создать аккаунт врача"}
          </h2>
          <p className="auth-intro">
            {mode === "login"
              ? "Введите логин и пароль для продолжения работы."
              : "Укажите имя, фамилию и данные для входа."}
          </p>
          <Tabs
            activeKey={mode}
            onChange={(value) => {
              setMode(value);
              setError("");
              form.resetFields();
            }}
            items={[
              { key: "login", label: "Войти", disabled: pending },
              { key: "register", label: "Регистрация", disabled: pending },
            ]}
          />
          <Form
            form={form}
            layout="vertical"
            onFinish={submit}
            disabled={pending}
            requiredMark={false}
            preserve={false}
          >
            {mode === "register" && (
              <div className="form-grid">
                <Form.Item
                  name="first_name"
                  label="Имя"
                  rules={[
                    {
                      required: true,
                      whitespace: true,
                      message: "Укажите имя",
                    },
                    { max: 120, message: "Не более 120 символов" },
                  ]}
                >
                  <Input autoComplete="given-name" placeholder="Имя" />
                </Form.Item>
                <Form.Item
                  name="last_name"
                  label="Фамилия"
                  rules={[
                    {
                      required: true,
                      whitespace: true,
                      message: "Укажите фамилию",
                    },
                    { max: 120, message: "Не более 120 символов" },
                  ]}
                >
                  <Input autoComplete="family-name" placeholder="Фамилия" />
                </Form.Item>
              </div>
            )}
            <Form.Item
              name="username"
              label="Логин"
              rules={[
                { required: true, whitespace: true, message: "Укажите логин" },
                ...(mode === "register"
                  ? [
                      {
                        min: 3,
                        max: 80,
                        pattern: /^[a-zA-Z0-9_.@+-]+$/,
                        message:
                          "От 3 до 80 символов: латиница, цифры, _ . @ + −",
                      },
                    ]
                  : []),
              ]}
            >
              <Input
                prefix={<UserOutlined />}
                autoComplete="username"
                placeholder={
                  mode === "login"
                    ? "Ваш логин или email"
                    : "Например, doctor.aliya"
                }
              />
            </Form.Item>
            <Form.Item
              name="password"
              label="Пароль"
              rules={[
                { required: true, message: "Введите пароль" },
                ...(mode === "register"
                  ? [
                      { min: 8, max: 72, message: "От 8 до 72 символов" },
                      {
                        validator: (_: unknown, value: string) =>
                          !value || new TextEncoder().encode(value).length <= 72
                            ? Promise.resolve()
                            : Promise.reject(
                                new Error("Не более 72 байт UTF-8"),
                              ),
                      },
                    ]
                  : []),
              ]}
            >
              <Input.Password
                prefix={<LockOutlined />}
                autoComplete={
                  mode === "login" ? "current-password" : "new-password"
                }
                placeholder={
                  mode === "login" ? "Ваш пароль" : "Не менее 8 символов"
                }
              />
            </Form.Item>
            {error && (
              <Alert
                type="error"
                showIcon
                title={error}
                className="auth-error"
              />
            )}
            <Button
              type="primary"
              htmlType="submit"
              block
              loading={pending}
              icon={<ArrowRightOutlined />}
              iconPlacement="end"
            >
              {mode === "login" ? "Войти" : "Зарегистрироваться"}
            </Button>
          </Form>
          <p className="auth-footnote">
            {mode === "register"
              ? "При регистрации назначается роль «Врач». Роль администратора назначает администратор клиники."
              : "Сессия продлевается при входе и обновлении токенов. После 30 дней без обновления потребуется войти заново."}
          </p>
        </div>
        <span className="auth-copyright">EMBICO · Репродуктивная медицина</span>
      </section>
    </main>
  );
};
