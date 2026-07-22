FROM python:3.12-slim

RUN pip install --no-cache-dir uv

WORKDIR /code

COPY pyproject.toml ./
RUN uv sync --no-install-project

COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./alembic.ini
COPY scripts ./scripts

RUN uv sync

ENV PATH="/code/.venv/bin:$PATH"

EXPOSE 8000

CMD ["sh", "scripts/start.sh"]
