from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import HTTPBearer, OAuth2AuthorizationCodeBearer
from jose import jwt
import requests
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

app = FastAPI()

bearer_scheme = HTTPBearer()
oauth2_interno = OAuth2AuthorizationCodeBearer(
    authorizationUrl="https://sso.ajvale.com.br/realms/interno/protocol/openid-connect/auth",
    tokenUrl="https://sso.ajvale.com.br/realms/interno/protocol/openid-connect/token",
)

KEYCLOAK_JWKS_URL = "https://sso.ajvale.com.br/realms/interno/protocol/openid-connect/certs"
JWKS = requests.get(KEYCLOAK_JWKS_URL).json()


def get_public_key(token: str):
    # Pega o kid do token
    headers = jwt.get_unverified_header(token)
    kid = headers.get("kid")
    if not kid:
        raise HTTPException(status_code=401, detail="Token sem 'kid'")

    # Procura a chave correspondente no JWKS
    key_dict = next((k for k in JWKS["keys"] if k["kid"] == kid and k["use"] == "sig"), None)
    if not key_dict:
        raise HTTPException(status_code=401, detail="Chave pública não encontrada no JWKS")

    # Converte a chave RSA para objeto e depois para PEM
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import padding
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives.asymmetric import rsa
    import base64

    # Monta a chave pública RSA a partir de n/e
    n_int = int.from_bytes(base64.urlsafe_b64decode(key_dict["n"] + "=="), "big")
    e_int = int.from_bytes(base64.urlsafe_b64decode(key_dict["e"] + "=="), "big")
    public_numbers = rsa.RSAPublicNumbers(e_int, n_int)
    public_key_obj = public_numbers.public_key(default_backend())

    # Retorna PEM como string
    pem = public_key_obj.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode("utf-8")
    return pem


def decode_token(token: str):
    try:
        public_key = get_public_key(token)
        payload = jwt.decode(
            token,
            public_key,
            algorithms=["RS256"],
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
            raise Exception("Audience inválido no token")

        if not (token_aud & allowed_audiences):
            raise Exception("Audience não permitido")

        return payload

    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Token inválido: {str(e)}")


def get_auth(token_oauth: str = Depends(oauth2_interno),
             api_key: str = Depends(bearer_scheme)):
    if token_oauth:
        payload = decode_token(token_oauth)
        return {"type": "oauth", "token": token_oauth, "payload": payload}
    if api_key:
        payload = decode_token(api_key.credentials)
        return {"type": "api_key", "token": api_key.credentials, "payload": payload}
    raise HTTPException(status_code=401, detail="Não autenticado")


