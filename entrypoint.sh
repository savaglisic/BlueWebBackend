#!/bin/bash
set -e  # Exit on error

# Run DB initialization script
python init_db.py

# Now launch gunicorn
exec gunicorn app:app --bind 0.0.0.0:5001
