sudo docker build -t mocked_account_management -f Dockerfile_test . && \
sudo docker run -p 5000:5000 --name account_management_testing mocked_account_management -d 