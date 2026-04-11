FROM python:3.12-slim

# Install MariaDB C connector for the Python driver
RUN apt-get update && \
    apt-get install -y --no-install-recommends libmariadb-dev gcc && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install dependencies first (cache layer)
COPY pyproject.toml .
RUN pip install --no-cache-dir ".[mariadb,embeddings]"

# Copy source
COPY src/ src/
RUN pip install --no-cache-dir -e .

# Download embedding model at build time
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

ENTRYPOINT ["seamless-rag"]
CMD ["--help"]
