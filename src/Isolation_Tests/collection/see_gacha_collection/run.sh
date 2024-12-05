docker build -t mocked_see_gacha -f Dockerfile_test .
docker run -p 5000:5000 --name see_gacha_testing -d mocked_see_gacha