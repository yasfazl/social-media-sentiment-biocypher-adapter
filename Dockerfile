FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/src

COPY pyproject.toml README.md ./
COPY src ./src

RUN python -m pip install --no-cache-dir -e .

COPY config ./config
COPY create_knowledge_graph.py ./

CMD ["python", "create_knowledge_graph.py"]