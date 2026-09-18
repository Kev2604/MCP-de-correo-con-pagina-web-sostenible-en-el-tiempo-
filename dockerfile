FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && adduser --disabled-password --gecos "" app

COPY requirements.txt ./
RUN python -m pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY . .
RUN chown -R app:app /app

USER app

HEALTHCHECK CMD python -c "import sys; sys.exit(0)"

CMD ["python", "-m", "servidor_correo"]
