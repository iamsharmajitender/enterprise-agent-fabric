FROM python:3.12-slim AS test
WORKDIR /app
COPY requirements.txt requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements-dev.txt
COPY server.py telemetry.py tools.json pytest.ini ./
COPY tests tests
ENV PYTHONPATH=/app
RUN pytest

FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY server.py telemetry.py tools.json ./
ENV TOOLS_JSON=/app/tools.json PYTHONUNBUFFERED=1
EXPOSE 3010
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "3010"]
