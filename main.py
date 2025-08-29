# ----------- Bibliotecas -----------



from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from fastapi.params import Header
import requests
from fastapi.security import HTTPBearer, OAuth2PasswordBearer
from jose import JWTError, jwt, jwk

from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

from typing import Annotated
from sqlalchemy.orm import Session

from config.database import SspUsuarioBase, SspCriminososBase
from functions.auth_crud import verify_crud_api_key

from functions.auth_keycloak import decode_jwt
from functions.dependencias import get_ssp_usuario_db, get_ssp_criminosos_db

from config.database import ssp_usuario_engine, ssp_criminosos_engine
# from firebase_admin import credentials, initialize_app

from dotenv import load_dotenv

# from functions.auth_utils import verify_token


# from functions.requests.auth_with_firebase import auth_with_firebase
from functions.requests.buscar_ficha_criminal import buscar_ficha_criminal 
from functions.requests.buscar_similaridade import buscar_similaridade
# from functions.requests.perfil_usuario import perfil_usuario

from functions.crud.create_identidade import create_identidade
from functions.crud.delete_identidade import delete_identidade
from functions.crud.create_usuario import create_usuario
from functions.crud.update_usuario import update_usuario
from functions.crud.delete_usuario import delete_usuario
from functions.crud.update_ficha import update_ficha
from functions.crud.create_crime import CrimeStatus, create_crime


from fastapi import Query



load_dotenv()


app = FastAPI()



app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ----------- Dependências -----------


ssp_usuario_db_dependency = Annotated[Session, Depends(get_ssp_usuario_db)]
ssp_criminosos_db_dependency = Annotated[Session, Depends(get_ssp_criminosos_db)]

SspUsuarioBase.metadata.create_all(bind=ssp_usuario_engine)
SspCriminososBase.metadata.create_all(bind=ssp_criminosos_engine)


# ---------- Rotas -----------


# class FirebaseToken(BaseModel):
#     firebase_token: str
  

# @app.get("/protected", tags=["KeyCloak"])
# async def protected_route(authorization: str = Header(...)):
#     """
#     Valida o token enviado no header Authorization: Bearer <token>
#     """
#     if not authorization.startswith("Bearer "):
#         raise HTTPException(status_code=401, detail="Token inválido")
#     token = authorization.split(" ")[1]
#     decoded_token = decode_jwt(token)
#     return {"message": "You have access to this route", "user": decoded_token}
    
# @app.get("/callback", tags=["KeyCloak"])
# async def keycloak_callback(code: str):
#     """
#     Recebe o authorization code do Keycloak e troca pelo token
#     """
#     token_url = f"{KEYCLOAK_URL}/protocol/openid-connect/token"
#     data = {
#         "grant_type": "authorization_code",
#         "client_id": CLIENT_ID,
#         "client_secret": KEYCLOAK_CLIENT_SECRET,
#         "code": code,
#         "redirect_uri": "http://localhost:8000/callback",  # mesma URL registrada no Keycloak
#     }
#     response = requests.post(token_url, data=data)
#     if response.status_code != 200:
#         raise HTTPException(status_code=400, detail="Erro ao trocar código por token")
#     return response.json()  # aqui vem access_token, refresh_token, id_token



# @app.get("/usuario/perfil", tags=["Requisição do Aplicativo"], dependencies=[Depends(verify_token)])

# async def get_perfil_usuario(
#     db: ssp_usuario_db_dependency,
#     user_data: dict = Depends(verify_token),
# ):
#     return perfil_usuario(db, user_data)



# @app.post("/auth/firebase", tags=["Requisição do Aplicativo"])

# async def get_firebase_auth(
#     token_data: str
# ):
#     return auth_with_firebase(token_data)

bearer_scheme = HTTPBearer()

KEYCLOAK_URL = "http://localhost:8090/realms/interno/protocol/openid-connect"
CLIENT_ID = "visionapp"

# Carrega as chaves públicas do Keycloak
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




@app.post(
    "/buscar-similaridade-foto/", 
    tags=["Requisição do Aplicativo"]
)
async def get_buscar_similaridade(
    ficha_db: ssp_criminosos_db_dependency,
    user_db: ssp_usuario_db_dependency,
    file: UploadFile = File(...),
    matricula: str = Query(...),
    user=Depends(validate_token),   # ← aqui você pega o payload do token
):
    try:

        return buscar_similaridade(matricula, ficha_db, user_db, file)

    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)

    

