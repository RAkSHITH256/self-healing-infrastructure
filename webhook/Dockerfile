FROM python:3.12-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends docker.io && \
    rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir --default-timeout=300 --retries=10 ansible-core
RUN ansible-galaxy collection install community.docker
WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir --default-timeout=300 --retries=10 -r requirements.txt

CMD ["python", "app.py"]
