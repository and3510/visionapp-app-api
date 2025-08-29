# ----------- Bibliotecas -----------



from fastapi import FastAPI, Depends, HTTPException, UploadFile, File


from fastapi.middleware.cors import CORSMiddleware

from typing import Annotated
from sqlalchemy.orm import Session

from config.database import SspUsuarioBase, SspCriminososBase
from functions.auth_crud import verify_crud_api_key

from functions.auth_keycloak import validate_token
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

    


@app.get("/buscar-ficha-criminal/{cpf}", tags=["Requisição do Aplicativo"])
async def get_buscar_ficha_criminal(
    cpf: str, 
    ficha_db: ssp_criminosos_db_dependency,
    user_db: ssp_usuario_db_dependency,
    matricula: str = Query(...),
    user=Depends(validate_token)
):
    try:
        return buscar_ficha_criminal(cpf, matricula, ficha_db, user_db)
    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@app.get("/", tags=["Requisição do Aplicativo"])
def dados(user=Depends(validate_token)):
    return {"msg": "Token válido", "usuario": user.get("preferred_username")}


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
