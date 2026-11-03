import { apiClient, authClient, withAuthLock } from "./client";
import type {
  LoginRequest,
  RegisterRequest,
  TokenResponse,
  User,
} from "../types";

export const authApi = {
  login: async (values: LoginRequest): Promise<TokenResponse> =>
    withAuthLock(
      async () =>
        (await authClient.post<TokenResponse>("/api/v1/auth/login", values))
          .data,
    ),
  register: async (values: RegisterRequest): Promise<TokenResponse> =>
    withAuthLock(
      async () =>
        (await authClient.post<TokenResponse>("/api/v1/auth/register", values))
          .data,
    ),
  logout: async (): Promise<void> => {
    await withAuthLock(async () => {
      await authClient.post("/api/v1/auth/logout");
    });
  },
  getCurrentUser: async (): Promise<User> =>
    (await apiClient.get<User>("/api/v1/users/me")).data,
};
