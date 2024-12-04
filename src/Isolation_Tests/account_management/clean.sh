sudo docker stop $(sudo docker container ls -q) # Stop all running containers
sudo docker rm $(sudo docker container ls -aq) # Remove all containers
sudo docker rmi $(sudo docker images -q) # Remove all docker images