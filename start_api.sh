#!/bin/bash
cd /home/guard/Documents/perkuliahan/sem\ 7/Cap/backend
PYTHONPATH=. .venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000