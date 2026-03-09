#!/usr/bin/env bash
set -euo pipefail

python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m streamlit run app.py --server.headless true --server.address 0.0.0.0 --server.port 8501
