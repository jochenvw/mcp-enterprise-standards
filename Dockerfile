FROM python:3.12-slim
WORKDIR /app
RUN pip install uv
COPY pyproject.toml .
COPY src/ ./src/
COPY .env .
RUN uv pip install . --system
ENV PYTHONUNBUFFERED=1
CMD ["python", "src/server.py"]