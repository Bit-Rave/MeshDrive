FROM python:3.11-slim

WORKDIR /app
COPY . .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir --prefix=/install -r requirements.txt \

RUN addgroup -S app && adduser -S app -G app
USER app

WORKDIR /app

EXPOSE 8000

CMD ["python3", "main.py"]