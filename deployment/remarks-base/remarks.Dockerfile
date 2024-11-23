FROM python:3.10-buster

RUN curl -sSL https://install.python-poetry.org | python3 -

RUN ["mkdir", "/app"]
WORKDIR /app

COPY . /app

RUN ["/root/.local/bin/poetry", "install"]
ENTRYPOINT ["/root/.local/bin/poetry", "run", "python", "-m", "remarks"]
