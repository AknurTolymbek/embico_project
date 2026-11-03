"""Authentication integration tests against an explicitly selected disposable PostgreSQL DB.

Run with TEST_DATABASE_URL set; every test uses an outer rollback transaction.
Never set TEST_DATABASE_URL to a production database.
"""
from datetime import datetime, timedelta, timezone
import os
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from jose import jwt
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.core.config import settings
from app.core.enums import UserRole
from app.core import security
from app.db.database import get_db
from app.main import app
from app.modules.auth import service
from app.modules.auth.models import AuthSession
from app.modules.users.models import User

URL = os.environ.get('TEST_DATABASE_URL')
pytestmark = pytest.mark.skipif(not URL, reason='Set TEST_DATABASE_URL to a migrated disposable PostgreSQL database')
AUTH = '/api/v1/auth'
CSRF = {'X-CSRF-Protection': '1'}


@pytest.fixture
async def db():
    assert URL and 'test' in URL.rsplit('/', 1)[-1], 'Use a dedicated test database'
    engine = create_async_engine(URL.replace('postgresql://', 'postgresql+asyncpg://'))
    async with engine.connect() as connection:
        transaction = await connection.begin()
        async with AsyncSession(bind=connection, expire_on_commit=False, join_transaction_mode='create_savepoint') as session:
            yield session
        await transaction.rollback()
    await engine.dispose()


@pytest.fixture
async def client(db):
    async def test_db():
        yield db
    app.dependency_overrides[get_db] = test_db
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test', headers=CSRF) as client:
            yield client
    finally:
        app.dependency_overrides.pop(get_db, None)


def account(**extra):
    return {'username': 'doctor_' + uuid4().hex[:12], 'password': 'TestPassword123!',
            'first_name': 'Тест', 'last_name': 'Врач', **extra}


async def register(client, **extra):
    values = account(**extra)
    response = await client.post(AUTH + '/register', json=values)
    assert response.status_code == 201, response.text
    return values, response


def bearer(response):
    return {'Authorization': 'Bearer ' + response.json()['access_token']}


async def test_register_login_cookie_and_token_lifetimes(client, db):
    values, response = await register(client)
    body = response.json()
    assert body['user']['role'] == 'doctor'
    assert body['user']['first_name'] == 'Тест'
    assert 'hashed_password' not in body['user'] and 'refresh_token' not in body
    cookie = response.headers['set-cookie']
    assert 'HttpOnly' in cookie and 'SameSite=lax' in cookie and 'Max-Age=2592000' in cookie
    access = security.decode_token(body['access_token'], 'access')
    refresh_token = client.cookies[settings.AUTH_COOKIE_NAME]
    refresh = security.decode_token(refresh_token, 'refresh')
    assert access['exp'] - access['iat'] == 86400
    assert refresh['exp'] - refresh['iat'] == 2592000
    assert body['expires_in'] == 86400
    session = await db.get(AuthSession, access['sid'])
    assert session.refresh_hash == service.token_hash(refresh_token)
    assert session.refresh_hash != refresh_token
    me = await client.get('/api/v1/users/me', headers=bearer(response))
    assert me.status_code == 200 and me.json()['username'] == values['username']
    login = await client.post(AUTH + '/login', json={'username': values['username'].upper(), 'password': values['password']})
    assert login.status_code == 200
    assert login.json()['access_token'] != body['access_token']


async def test_wrong_password_and_missing_login_return_same_error(client):
    values, _ = await register(client)
    wrong = await client.post(AUTH + '/login', json={'username': values['username'], 'password': 'WrongPassword'})
    missing = await client.post(AUTH + '/login', json={'username': 'does_not_exist', 'password': 'WrongPassword'})
    assert wrong.status_code == missing.status_code == 401
    assert wrong.json() == missing.json()


async def test_public_registration_cannot_grant_admin(client):
    response = await client.post(AUTH + '/register', json=account(role='admin'))
    assert response.status_code == 422
    _, registered = await register(client)
    denied = await client.get('/api/v1/users/', headers=bearer(registered))
    assert denied.status_code == 403


async def test_duplicate_username_and_overlong_utf8_password(client):
    values, _ = await register(client)
    response = await client.post(AUTH + '/register', json=values)
    assert response.status_code == 409
    invalid = await client.post(AUTH + '/register', json=account(password='я' * 40))
    assert invalid.status_code == 422


