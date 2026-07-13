FROM python:3.12-slim

RUN pip install --no-cache-dir uv

WORKDIR /code

COPY pyproject.toml ./
RUN uv sync --no-install-project

COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./alembic.ini

RUN uv sync

ENV PATH="/code/.venv/bin:$PATH"

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]