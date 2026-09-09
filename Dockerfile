# Edusphere - one image serving both the API and the built frontend.
#
# WHY ONE IMAGE AND NOT TWO
# Two containers means two services to deploy, a network between them, and CORS
# to configure. Serving the built frontend from FastAPI means one thing to
# deploy, one URL, and no cross-origin requests at all - which is what free
# hosting tiers are built for.
#
# Build:  docker build -t edusphere .
# Run:    docker run -p 5001:5001 --env-file Edusphere_backend/.env edusphere

# ---------------------------------------------------------------------------
# Stage 1 - build the frontend.
# Node is only needed to produce dist/. Doing it in a separate stage keeps the
# whole Node toolchain (~400 MB) out of the image that actually ships.
# ---------------------------------------------------------------------------
FROM node:20-slim AS frontend

WORKDIR /build

# Copy manifests first. Docker caches each step, and this one only re-runs when
# dependencies change - so editing a component does not reinstall node_modules.
COPY Edusphere_frontend/package*.json ./
RUN npm ci --no-audit --no-fund

COPY Edusphere_frontend/ ./
RUN npm run build


# ---------------------------------------------------------------------------
# Stage 2 - the runtime image.
# ---------------------------------------------------------------------------
# Python 3.11, not 3.10.
#
# Current litellm imports NotRequired from typing, which only exists from 3.11.
# On 3.10 the container died at startup with:
#   ImportError: cannot import name 'NotRequired' from 'typing'
# Nothing here needs 3.10, and everything else supports 3.11.
FROM python:3.11-slim

# PYTHONUNBUFFERED: send logs straight out instead of buffering them, so a
#   crash loop on a host actually shows you why.
# HF_HOME: where sentence-transformers caches its model. Set explicitly so the
#   model baked in below is the one found at runtime.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    HF_HOME=/opt/hf \
    PORT=5001

WORKDIR /app

# curl is for the healthcheck; build-essential is dropped again below because
# some wheels need a compiler to install but nothing needs one to run.
RUN apt-get update \
 && apt-get install -y --no-install-recommends curl build-essential \
 && rm -rf /var/lib/apt/lists/*

# CPU-only torch, installed first and on its own.
#
# The default torch wheel bundles CUDA and is roughly 2 GB. Nothing here uses a
# GPU - the embedding model runs fine on a CPU - so the CPU build cuts the image
# by well over a gigabyte, which matters on a free tier with a size cap.
#
# BOTH index URLs are needed. --index-url REPLACES PyPI rather than adding to
# it, so with only the PyTorch index pip cannot find torch's own build
# dependencies (flit_core, typing_extensions) and fails trying to build them
# from source. Listing the PyTorch index first keeps torch CPU-only; the
# --extra-index-url leaves PyPI available for everything else.
RUN pip install --no-cache-dir \
      --index-url https://download.pytorch.org/whl/cpu \
      --extra-index-url https://pypi.org/simple \
      torch

COPY Edusphere_backend/requirements_simple.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Bake the embedding model into the image.
#
# Without this the first request downloads ~90 MB, so the first visitor waits,
# and a host with no writable cache or no outbound access fails outright.
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# The compiler is no longer needed now that everything is installed.
RUN apt-get purge -y build-essential && apt-get autoremove -y

COPY Edusphere_backend/ ./

# The built frontend lands where app.py looks for it.
COPY --from=frontend /build/dist ./static

# Runtime data (users, conversations, feedback) lives here. Mount a volume over
# it to keep data across restarts - without one, a redeploy starts empty.
RUN mkdir -p /app/data

EXPOSE 5001

HEALTHCHECK --interval=30s --timeout=10s --start-period=90s --retries=3 \
  CMD curl -fsS http://localhost:${PORT}/ || exit 1

CMD ["sh", "-c", "uvicorn app:app --host 0.0.0.0 --port ${PORT}"]
