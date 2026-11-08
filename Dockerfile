FROM python:3.11

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY src ./src

EXPOSE 8000

CMD ["uvicorn", "--factory", "src.main:get_app", "--host", "0.0.0.0", "--port", "8000"]