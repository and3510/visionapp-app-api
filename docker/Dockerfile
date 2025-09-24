# Etapa 1: Builder
FROM python:3.11 AS builder

WORKDIR /app
ENV DEBIAN_FRONTEND=noninteractive

# Dependências para compilar pacotes Python nativos
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    python3-dev \
    libboost-all-dev \
 && rm -rf /var/lib/apt/lists/*

# Copia requirements e instala deps em /install
COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install --prefix=/install --no-cache-dir -r requirements.txt


# Etapa 2: Runtime
FROM python:3.11-slim

WORKDIR /app
ENV DEBIAN_FRONTEND=noninteractive

# Apenas libs necessárias para rodar, não para compilar
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglx-mesa0 \
 && rm -rf /var/lib/apt/lists/*

# Copia pacotes Python já compilados do builder
COPY --from=builder /install /usr/local

# Copia o código da aplicação
COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