async def test_refresh_rotates_rejects_replay_and_slides_30_days(client, db, monkeypatch):
    _, registered = await register(client)
    original = client.cookies[settings.AUTH_COOKIE_NAME]
    old = security.decode_token(original, 'refresh')
    future = datetime.now(timezone.utc) + timedelta(days=29)
    class FutureDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            return future if tz else future.replace(tzinfo=None)
    monkeypatch.setattr(service, 'datetime', FutureDateTime)
    monkeypatch.setattr(security, 'datetime', FutureDateTime)
    response = await client.post(AUTH + '/refresh')
    assert response.status_code == 200, response.text
    rotated = client.cookies[settings.AUTH_COOKIE_NAME]
    claims = security.decode_token(rotated, 'refresh')
    assert rotated != original
    assert claims['sid'] == old['sid'] and claims['jti'] != old['jti']
    assert claims['exp'] - claims['iat'] == 30 * 86400
    assert claims['exp'] >= old['exp'] + 29 * 86400 - 1
    assert response.json()['access_token'] != registered.json()['access_token']
    async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test', headers=CSRF) as replay:
        replay.cookies.set(settings.AUTH_COOKIE_NAME, original)
        assert (await replay.post(AUTH + '/refresh')).status_code == 401
    # Reusing the stale token does not invalidate the user's newly rotated cookie.
    assert (await client.post(AUTH + '/refresh')).status_code == 200


async def test_30_days_of_inactivity_expire_session(client, db):
    _, registered = await register(client)
    claims = security.decode_token(registered.json()['access_token'], 'access')
    session = await db.get(AuthSession, claims['sid'])
    session.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
    await db.commit()
    assert (await client.post(AUTH + '/refresh')).status_code == 401
    assert settings.AUTH_COOKIE_NAME not in client.cookies
    assert (await client.get('/api/v1/users/me', headers=bearer(registered))).status_code == 401


async def test_expired_refresh_jwt_is_rejected_even_if_db_session_is_valid(client, db):
    _, response = await register(client)
    claims = security.decode_token(response.json()['access_token'], 'access')
    expired = security.create_token(response.json()['user']['id'], claims['sid'], 'refresh', timedelta(seconds=-1))
    session = await db.get(AuthSession, claims['sid'])
    session.refresh_hash = service.token_hash(expired)
    await db.commit()
    client.cookies.clear()
    client.cookies.set(settings.AUTH_COOKIE_NAME, expired)
    assert (await client.post(AUTH + '/refresh')).status_code == 401


async def test_logout_revokes_access_and_refresh(client):
    _, response = await register(client)
    old_refresh = client.cookies[settings.AUTH_COOKIE_NAME]
    assert (await client.post(AUTH + '/logout')).status_code == 204
    assert settings.AUTH_COOKIE_NAME not in client.cookies
    assert (await client.get('/api/v1/patients/', headers=bearer(response))).status_code == 401
    client.cookies.set(settings.AUTH_COOKIE_NAME, old_refresh)
    assert (await client.post(AUTH + '/refresh')).status_code == 401


@pytest.mark.parametrize('url', ['/api/v1/patients/', '/api/v1/ml/status', '/api/v1/users/me'])
async def test_clinical_and_user_endpoints_reject_guests(client, url):
    assert (await client.get(url)).status_code == 401


async def test_refresh_is_not_an_access_token_and_expired_access_can_refresh(client):
    _, response = await register(client)
    refresh = client.cookies[settings.AUTH_COOKIE_NAME]
    assert (await client.get('/api/v1/patients/', headers={'Authorization': f'Bearer {refresh}'})).status_code == 401
    claims = security.decode_token(response.json()['access_token'], 'access')
    expired = security.create_access_token(response.json()['user']['id'], claims['sid'], timedelta(seconds=-1))
    assert (await client.get('/api/v1/patients/', headers={'Authorization': f'Bearer {expired}'})).status_code == 401
    renewed = await client.post(AUTH + '/refresh')
    assert renewed.status_code == 200
    assert (await client.get('/api/v1/patients/', headers=bearer(renewed))).status_code == 200


