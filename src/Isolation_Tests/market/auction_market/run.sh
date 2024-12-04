#!/usr/bin/bash
docker build -t mocked_auction_market -f Dockerfile_test .
docker run -p 5000:5000 --name auction_market_testing mocked_auction_market
