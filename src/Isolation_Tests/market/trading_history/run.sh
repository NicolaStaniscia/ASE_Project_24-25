#!/usr/bin/bash

# Costruisce l'immagine Docker
docker build -t mocked_trading_history -f Dockerfile_test .

# Lancia il container
docker run \
  -p 5000:5000 \
  --name trading_history_testing \
  mocked_trading_history \
  -d
