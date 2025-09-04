from sqlalchemy import Column, String, Boolean, Text
from config.database import SspCriminososBase, SspUsuarioBase
from pgvector.sqlalchemy import Vector 



class Log_Resultado_Reconhecimento(SspUsuarioBase):
    __tablename__ = "log_resultado_reconhecimento"

    id_ocorrido = Column(String(30), primary_key=True, index=True)  # Gera um novo ID com no máximo 20 caracteres
    matricula = Column(String(10), primary_key=True, index=True)
    id_usuario = Column(String(50), nullable=False)
    distancia = Column(String(45), nullable=False)
    cpf = Column(String(14), nullable=True)
    id_ficha = Column(String(30), nullable=True)
    status_reconhecimento = Column(String(90), nullable=False)
    data_ocorrido = Column(String(50), nullable=False)
    url_facial_referencia = Column(String(200), nullable=True)


class Log_Resultado_Cpf(SspUsuarioBase):
    __tablename__ = "log_resultado_cpf"

    id_ocorrido = Column(String(30), primary_key=True, index=True)
    matricula = Column(String(10), primary_key=True, index=True)
    id_usuario = Column(String(50), nullable=False)
    cpf = Column(String(14), nullable=True)
    id_ficha = Column(String(30), nullable=True)
    data_ocorrido = Column(String(50), nullable=False)

class Identidade(SspCriminososBase):
    __tablename__ = "identidade"

    cpf = Column(String(14), primary_key=True, index=True)
    nome = Column(String(150), nullable=False)
    nome_mae = Column(String(150), nullable=False)
    nome_pai = Column(String(150), nullable=False)
    data_nascimento = Column(String(20), nullable=False)
    vetor_facial = Column(Vector(128), nullable=False)  # coerente com VECTOR(128)
    url_facial = Column(String(255), nullable=False)
    gemeo = Column(Boolean, nullable=False, default=False)


class FichaCriminal(SspCriminososBase):
    __tablename__ = "ficha_criminal"

    id_ficha = Column(String(30), primary_key=True, index=True)
    cpf = Column(String(14), primary_key=True, index=True)
    vulgo = Column(String(100), nullable=False)


class Crime(SspCriminososBase):
    __tablename__ = "crime"

    id_crime = Column(String(30), primary_key=True, index=True)
    id_ficha = Column(String(30), nullable=False)
    nome_crime = Column(String(150), nullable=False)
    artigo = Column(String(100), nullable=False)
    descricao = Column(Text, nullable=False)
    data_ocorrencia = Column(String(20), nullable=False)
    cidade = Column(String(100), nullable=False)
    estado = Column(String(2), nullable=False)
    status = Column(String(20), nullable=False)

