docker build -t mocked_roll -f Dockerfile_test .
docker run -p 5000:5000 --name roll_gacha_testing mocked_roll -d