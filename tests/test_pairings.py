from app.models.user import User
from app.core.config import settings

def create_user(client, session, email="test@example.com"):
    user = User(email=email)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user

def get_auth_headers(user_id):
    # Mock JWT - in real tests we might generate a real token or mock the dependency
    # Here we should verify how deps.py validates. It uses jose jwt.decode.
    # So we need to generate a valid token signed with SECRET_KEY.
    from jose import jwt
    import datetime
    
    token_data = {"sub": str(user_id)}
    expire = datetime.datetime.utcnow() + datetime.timedelta(minutes=60)
    to_encode = token_data.copy()
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
    return {"Authorization": f"Bearer {encoded_jwt}"}

def test_generate_pairing_code(client, session):
    user = create_user(client, session)
    headers = get_auth_headers(user.id)
    
    response = client.post(f"{settings.API_V1_STR}/pairings/code", headers=headers)
    assert response.status_code == 200
    assert "pairing_code" in response.json()
    
    # Verify DB
    session.refresh(user)
    assert user.pairing_code is not None

def test_pair_users(client, session):
    user1 = create_user(client, session, "u1@example.com")
    user2 = create_user(client, session, "u2@example.com")
    
    # User 1 gets code
    headers1 = get_auth_headers(user1.id)
    resp = client.post(f"{settings.API_V1_STR}/pairings/code", headers=headers1)
    code = resp.json()["pairing_code"]
    
    # User 2 pairs
    headers2 = get_auth_headers(user2.id)
    resp = client.post(f"{settings.API_V1_STR}/pairings/pair", headers=headers2, json={"code": code})
    assert resp.status_code == 200
    
    # Wait, variable name typo above.
    assert resp.status_code == 200
    assert resp.json()["partner"]["email"] == "u1@example.com"
    
    # Verify DB
    session.refresh(user1)
    session.refresh(user2)
    assert user1.partner_id == user2.id
    assert user2.partner_id == user1.id
    assert user1.pairing_code is None
    assert user2.pairing_code is None

def test_unpair_users(client, session):
    user1 = create_user(client, session, "u1@example.com")
    user2 = create_user(client, session, "u2@example.com")
    
    # Manually pair
    user1.partner_id = user2.id
    user2.partner_id = user1.id
    session.add(user1)
    session.add(user2)
    session.commit()
    
    headers1 = get_auth_headers(user1.id)
    resp = client.post(f"{settings.API_V1_STR}/pairings/unpair", headers=headers1)
    assert resp.status_code == 200
    
    session.refresh(user1)
    session.refresh(user2)
    assert user1.partner_id is None
    assert user2.partner_id is None
