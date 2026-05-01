FROM python:3.12-slim

WORKDIR /repo

COPY pyproject.toml uv.lock* ./
COPY apps/client ./apps/client

RUN pip install uv
RUN uv pip install --system ./apps/client

CMD ["python", "-m", "apps.client.main"]