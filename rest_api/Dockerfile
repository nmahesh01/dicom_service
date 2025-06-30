FROM python:3.12-slim

WORKDIR /app
# Install Poetry
RUN pip install --upgrade pip && pip install poetry

# Copy the rest of the code
COPY . /app/

# Install dependencies using Poetry
RUN poetry install

EXPOSE 8000

#ENTRYPOINT ["/bin/bash"]

CMD ["poetry", "run", "python3", "rest_api/app.py"]