FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN pip install --no-cache-dir pyyaml structlog

COPY src/ ./src/
COPY run.py report.html ./

RUN mkdir -p logs reports config

ENTRYPOINT ["python","run.py"]
CMD ["--config","config/config.yaml"]
