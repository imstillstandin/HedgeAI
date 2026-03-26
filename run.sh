<<<<<<< HEAD
#!/usr/bin/env bash
set -euo pipefail

python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m streamlit run app.py --server.headless true --server.address 0.0.0.0 --server.port 8501
=======
#!/bin/bash

# Install dependencies
pip install -r requirements.txt

# Run the Streamlit app
streamlit run app.py
>>>>>>> 04854bc (Commit staged changes)
