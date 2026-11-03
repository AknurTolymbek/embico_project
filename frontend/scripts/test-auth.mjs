// Exercise the actual Axios interceptors without a browser or a mocked implementation.
import assert from "node:assert/strict";
import fs from "node:fs/promises";
import path from "node:path";
import { pathToFileURL } from "node:url";
import { transformWithOxc } from "vite";
import axios from "axios";

await fs.mkdir(path.resolve("node_modules/.tmp"), { recursive: true });
const directory = await fs.mkdtemp(
  path.resolve("node_modules/.tmp/auth-check-"),
);
const storage = new Map([
  ["access_token", "old-demo-token"],
  ["user", '{"id":0}'],
]);
globalThis.localStorage = {
  getItem: (key) => storage.get(key) ?? null,
  setItem: (key, value) => storage.set(key, value),
  removeItem: (key) => storage.delete(key),
};
try {
  const authSource = await fs.readFile("src/utils/auth.ts", "utf8");
  const clientSource = (await fs.readFile("src/api/client.ts", "utf8"))
    .replace(/from ["']\.\.\/utils\/auth["']/, 'from "./auth.mjs"')
    .replace("import.meta.env.VITE_API_URL", '""');
  await fs.writeFile(
    path.join(directory, "auth.mjs"),
    (await transformWithOxc(authSource, "auth.ts")).code,
  );
  await fs.writeFile(
    path.join(directory, "client.mjs"),
    (await transformWithOxc(clientSource, "client.ts")).code,
  );
  const auth = await import(
    pathToFileURL(path.join(directory, "auth.mjs")).href
  );
  const { apiClient, authClient } = await import(
    pathToFileURL(path.join(directory, "client.mjs")).href
  );
  assert.equal(storage.has("access_token"), false);
  assert.equal(storage.has("user"), false);
  const user = { id: 1, username: "doctor_test", role: "doctor" };
  let refreshCalls = 0;
  let requestCalls = 0;
  let outcome = "ok";
  const response = (config, status, data) => ({
    config,
    status,
    data,
    statusText: String(status),
    headers: {},
  });
  const reject = (config, status) =>
    Promise.reject(
      new axios.AxiosError(
        "Rejected",
        "ERR_BAD_REQUEST",
        config,
        undefined,
        response(config, status, {}),
      ),
    );
  authClient.defaults.adapter = async (config) => {
    refreshCalls++;
    assert.equal(config.withCredentials, true);
    assert.equal(config.headers["X-CSRF-Protection"], "1");
    await new Promise((resolve) => setTimeout(resolve, 5));
    if (outcome === "offline")
      throw new axios.AxiosError("Network error", "ERR_NETWORK", config);
    if (outcome === "expired") return reject(config, 401);
    return response(config, 200, {
      access_token: "new-access",
      user,
      token_type: "bearer",
      expires_in: 86400,
    });
  };
  apiClient.defaults.adapter = async (config) => {
    requestCalls++;
    return config.headers.Authorization === "Bearer new-access"
      ? response(config, 200, { ok: true })
      : reject(config, 401);
  };
  auth.setSession("expired-access", user);
  const requests = await Promise.all(
    Array.from({ length: 12 }, () => apiClient.get("/api/v1/patients/")),
  );
  assert.ok(requests.every((result) => result.status === 200));
  assert.equal(refreshCalls, 1, "Parallel 401s must share one refresh");
  assert.equal(requestCalls, 24, "Each original request retries exactly once");
  assert.equal(auth.getToken(), "new-access");
  assert.equal(
    storage.size,
    0,
    "JWTs and users must never be persisted in localStorage",
  );

  outcome = "offline";
  auth.setSession("expired-access", user);
  await assert.rejects(apiClient.get("/api/v1/patients/"));
  assert.equal(
    auth.getUser(),
    user,
    "Network failures must not silently destroy the session",
  );

  outcome = "expired";
  auth.setSession("expired-access", user);
  await assert.rejects(apiClient.get("/api/v1/patients/"));
  assert.equal(
    auth.getUser(),
    null,
    "Rejected refresh must clear the logged-in user",
  );
  assert.equal(auth.getToken(), null);

  outcome = "ok";
  auth.setSession("expired-access", user);
  apiClient.defaults.adapter = (config) => reject(config, 401);
  const before = refreshCalls;
  await assert.rejects(apiClient.get("/api/v1/patients/"));
  assert.equal(
    refreshCalls,
    before + 1,
    "Retried 401 must not start an infinite refresh loop",
  );
  assert.equal(auth.getUser(), null);
  console.log(
    "PASS: 12 parallel 401s share one refresh; credentials/CSRF, memory-only tokens, transient failures, expired sessions and retry bounds.",
  );
} finally {
  await fs.rm(directory, { recursive: true, force: true });
}
