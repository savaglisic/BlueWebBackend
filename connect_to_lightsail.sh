#!/bin/bash

# Define variables
PEM_FILE="$HOME/.ssh/lightsail_key.pem"
REMOTE_USER="ubuntu"  # Change if your server uses a different user
REMOTE_HOST="3.220.211.56"

# Connect to the server
ssh -i "$PEM_FILE" "$REMOTE_USER@$REMOTE_HOST"
