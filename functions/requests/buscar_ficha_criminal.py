import os
from fastapi import Depends, HTTPException
from typing import Annotated
from sqlalchemy.orm import Session
from config.database import SspCriminososBase, SspUsuarioBase
from functions.auth_keycloak import get_auth
from functions.dependencias import get_ssp_criminosos_db, get_ssp_usuario_db
import config.models as models
from config.database import ssp_criminosos_engine, ssp_usuario_engine
from uuid import uuid4
from datetime import datetime
import pytz

from functions.minio import proxy_object_by_cpf 


ssp_criminosos_db_dependency = Annotated[Session, Depends(get_ssp_criminosos_db)]

SspCriminososBase.metadata.create_all(bind=ssp_criminosos_engine)

ssp_usuario_db_dependency = Annotated[Session, Depends(get_ssp_usuario_db)]

SspUsuarioBase.metadata.create_all(bind=ssp_usuario_engine)


def buscar_ficha_criminal(
    cpf: str,
    ficha_db: ssp_criminosos_db_dependency,
    user_db: ssp_usuario_db_dependency,
    user: dict,
    matricula: str = None
):
    identidade = ficha_db.query(models.Identidade).filter(models.Identidade.cpf == cpf).first()
    ficha_criminal = ficha_db.query(models.FichaCriminal).filter(models.FichaCriminal.cpf == cpf).first()
    crimes = []

    if ficha_criminal:
        crimes = ficha_db.query(models.Crime).filter(models.Crime.id_ficha == ficha_criminal.id_ficha).all()

    # dados do token
    payload = user["payload"]
    user_id = payload.get("sub")  # ou outro identificador único

    br_tz = pytz.timezone('America/Sao_Paulo')

    log_resultado_cpf = models.LogResultadoCpf(
        id_ocorrido=str(uuid4()).replace("-", "")[:30],
        matricula=matricula,  # ← agora vem do parâmetro
        data_ocorrido=datetime.now(br_tz).strftime("%H:%M:%S %d/%m/%Y"),
        cpf=cpf,
        id_usuario=user_id,
        id_ficha=ficha_criminal.id_ficha if ficha_criminal else None
    )
    user_db.add(log_resultado_cpf)
    user_db.commit()
    user_db.refresh(log_resultado_cpf)

    foto_url_result = proxy_object_by_cpf(cpf)
    foto_url = foto_url_result["url"] if isinstance(foto_url_result, dict) and "url" in foto_url_result else None

    resposta = {
        "cpf": identidade.cpf,
        "nome": identidade.nome,
        "nome_mae": identidade.nome_mae,
        "nome_pai": identidade.nome_pai,
        "data_nascimento": identidade.data_nascimento,
        "foto_url": foto_url,
        "gemeo": identidade.gemeo,
        "ficha_criminal": {
            "id_ficha": ficha_criminal.id_ficha if ficha_criminal else None,
            "vulgo": ficha_criminal.vulgo if ficha_criminal else None,
        },
        "crimes": [
            {
                "id_crime": crime.id_crime,
                "nome_crime": crime.nome_crime,
                "artigo": crime.artigo,
                "descricao": crime.descricao,
                "data_ocorrencia": crime.data_ocorrencia,
                "cidade": crime.cidade,
                "estado": crime.estado,
                "status": crime.status,
            }
            for crime in crimes
        ]
    }

    return resposta