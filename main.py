# ----------- Bibliotecas -----------


from fastapi import FastAPI, Depends, HTTPException, UploadFile, File


from fastapi.middleware.cors import CORSMiddleware

from typing import Annotated
from sqlalchemy.orm import Session

from config.database import SspUsuarioBase, SspCriminososBase


from config.models import FichaCriminalRequest
from functions.auth_keycloak import get_auth
from functions.dependencias import get_ssp_usuario_db, get_ssp_criminosos_db

from config.database import ssp_usuario_engine, ssp_criminosos_engine


from dotenv import load_dotenv
from fastapi import Form
from functions.requests.buscar_ficha_criminal import buscar_ficha_criminal 
from functions.requests.buscar_similaridade import buscar_similaridade



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
    matricula: str = Form(...),
    file: UploadFile = File(...),
    user=Depends(get_auth),
):
    try:
        return buscar_similaridade(ficha_db, user_db,user, matricula, file, )
    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)





@app.post("/buscar-ficha-criminal/", tags=["Requisição do Aplicativo"])
async def get_buscar_ficha_criminal(
    request: FichaCriminalRequest,
    ficha_db: ssp_criminosos_db_dependency,
    user_db: ssp_usuario_db_dependency,
    user=Depends(get_auth)
):
    try:
        return buscar_ficha_criminal(request.cpf, ficha_db, user_db, user, matricula=request.matricula)
    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    

