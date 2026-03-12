FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY engine.py main.py ./

# Required at runtime — pass via `docker run -e` or compose `environment:`
ENV OSH_ADDRESS=""
ENV OSH_USER=""
ENV OSH_PASS=""

EXPOSE 8080

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
