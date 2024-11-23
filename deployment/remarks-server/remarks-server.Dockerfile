FROM laauurraaa/remarks-bin:0.3.16

COPY server.py /app/server.py
RUN ["/root/.local/bin/poetry", "run", "pip", "install", "flask"]

ENTRYPOINT ["/root/.local/bin/poetry", "run", "python", "/app/server.py"]
