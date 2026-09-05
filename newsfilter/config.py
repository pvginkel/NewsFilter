import os

# The defaults are what a checkout looks like: `data/` is in the repo and
# `store/` is gitignored beside it. The container image sets DATA_PATH to
# /app/data and has WORKDIR /app, so the STORE_PATH default lands on
# /app/store there — the deployment overrides it to point at its volume.
DATA_PATH = os.getenv("DATA_PATH", "data")
STORE_PATH = os.getenv("STORE_PATH", "store")
