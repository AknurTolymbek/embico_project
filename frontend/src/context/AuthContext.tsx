import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import { useQueryClient } from "@tanstack/react-query";
import axios from "axios";
import type { TokenResponse, User } from "../types";
import { authApi } from "../api/auth";
import { refreshSession } from "../api/client";
import { getUser, setSession, removeToken, subscribeAuth } from "../utils/auth";

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  sessionError: boolean;
  retrySession: () => void;
  acceptSession: (data: TokenResponse) => void;
  logout: () => Promise<void>;
  isAuthenticated: boolean;
}
const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<User | null>(getUser);
  const [isLoading, setIsLoading] = useState(true);
  const [sessionError, setSessionError] = useState(false);
  const queryClient = useQueryClient();
  useEffect(
    () =>
      subscribeAuth(() => {
        const nextUser = getUser();
        setUser(nextUser);
        if (!nextUser) queryClient.clear();
      }),
    [queryClient],
  );
  const checkSession = useCallback(() => {
    refreshSession()
      .catch((error) => {
        if (
          !axios.isAxiosError(error) ||
          ![401, 403].includes(error.response?.status ?? 0)
        )
          setSessionError(true);
      })
      .finally(() => setIsLoading(false));
  }, []);
  const retrySession = () => {
    setIsLoading(true);
    setSessionError(false);
    checkSession();
  };
  useEffect(() => {
    checkSession();
  }, [checkSession]);
  const acceptSession = (data: TokenResponse) => {
    queryClient.clear();
    setSession(data.access_token, data.user);
    setSessionError(false);
    setIsLoading(false);
  };
  const logout = async () => {
    // In-flight API refreshes must finish before the cookie/session is revoked.
    try {
      await authApi.logout();
    } catch (error) {
      if (!axios.isAxiosError(error) || error.response?.status !== 401)
        throw error;
    }
    removeToken();
    setSessionError(false);
    queryClient.clear();
  };
  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        sessionError,
        retrySession,
        acceptSession,
        logout,
        isAuthenticated: !!user,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used within AuthProvider");
  return context;
};
