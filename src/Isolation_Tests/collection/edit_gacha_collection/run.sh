docker build -t mocked_edit_gacha -f Dockerfile_test . && \
docker run -p 5000:5000 --name edit_gacha_testing -d mocked_edit_gacha