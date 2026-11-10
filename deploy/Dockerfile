# Social Manager na serveri (nie na Macu). Dáta sú v zväzku /data, kľúče len v súbore server.env (nie v repozitári).
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
 && python -m playwright install --with-deps chromium
COPY app ./app
COPY static ./static
COPY VERSION ./
ENV SM_DATA_DIR=/data \
    SM_HOST=0.0.0.0 \
    SM_NO_BROWSER=1 \
    SM_SKIP_UPDATE=1 \
    SM_DRY_RUN=1 \
    SM_AI_BACKEND=api \
    PYTHONUNBUFFERED=1
VOLUME ["/data"]
EXPOSE 8765
CMD ["python", "-m", "app.main"]