async def test_admin_creation_deactivation_and_live_role_checks(client, db):
    _, response = await register(client)
    user = await db.get(User, response.json()['user']['id'])
    user.role = UserRole.ADMIN
    await db.commit()
    headers = bearer(response)
    assert (await client.get('/api/v1/users/', headers=headers)).status_code == 200
    created = await client.post('/api/v1/users/', json=account(role='admin'), headers=headers)
    assert created.status_code == 201 and created.json()['role'] == 'admin'
    own = await client.patch(f'/api/v1/users/{user.id}', json={'is_active':False}, headers=headers)
    assert own.status_code == 400
    user.role = UserRole.DOCTOR
    await db.commit()
    assert (await client.get('/api/v1/users/', headers=headers)).status_code == 403
    user.is_active = False
    await db.commit()
    assert (await client.get('/api/v1/patients/', headers=headers)).status_code == 401
    assert (await client.post(AUTH + '/refresh')).status_code == 401


async def test_profile_can_edit_names_but_not_role(client):
    _, response = await register(client)
    updated = await client.patch('/api/v1/users/me', headers=bearer(response), json={'first_name':'Новое', 'last_name':'Имя'})
    assert updated.status_code == 200
    assert updated.json()['full_name'] == 'Новое Имя'
    denied = await client.patch('/api/v1/users/me', headers=bearer(response), json={'role':'admin'})
    assert denied.status_code == 422


async def test_cookie_mutations_require_csrf_header(client):
    for route in ('login', 'register', 'refresh', 'logout'):
        response = await client.post(f'{AUTH}/{route}', json=account(), headers={'X-CSRF-Protection':''})
        assert response.status_code == 403


async def test_migration_kept_legacy_accounts_patients_and_cycles(client, db):
    # These rows are prepared before upgrading 001 -> 002 in the migration test DB.
    existing = (await db.execute(select(User).where(User.email == 'legacy@example.test'))).scalar_one_or_none()
    if existing is None:
        pytest.skip('No legacy migration fixture in this database')
    assert existing.role == UserRole.DOCTOR
    assert existing.username == f'user_{existing.id}'
    assert existing.full_name == 'Legacy Doctor'
    assert (await db.execute(text("SELECT count(*) FROM cycles c JOIN patients p ON c.patient_id=p.id WHERE p.medical_record_number='MIGRATION_CHECK' AND c.assigned_doctor_id=:user"), {'user':existing.id})).scalar_one() == 1
    logged = await client.post(AUTH + '/login', json={'username':'legacy@example.test','password':'LegacyPassword12!'})
    assert logged.status_code == 200


async def test_concurrent_refresh_rotates_cookie_only_once():
    import asyncio
    import runpy
    from pathlib import Path
    from sqlalchemy import delete
    from sqlalchemy.ext.asyncio import async_sessionmaker
    engine = create_async_engine(URL.replace('postgresql://', 'postgresql+asyncpg://'))
    factory = async_sessionmaker(engine, expire_on_commit=False)
    isolated = runpy.run_path(str(Path(__file__).parents[1] / 'app/main.py'))['app']
    async def db_for_request():
        async with factory() as session:
            yield session
    isolated.dependency_overrides[get_db] = db_for_request
    user_id = None
    try:
        async with AsyncClient(transport=ASGITransport(app=isolated), base_url='http://test', headers=CSRF) as initial:
            response = await initial.post(AUTH + '/register', json=account())
            assert response.status_code == 201
            user_id = response.json()['user']['id']
            refresh_cookie = initial.cookies[settings.AUTH_COOKIE_NAME]
        async def refresh_once():
            async with AsyncClient(transport=ASGITransport(app=isolated), base_url='http://test', headers=CSRF) as browser:
                browser.cookies.set(settings.AUTH_COOKIE_NAME, refresh_cookie)
                return await browser.post(AUTH + '/refresh')
        responses = await asyncio.gather(refresh_once(), refresh_once())
        assert sorted(response.status_code for response in responses) == [200, 401]
    finally:
        if user_id:
            async with factory() as session:
                await session.execute(delete(User).where(User.id == user_id))
                await session.commit()
        await engine.dispose()


async def test_tampered_access_token_is_rejected(client):
    _, response = await register(client)
    token = response.json()['access_token']
    claims = jwt.get_unverified_claims(token)
    tampered = jwt.encode(claims, 'incorrect-signing-key', algorithm=settings.ALGORITHM)
    assert (await client.get('/api/v1/users/me', headers={'Authorization': f'Bearer {tampered}'})).status_code == 401
