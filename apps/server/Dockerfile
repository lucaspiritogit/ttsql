FROM python:3.12-slim

WORKDIR /repo

COPY pyproject.toml uv.lock* ./
COPY apps/server ./apps/server

RUN pip install uv
RUN uv pip install --system ./apps/server

CMD ["uvicorn", "apps.server.main:app", "--host", "0.0.0.0", "--port", "8000"]