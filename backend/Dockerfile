FROM python:3.13-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn==23.0.0
COPY . .
EXPOSE 5000
CMD ["sh", "-c", "flask --app run.py db upgrade && gunicorn --bind 0.0.0.0:5000 run:app"]

