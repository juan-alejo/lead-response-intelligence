# ReachRate — production image for the operator dashboard.
#
# Build:  docker build -t reachrate .
# Run:    docker run -p 8501:8501 -v $(pwd)/config:/app/config \
#                                 -v $(pwd)/data:/app/data \
#                                 --env-file .env reachrate
#
# The image ships the full pipeline + Streamlit dashboard. Bring your own
# `.env` and `config/verticals.yaml` (bind-mount at runtime so settings
# persist across container restarts).

FROM python:3.11-slim

# System deps required by Playwright's bundled Chromium.
RUN apt-get update && apt-get install -y --no-install-recommends \
        libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libxkbcommon0 \
        libxcomposite1 libxdamage1 libxrandr2 libgbm1 libasound2 libpango-1.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Python deps first so the layer caches well across code-only changes.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Playwright browsers (Chromium only — adds ~300MB; skip if you only
# ever run in mock mode).
RUN playwright install --with-deps chromium

# Source code last.
COPY . .

EXPOSE 8501

# Streamlit listens on 0.0.0.0 so the container port is reachable.
CMD ["streamlit", "run", "src/dashboard/app.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--browser.gatherUsageStats=false"]
