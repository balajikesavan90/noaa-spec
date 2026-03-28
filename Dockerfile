FROM python:3.12-slim

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends bash coreutils git \
    && rm -rf /var/lib/apt/lists/*

COPY . /app

RUN pip install --no-cache-dir -r requirements-review.txt \
    && pip install --no-cache-dir -e .

CMD ["bash", "-lc", "python reproducibility/run_pipeline_example.py --example minimal --out /tmp/noaa-spec-sample.csv && bash scripts/verify_reproducibility.sh && pytest -q"]
