FROM python:slim

RUN useradd forum

WORKDIR /home/forum

COPY requirements.txt requirements.txt
RUN python -m venv venv
RUN venv/bin/pip install -r requirements.txt
RUN venv/bin/pip install gunicorn pymysql cryptography

COPY app app
COPY migrations migrations
COPY forum.py config.py boot.sh ./
RUN chmod a+x boot.sh

ENV FLASK_APP forum.py

RUN chown -R forum:forum ./
USER forum

EXPOSE 5000
ENTRYPOINT ["./boot.sh"]
