FROM python:3.12-slim
WORKDIR /app
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*
COPY pyproject.toml .
RUN pip install --no-cache-dir -e . 2>/dev/null || pip install --no-cache-dir fastapi uvicorn[standard] websockets pydantic
COPY src/ src/
COPY run.py .
EXPOSE 8720
CMD ["python", "run.py"]
