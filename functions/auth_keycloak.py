from typing import Optional
from jose import jwt, JWTError
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import httpx

# Configurações do Keycloak
KEYCLOAK_URL = "http://localhost:8080/realms/interno/protocol/openid-connect"
CLIENT_ID = "visionapp"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{KEYCLOAK_URL}/token")

# Buscar a chave pública do Keycloak
async def get_public_key():
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{KEYCLOAK_URL}/certs")
        jwks = resp.json()
        return jwks

# Função para validar o token JWT
async def verify_token_keycloak(token: str = Depends(oauth2_scheme)):
    try:
        jwks = await get_public_key()
        unverified_header = jwt.get_unverified_header(token)

        # Localizar a chave correta
        key = next(
            (k for k in jwks["keys"] if k["kid"] == unverified_header["kid"]), None
        )
        if key is None:
            raise HTTPException(status_code=401, detail="Invalid token header")

        payload = jwt.decode(
            token,
            key,
            algorithms=["RS256"],
            audience=CLIENT_ID,
        )
        return payload

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )
