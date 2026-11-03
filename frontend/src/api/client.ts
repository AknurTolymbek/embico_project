import axios from "axios";
import type { InternalAxiosRequestConfig } from "axios";
import type { TokenResponse } from "../types";
import { getToken, setSession, removeToken } from "../utils/auth";

const options = {
  baseURL: import.meta.env.VITE_API_URL || "",
  withCredentials: true,
  headers: { "Content-Type": "application/json", "X-CSRF-Protection": "1" },
};
export const apiClient = axios.create(options);
// Does not intercept its own 401s or recursively attempt refresh.
export const authClient = axios.create(options);

// Serialize cookie rotation/login/logout across tabs where Web Locks is available.
export const withAuthLock = <T>(request: () => Promise<T>): Promise<T> =>
  typeof navigator !== "undefined" && navigator.locks
    ? navigator.locks.request("embico-refresh", request)
    : request();

let refreshFlight: Promise<TokenResponse> | null = null;
export const refreshSession = (): Promise<TokenResponse> => {
  if (!refreshFlight) {
    const request = async () => {
      const { data } = await authClient.post<TokenResponse>(
        "/api/v1/auth/refresh",
      );
      setSession(data.access_token, data.user);
      return data;
    };
    const locked = withAuthLock(request);
    refreshFlight = locked
      .catch((error) => {
        if (
          axios.isAxiosError(error) &&
          [401, 403].includes(error.response?.status ?? 0)
        )
          removeToken();
        throw error;
      })
      .finally(() => {
        refreshFlight = null;
      });
  }
  return refreshFlight;
};

apiClient.interceptors.request.use((config) => {
  const token = getToken();
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

type RetryConfig = InternalAxiosRequestConfig & { _authRetried?: boolean };
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const config = error.config as RetryConfig | undefined;
    if (error.response?.status !== 401 || !config) return Promise.reject(error);
    if (config._authRetried) {
      removeToken();
      return Promise.reject(error);
    }
    // A different request may already have refreshed the token while this one was in flight.
    const currentToken = getToken();
    const previousToken = config.headers.Authorization;
    config._authRetried = true;
    if (currentToken && previousToken !== `Bearer ${currentToken}`) {
      config.headers.Authorization = `Bearer ${currentToken}`;
      return apiClient.request(config);
    }
    const data = await refreshSession();
    config.headers.Authorization = `Bearer ${data.access_token}`;
    return apiClient.request(config);
  },
);
