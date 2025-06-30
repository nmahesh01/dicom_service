FROM python:3.12-slim

WORKDIR /app
# Install Poetry
RUN pip install --upgrade pip && pip install poetry

# Copy the rest of the code
COPY . /app/

# Install dependencies using Poetry
RUN poetry install

EXPOSE 50051

#ENTRYPOINT ["/bin/bash"]

CMD ["poetry", "run", "python3", "grpc_backend/server.py"]