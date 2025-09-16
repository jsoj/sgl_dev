# Use Python 3.12 oficial
FROM python:3.12-slim

# Definir diretório de trabalho
WORKDIR /app

# Instalar dependências do sistema para PostgreSQL
RUN apt-get update && apt-get install -y \
    postgresql-client \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements e instalar dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código da aplicação
COPY . .

# Coletar arquivos estáticos
RUN python manage.py collectstatic --noinput --clear

# Criar usuário não-root
RUN useradd --create-home --shell /bin/bash app && chown -R app:app /app
USER app

# Expor porta
EXPOSE 8000

# Comando para iniciar aplicação
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "600", "SGL.wsgi:application"]