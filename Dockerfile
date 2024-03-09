FROM python:3

# RUN mkdir /app
WORKDIR /app

# RUN python -m pip install -U wheel setuptools

COPY requirements.txt /app

RUN pip install -r requirements.txt

COPY . /app

CMD ["python", "app.py"]