@app.get("/dados")
def dados(user=Depends(validate_token)):
    return {"msg": "Token válido", "usuario": user.get("preferred_username")}


@app.get("/buscar-ficha-criminal/{cpf}", dependencies=[Depends(validate_token)], tags=["Requisição do Aplicativo"])
async def get_buscar_ficha_criminal(
    cpf: str, # <- Novo parâmetro obrigatório
    ficha_db: ssp_criminosos_db_dependency,
    user_db: ssp_usuario_db_dependency,
    matricula: str = Query(...), 
):
    try:
        return buscar_ficha_criminal(cpf, matricula, ficha_db, user_db)
    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


# CRUD 


@app.post("/create-identidade/", dependencies=[Depends(verify_crud_api_key)], tags=["CRUD"])

async def get_create_identidade(
    db: ssp_criminosos_db_dependency,
    cpf: str,
    nome: str,
    nome_mae: str,
    nome_pai: str,
    data_nascimento: str,
    gemeo: bool = False,
    file: UploadFile = File(...)
):
    try:
        return create_identidade(
            db,
            cpf,
            nome,
            nome_mae,
            nome_pai,
            data_nascimento,
            gemeo,
            file
        )
    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@app.delete("/delete-identidade/{cpf}", dependencies=[Depends(verify_crud_api_key)], tags=["CRUD"])
async def get_delete_identidade(cpf: str, db: ssp_criminosos_db_dependency):
    try:
        return delete_identidade(cpf, db)
    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    


@app.post("/create-usuario/",  dependencies=[Depends(verify_crud_api_key)], tags=["CRUD"])
async def get_create_usuario(
    db: ssp_usuario_db_dependency,
    matricula: str,
    nome: str,
    nome_mae: str,
    nome_pai: str,
    data_nascimento: str,
    cpf: str,
    telefone: str,
    sexo: str,
    nacionalidade: str,
    naturalidade: str,
    tipo_sanguineo: str,
    cargo: str,
    nivel_classe: str,
    senha: str,
    nome_social: str = None
):
    try:
        return create_usuario(
            db,
            matricula,
            nome,
            nome_mae,
            nome_pai,
            data_nascimento,
            cpf,
            telefone,
            sexo,
            nacionalidade,
            naturalidade,
            tipo_sanguineo,
            cargo,
            nivel_classe,
            senha,
            nome_social
        )
    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@app.put("/update-usuario/{matricula}",  dependencies=[Depends(verify_crud_api_key)], tags=["CRUD"])
async def get_update_usuario(
    matricula: str,
    db: ssp_usuario_db_dependency,
    nome: str = None,
    nome_social: str = None,
    nome_mae: str = None,
    nome_pai: str = None,
    data_nascimento: str = None,
    cpf: str = None,
    telefone: str = None,
    sexo: str = None,
    nacionalidade: str = None,
    naturalidade: str = None,
    tipo_sanguineo: str = None,
    cargo: str = None,
    nivel_classe: str = None,
    senha: str = None
):
    try:
        return update_usuario(
            matricula,
            db,
            nome,
            nome_social,
            nome_mae,
            nome_pai,
            data_nascimento,
            cpf,
            telefone,
            sexo,
            nacionalidade,
            naturalidade,
            tipo_sanguineo,
            cargo,
            nivel_classe,
            senha
        )
    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)

@app.delete("/delete-usuario/{matricula}",  dependencies=[Depends(verify_crud_api_key)], tags=["CRUD"])
async def get_delete_usuario(matricula: str, db: ssp_usuario_db_dependency):
    
    try:    
        return delete_usuario(matricula, db)
    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@app.put("/update-ficha/",   dependencies=[Depends(verify_crud_api_key)], tags=["CRUD"])
async def get_update_ficha(
    db: ssp_criminosos_db_dependency,
    cpf: str,
    vulgo: str = None,
):
    try:
        return update_ficha(
            db,
            cpf,
            vulgo
        )
    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@app.post("/create-crime/",   dependencies=[Depends(verify_crud_api_key)], tags=["CRUD"])
async def get_create_crime(
    db: ssp_criminosos_db_dependency,
    cpf: str,
    nome_crime: str,
    artigo: str,
    descricao: str,
    data_ocorrencia: str,
    cidade: str,
    estado: str,
    status: CrimeStatus,
    vulgo: str = None,
):
    try:
        return create_crime(
            db,
            cpf,
            nome_crime,
            artigo,
            descricao,
            data_ocorrencia,
            cidade,
            estado,
            status,
            vulgo
        )
    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
