FROM python:3.12-slim@sha256:804ddf3251a60bbf9c92e73b7566c40428d54d0e79d3428194edf40da6521286

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends bash coreutils git \
    && rm -rf /var/lib/apt/lists/*

COPY . /app

RUN pip install --no-cache-dir --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -r requirements-review.txt \
    && pip install --no-cache-dir -e .

CMD ["bash", "scripts/verify_reproducibility.sh"]
