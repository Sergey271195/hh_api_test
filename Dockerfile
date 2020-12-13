FROM python:3.8-alpine as builder

WORKDIR /usr/src/test

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apk update && apk add git

RUN git clone https://github.com/Sergey271195/hh_api_test.git .

RUN pip wheel --no-cache-dir --no-deps --wheel-dir /usr/src/test/wheels -r requirements.txt

FROM python:3.8-alpine

COPY --from=builder /usr/src/test/wheels /wheels
COPY --from=builder /usr/src/test/test.py /src/
RUN pip install --no-cache /wheels/*

CMD ["python", "src/test.py"]
