docker stop $(docker container ls -q) # Stop all running containers
docker rm $(docker container ls -aq) # Remove all containers
docker rmi $(docker images -q) # Remove all docker images