from fastapi.params import Depends
from jose import jwt
from fastapi import HTTPException
from fastapi.security import HTTPBearer, OAuth2AuthorizationCodeBearer
import requests


bearer_scheme = HTTPBearer()
# OAuth2 para client interno
oauth2_interno = OAuth2AuthorizationCodeBearer(
    authorizationUrl="https://sso.ajvale.com.br/realms/interno/protocol/openid-connect/auth",
    tokenUrl="https://sso.ajvale.com.br/realms/interno/protocol/openid-connect/token",
)

KEYCLOAK_JWKS_URL = "https://sso.ajvale.com.br/realms/interno/protocol/openid-connect/certs"
JWKS = requests.get(KEYCLOAK_JWKS_URL).json()



def decode_token(token: str):
    try:
        # pega a primeira key do JWKS (simples, mas pode melhorar)
        key = JWKS["keys"][0]

        payload = jwt.decode(
            token,
            key,
            algorithms=[key["alg"]],
            options={"verify_aud": False}
        )

        # valida audiences manualmente
        allowed_audiences = {"visionapp-interno", "visionapp"}
        token_aud = payload.get("aud")

        if isinstance(token_aud, str):
            token_aud = {token_aud}
        elif isinstance(token_aud, list):
            token_aud = set(token_aud)
        else:
            raise Exception("audience inválido no token")

        if not (token_aud & allowed_audiences):
            raise Exception("audience não permitido")

        return payload

    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Token inválido: {str(e)}")



def get_auth(token_oauth: str = Depends(oauth2_interno),
             api_key: str = Depends(bearer_scheme)):
    if token_oauth:
        payload = decode_token(token_oauth)
        return {"type": "oauth", "token": token_oauth, "payload": payload}
    if api_key:
        return {"type": "api_key", "token": api_key}
    raise HTTPException(status_code=401, detail="Não autenticado")
