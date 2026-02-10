# stage 1: base build stage
FROM python:3.14-slim AS builder

RUN mkdir /app

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN pip install --upgrade pip

COPY requirements.txt /app/

RUN pip install --no-cache-dir -r requirements.txt

# stage: final stage
FROM python:3.14-slim

RUN mkdir /app

COPY --from=builder /usr/local/lib/python3.14/site-packages/ /usr/local/lib/python3.14/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/

RUN playwright install --with-deps

WORKDIR /app

COPY . .

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

EXPOSE 8200

CMD ["uvicorn", "main:bus_app", "--host", "0.0.0.0", "--port", "8200"]
