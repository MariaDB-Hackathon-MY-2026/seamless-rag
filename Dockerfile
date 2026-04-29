FROM python:3.12-slim

# MariaDB C connector for the Python driver
RUN apt-get update && \
    apt-get install -y --no-install-recommends libmariadb-dev gcc && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy the package metadata first so dependency-install layer can be cached.
# README.md is included because pyproject.toml's [project].readme references it.
COPY pyproject.toml README.md ./
COPY src/ src/

RUN pip install --no-cache-dir ".[mariadb,embeddings]"

# Pre-download embedding model so judges' first command isn't a 90 MB cold start.
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

ENTRYPOINT ["seamless-rag"]
CMD ["--help"]
