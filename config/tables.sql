-- Banco de Dados SSP-USUARIO


-- Tabela: Log_resultado_reconhecimento

CREATE TABLE log_resultado_reconhecimento (
    id_resultado_reconhecimento VARCHAR(30) PRIMARY KEY DEFAULT gen_random_uuid(),
    matricula VARCHAR(10) REFERENCES usuario(matricula),
    distancia VARCHAR(45) NOT NULL,
    id_usuario VARCHAR(100),
    cpf VARCHAR(14),
    id_ficha VARCHAR(30),
    status_reconhecimento(VARCHAR(90), NOT NULL),
    data_ocorrido TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    -- url_facial_referencia VARCHAR(200)
);

-- Tabela: Log_resultado_cpf

CREATE TABLE log_resultado_cpf (
    id_resultado_cpf VARCHAR(30) PRIMARY KEY DEFAULT gen_random_uuid(),
    matricula VARCHAR(10) REFERENCES usuario(matricula),
    id_usuario VARCHAR(100),
    cpf VARCHAR(14),
    id_ficha VARCHAR(30),
    data_ocorrido TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
);





-- Banco de Dados SSP-CRIMINOSOS


-- Tabela: identidade

CREATE EXTENSION vector;


CREATE TABLE identidade (
    cpf VARCHAR(14) PRIMARY KEY,
    nome VARCHAR(150) NOT NULL,
    nome_mae VARCHAR(150) NOT NULL,
    nome_pai VARCHAR(150) NOT NULL,
    data_nascimento VARCHAR(20) NOT NULL,
    vetor_facial VECTOR(128) NOT NULL,
    -- url_facial VARCHAR(200) NOT NULL,
    gemeo = Column(Boolean, nullable=False, default=False)


);


-- Tabela: ficha_criminal
CREATE TABLE ficha_criminal (
    id_ficha VARCHAR(30) PRIMARY KEY DEFAULT gen_random_uuid(),
    cpf VARCHAR(14) REFERENCES identidade(cpf),
    vulgo VARCHAR(100)
);

-- Tabela: crime
CREATE TABLE crime (
    id_crime VARCHAR(30) PRIMARY KEY DEFAULT gen_random_uuid(),
    id_ficha VARCHAR REFERENCES ficha_criminal(id_ficha),
    nome_crime VARCHAR(150),
    artigo VARCHAR(50),
    descricao TEXT,
    data_ocorrencia VARCHAR(20),
    cidade VARCHAR(100),
    estado CHAR(2),
    status VARCHAR(20) CHECK (status IN ('Em Aberto', 'Foragido'))
);
