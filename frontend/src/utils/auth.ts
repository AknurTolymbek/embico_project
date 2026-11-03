import type { User } from "../types";

let accessToken: string | null = null;
let currentUser: User | null = null;
const listeners = new Set<() => void>();

// Remove credentials left by the former demo implementation.
localStorage.removeItem("access_token");
localStorage.removeItem("user");

export const getToken = () => accessToken;
export const getUser = () => currentUser;
export const setSession = (token: string, user: User) => {
  accessToken = token;
  currentUser = user;
  listeners.forEach((listener) => listener());
};
export const removeToken = () => {
  accessToken = null;
  currentUser = null;
  listeners.forEach((listener) => listener());
};
export const subscribeAuth = (listener: () => void) => {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
};
