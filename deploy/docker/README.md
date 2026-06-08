# SYM Docker 部署说明

这个目录存放的是 Docker / Docker Compose 部署所需的说明。

## 服务拆分

- `nginx`：对外提供官网、管理后台和 `/api/` 反代
- `api`：FastAPI 接口服务
- `worker`：Celery 异步任务消费者
- `beat`：Celery 定时任务调度器
- `postgres`：PostgreSQL 数据库
- `redis`：Redis 与 Celery Broker

## 首次部署

### 第 1 步：准备环境变量

```bash
cp .env.docker.example .env.docker
```

然后手动编辑 `.env.docker`，填入生产环境真实配置。

### 第 2 步：构建并启动全部服务

```bash
docker compose --env-file .env.docker up -d --build
```

### 第 3 步：查看服务状态

```bash
docker compose --env-file .env.docker ps
```

## 常用命令

查看日志：

```bash
docker compose --env-file .env.docker logs -f nginx
docker compose --env-file .env.docker logs -f api
docker compose --env-file .env.docker logs -f worker
docker compose --env-file .env.docker logs -f beat
```

重建并更新：

```bash
docker compose --env-file .env.docker up -d --build
```

停止服务：

```bash
docker compose --env-file .env.docker down
```

停止并删除数据卷：

```bash
docker compose --env-file .env.docker down -v
```

## 持久化数据

- `postgres_data`：PostgreSQL 数据
- `redis_data`：Redis 数据
- `uploads_data`：上传文件
- `tmp_data`：商品导入等临时文件

`api`、`worker`、`beat` 共用 `uploads_data` 和 `tmp_data`，这样异步任务才能访问接口服务写入的文件。

## 验证方式

- `docker compose --env-file .env.docker ps`
- `docker compose --env-file .env.docker logs -f api`
- `docker compose --env-file .env.docker logs -f worker`
- `docker compose --env-file .env.docker logs -f beat`
- 打开 `/` 和 `/admin/`
- 访问 `/api/v1/*` 接口
