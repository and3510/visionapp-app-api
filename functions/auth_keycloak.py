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

# KEYCLOAK_URL = "http://sso.ajvale.com.br/realms/interno/protocol/openid-connect"
# CLIENT_ID = "visionapp"
# REDIRECT_URI = "http://localhost:8000/callback"   
# VALID_CLIENTS = ["visionapp", "visionapp-interno"]


# jwks_data = requests.get(f"{KEYCLOAK_URL}/certs").json()



# def get_public_key(token: str):
#     headers = jwt.get_unverified_header(token)
#     kid = headers["kid"]
#     # Recarrega sempre as chaves
#     jwks_data = requests.get(f"{KEYCLOAK_URL}/certs").json()
#     for key in jwks_data["keys"]:
#         if key["kid"] == kid:
#             return key
#     raise HTTPException(status_code=401, detail="Chave pública não encontrada")




# def validate_token(credentials=Depends(bearer_scheme)):
#     token = credentials.credentials
#     public_key = get_public_key(token)
#     try:
#         # Decodifica o token sem verificar 'aud' diretamente
#         payload = jwt.decode(
#             token,
#             public_key,
#             algorithms=["RS256"],
#             audience="account"  # desativa verificação de 'aud'
#         )

#         # Verifica se o token é do client correto
#         if payload.get("azp") not in VALID_CLIENTS:
#             raise HTTPException(status_code=401, detail="Token não autorizado para este client")


#         return payload
#     except Exception as e:
#         raise HTTPException(status_code=401, detail=f"Token inválido: {str(e)}")


