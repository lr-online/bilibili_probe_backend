# bv probe

## 启动数据库

```shell
docker run --name mongodb \
  -p 27017:27017 \
  -e MONGO_INITDB_ROOT_USERNAME=<username> \
  -e MONGO_INITDB_ROOT_PASSWORD=<password> \
  -d --restart=always mongo

```

docker run --name mongodb \
  -p 27017:27017 \
  -e MONGO_INITDB_ROOT_USERNAME=someone \
  -e MONGO_INITDB_ROOT_PASSWORD=someone \
  -d --restart=always mongo