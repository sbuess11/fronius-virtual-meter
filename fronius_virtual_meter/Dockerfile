ARG BUILD_FROM
FROM $BUILD_FROM

RUN apk add --no-cache python3 py3-pip
RUN pip3 install --no-cache-dir pyModbusTCP==0.3.0

WORKDIR /app

COPY app.py /app/app.py
COPY run.sh /app/run.sh

RUN chmod a+x /app/run.sh

CMD ["/app/run.sh"]
