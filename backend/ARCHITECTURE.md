# Backend modules

`app/modules/auth`: JWT issuance/verification, refresh sessions, login/register/refresh/logout and authentication dependencies.

`app/modules/users`: user model, schemas, account creation and profile/admin APIs. Roles are `admin` and `doctor`; self-registration can only create a doctor. Administrators can create other admins via the protected user API. Bootstrap admin credentials come from environment variables.

`app/modules/patients`: patient model, schemas, service and routes.

`app/modules/ml`: multipart API and response schemas; `inference/` contains the unchanged model algorithms, weights discovery and registry.

`app/api/v1/api.py` composes the routers and applies authentication to all patient and ML endpoints. `app/core` holds configuration and cryptographic helpers. `app/db` owns database sessions; `app/models` registers SQLAlchemy metadata and contains shared mixins, enums and the future cycle model. Old import paths are compatibility aliases to the canonical modules, not duplicated implementations.

## Session lifecycle

- Access JWT lifetime: 1 day. Refresh JWT: 30 days from its latest successful rotation.
- Every login/register creates an independent persisted session. Only the SHA-256 hash of its current refresh token is stored. The browser receives the refresh in an HttpOnly, SameSite=Lax cookie; access is held in JavaScript memory.
- `/auth/refresh` locks the session row, checks the current refresh hash, rotates both tokens and advances the expiry by 30 days. The previous refresh is immediately invalid. No fixed maximum session lifetime is applied.
- Reloading the frontend refreshes the session. Expired access automatically triggers one shared refresh request and retries the original API request. Permanent refresh failures end the session; network/server failures allow retry.
- `/auth/logout` revokes the persisted session and clears the cookie. Access verification checks active user and session, so logout and deactivation also block otherwise unexpired access JWTs.
- Cookie endpoints require `X-CSRF-Protection: 1`; cross-origin browser calls also require an allowed CORS origin. For HTTPS production set `AUTH_COOKIE_SECURE=true`; serve frontend/API on the same site and keep `SECRET_KEY` private and stable across restarts.
- Role checks use the current database value, not a client-provided role or stale JWT claim. Public registration never grants admin. Account APIs do not return password hashes or refresh hashes.

Migration `002` keeps existing users, patients and cycles. Existing user logins are `user_<id>` and the former email remains accepted at login; former clinical roles become `doctor`. Existing full names and emails are retained. Historical admin-like accounts are not automatically elevated. Configure bootstrap admin credentials to create the first admin.
