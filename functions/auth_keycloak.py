from fastapi.params import Depends
from jose import jwt
from fastapi import HTTPException
from fastapi.security import HTTPBearer
import requests


bearer_scheme = HTTPBearer()

KEYCLOAK_URL = "http://sso.ajvale.com.br/realms/interno/protocol/openid-connect"
CLIENT_ID = "visionapp"
REDIRECT_URI = "http://localhost:8000/callback"   

jwks_data = requests.get(f"{KEYCLOAK_URL}/certs").json()


def get_public_key(token: str):
    headers = jwt.get_unverified_header(token)
    kid = headers["kid"]
    # Recarrega sempre as chaves
    jwks_data = requests.get(f"{KEYCLOAK_URL}/certs").json()
    for key in jwks_data["keys"]:
        if key["kid"] == kid:
            return key
    raise HTTPException(status_code=401, detail="Chave pública não encontrada")



def validate_token(credentials=Depends(bearer_scheme)):
    token = credentials.credentials
    public_key = get_public_key(token)
    try:
        # Decodifica o token sem verificar 'aud' diretamente
        payload = jwt.decode(
            token,
            public_key,
            algorithms=["RS256"],
            audience="account"  # desativa verificação de 'aud'
        )

        # Verifica se o token é do client correto
        if payload.get("azp") != CLIENT_ID:
            raise HTTPException(status_code=401, detail="Token não autorizado para este client")

        return payload
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Token inválido: {str(e)}")


