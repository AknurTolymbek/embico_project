import { createContext, useContext, useState, type ReactNode } from 'react';
import type { User } from '../types';
import { UserRole } from '../types';
import { setUser as saveUser, removeToken } from '../utils/auth';

// Авторизация временно отключена: по умолчанию работает гостевой пользователь.
const GUEST_USER: User = {
  id: 0,
  email: 'guest@embico.local',
  full_name: 'Гость',
  role: UserRole.REPRODUCTOLOGIST,
  is_active: true,
};

interface AuthContextType {
  user: User | null;
  setUser: (user: User | null) => void;
  logout: () => void;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUserState] = useState<User | null>(GUEST_USER);

  const setUser = (newUser: User | null) => {
    setUserState(newUser ?? GUEST_USER);
    if (newUser) {
      saveUser(newUser);
    }
  };

  const logout = () => {
    removeToken();
    setUserState(GUEST_USER);
  };

  return (
    <AuthContext.Provider value={{ user, setUser, logout, isAuthenticated: true }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
