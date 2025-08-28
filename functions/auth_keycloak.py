from typing import Optional
from jose import jwt, jwk, JWTError
from fastapi import HTTPException
from fastapi.security import OAuth2PasswordBearer
import requests

# Configurações do Keycloak
KEYCLOAK_URL = "http://localhost:8090/realms/interno"
CLIENT_ID = "visionapp"
KEYCLOAK_CLIENT_SECRET = "I0M9dvrSj9lMW0Wh7NlN5Cw02UVthfld"
KEYCLOAK_API_URL = f"{KEYCLOAK_URL}/protocol/openid-connect/token"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{KEYCLOAK_API_URL}")

# Buscar a chave pública do Keycloak
def get_keycloak_public_key():
        jwt_url = f"{KEYCLOAK_URL}/protocol/openid-connect/certs"
        response = requests.get(jwt_url)
        return response.json()


# Função para validar o token JWT
def decode_jwt(token: str):
    public_key = get_keycloak_public_key()
    headers = jwt.get_unverified_header(token)
    if not headers or 'kid' not in headers:
        raise HTTPException(status_code=403, detail="Invalid token: no kid header")
    for key in public_key['keys']:
        if key['kid'] == headers['kid']:
            try:
                key_obj = jwk.construct(key)
                # Ajuste aqui: use o valor correto do audience
                payload = jwt.decode(token, key_obj, algorithms=['RS256'], audience="account")
                return payload
            except JWTError as e:
                raise HTTPException(status_code=403, detail="Token validation error: " + str(e))
    raise HTTPException(status_code=403, detail="Invalid key")


def get_tokens(code: str):
    url = "http://localhost:8090/realms/interno/protocol/openid-connect/token"
    data = {
        "grant_type": "authorization_code",
        "client_id": "visionapp",
        "client_secret": "I0M9dvrSj9lMW0Wh7NlN5Cw02UVthfld",
        "code": code,
        "redirect_uri": "http://localhost:8000/callback",
    }
    response = requests.post(url, data=data)
    return response.json()
