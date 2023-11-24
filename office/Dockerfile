FROM python:latest
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_CONFIGURATION=Prod
EXPOSE 8000
WORKDIR /app 
COPY requirements.txt /app
RUN pip3 install -r requirements.txt --no-cache-dir
COPY . /app 
RUN groupadd -r -g 1337 user && useradd -r -u 1337 -g user user
RUN chown -R user:user /app
USER user
CMD ["gunicorn", "-b", "0.0.0.0:5000", "office.wsgi"]
