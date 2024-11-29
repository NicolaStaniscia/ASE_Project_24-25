docker stop $(docker container ls -q)
docker rm $(docker container ls -aq)
docker rmi $(docker images -q)