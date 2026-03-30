FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY keys.py indexes.py init_schema.py graph_models.py ./
CMD ["python", "init_schema.py"]
