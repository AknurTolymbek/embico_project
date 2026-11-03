// Авторизация временно отключена: пускаем любого пользователя без входа.
// Чтобы вернуть проверку, восстановите редирект на /login при !isAuthenticated.
export const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  return <>{children}</>;
};
