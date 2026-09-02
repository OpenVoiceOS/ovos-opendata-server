FROM python:3.11.9-slim
WORKDIR /app
COPY pyproject.toml .
RUN pip install --no-cache-dir .
COPY app/ ./app/
COPY alembic.ini .
COPY migrations/ ./migrations/
COPY scripts/entrypoint.sh ./scripts/entrypoint.sh
RUN chmod +x ./scripts/entrypoint.sh
EXPOSE 8000
CMD ["./scripts/entrypoint.sh"]
