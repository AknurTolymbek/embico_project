import type { ReactNode } from "react";
import { Navigate, useLocation } from "react-router-dom";
import { Alert, Button, Spin } from "antd";
import { useAuth } from "../context/AuthContext";

export const ProtectedRoute = ({ children }: { children: ReactNode }) => {
  const { isAuthenticated, isLoading, sessionError, retrySession } = useAuth();
  const location = useLocation();
  if (isLoading)
    return (
      <div className="session-loading">
        <Spin size="large" description="Проверяем сессию…" />
      </div>
    );
  if (sessionError)
    return (
      <div className="session-loading">
        <Alert
          type="error"
          showIcon
          title="Не удалось подключиться к серверу"
          description="Повторите проверку сессии, когда соединение восстановится."
          action={<Button onClick={retrySession}>Повторить</Button>}
        />
      </div>
    );
  return isAuthenticated ? (
    <>{children}</>
  ) : (
    <Navigate
      to="/login"
      replace
      state={{ from: location.pathname + location.search }}
    />
  );
};
