FROM python:3

COPY main.py /app/

RUN pip3 install flask

EXPOSE 8080

ENTRYPOINT ["python3", "/app/main.py"]