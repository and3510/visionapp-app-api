from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import HTTPBearer, OAuth2AuthorizationCodeBearer
import httpx
from jose import jwt, JWTError
import requests


# Esquemas de autenticação
# bearer_scheme = HTTPBearer()
oauth2_interno = OAuth2AuthorizationCodeBearer(
    authorizationUrl="https://sso.ajvale.com.br/realms/interno/protocol/openid-connect/auth",
    tokenUrl="https://sso.ajvale.com.br/realms/interno/protocol/openid-connect/token",
)

# JWKS do Keycloak
KEYCLOAK_JWKS_URL = "https://sso.ajvale.com.br/realms/interno/protocol/openid-connect/certs"
JWKS = requests.get(KEYCLOAK_JWKS_URL).json()


def decode_token(token: str):
    """
    Valida e decodifica o JWT usando as chaves do JWKS.
    Tenta cada chave até achar uma que funcione.
    Também verifica manualmente o 'audience'.
    """
    last_error = None
    for key_dict in JWKS["keys"]:
        try:
            # Converte a chave para JSON string
            jwk_json = key_dict

            payload = jwt.decode(
                token,
                jwk_json,
                algorithms=["RS256"],
                options={"verify_aud": False}  # validamos audience manualmente
            )

            # valida audiences permitidos
            allowed_audiences = {"visionapp-interno", "visionapp"}
            token_aud = payload.get("aud")
            if isinstance(token_aud, str):
                token_aud = {token_aud}
            elif isinstance(token_aud, list):
                token_aud = set(token_aud)
            else:
                raise Exception("Audience inválido no token")

            if not (token_aud & allowed_audiences):
                raise Exception("Audience não permitido")

            return payload

        except jwt.JWTError as e:
            last_error = e
            continue

    raise HTTPException(status_code=401, detail=f"Token inválido: {last_error}")


def get_auth(
    token_oauth: str = Depends(oauth2_interno),
    # api_key: str = Depends(bearer_scheme)
):
    """
    Autentica requisições usando OAuth2 ou API Key (JWT no header Authorization).
    """
    if token_oauth:
        payload = decode_token(token_oauth)
        return {"type": "oauth", "token": token_oauth, "payload": payload}
    # if api_key:
    #     payload = decode_token(api_key.credentials)
    #     return {"type": "api_key", "token": api_key.credentials, "payload": payload}
    raise HTTPException(status_code=401, detail="Não autenticado")


async def fetch_keycloak_userinfo(token: str):
    """
    Busca informações do usuário autenticado diretamente do Keycloak.
    """
    url = "https://sso.ajvale.com.br/realms/interno/protocol/openid-connect/userinfo"
    headers = {"Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Erro ao buscar userinfo")
        return response.json()