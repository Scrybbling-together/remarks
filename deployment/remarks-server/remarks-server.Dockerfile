FROM laauurraaa/remarks-bin:latest

COPY remarks_server/server.py /app/server.py
RUN ["/root/.local/bin/poetry", "run", "pip", "install", "flask"]

ENTRYPOINT ["/root/.local/bin/poetry", "run", "python", "/app/server.py"]
