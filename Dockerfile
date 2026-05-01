# Reviewer path: pin a specific Python patch release for a stable tested build path.
# Digest pinning can be added for archival reproduction, but this Dockerfile is a
# tested execution path rather than a guarantee of immutable upstream package state.
FROM python:3.12.11-slim-bookworm

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends bash coreutils git \
    && rm -rf /var/lib/apt/lists/*

COPY . /app

RUN pip install --no-cache-dir --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -r requirements-review.txt \
    && pip install --no-cache-dir -e .

CMD ["bash", "scripts/verify_reproducibility.sh"]
