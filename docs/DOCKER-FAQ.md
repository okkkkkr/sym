# Docker FAQ

这份 FAQ 针对当前项目的 Docker 部署方式编写，适用于本地开发、测试环境和生产环境。

项目当前的 Docker 结构如下：

- `nginx`：对外提供官网、管理后台和 `/api/` 反向代理
- `api`：FastAPI 后端接口
- `worker`：Celery 异步任务消费者
- `beat`：Celery 定时任务调度器
- `postgres`：PostgreSQL 数据库
- `redis`：Redis 和 Celery Broker

## 先记住这一条

本项目执行 Docker Compose 命令时，统一推荐带上：

```bash
docker compose --env-file .env.docker ...
```

原因：

- `api`、`worker`、`beat` 容器会读取 `.env.docker`
- `postgres` 的库名、用户名、密码在 `compose.yaml` 里也依赖变量替换
- 不带 `--env-file .env.docker` 时，`postgres` 可能退回默认值，导致和应用配置不一致

## 1. 如何用 Docker 启动本项目？

首次启动或需要完整重建时执行：

```bash
docker compose --env-file .env.docker up -d --build
```

说明：

- 会构建并启动 `nginx`、`api`、`worker`、`beat`、`postgres`、`redis`
- 适合首次部署、本地第一次启动、或你不确定该重建哪些服务时使用

启动后检查状态：

```bash
docker compose --env-file .env.docker ps
```

补充：

- 这条命令默认只使用 [compose.yaml](/Users/kun/dida/sym/compose.yaml:1)，适合服务器部署
- 如果你在本地开发，需要使用 [compose.local.yaml](/Users/kun/dida/sym/compose.local.yaml:1) 做覆盖

本地 Docker 启动命令：

```bash
docker compose --env-file .env.docker -f compose.yaml -f compose.local.yaml up -d --build
```

本地覆盖当前会做两件事：

- 把 Nginx 端口改成 `6868:80`
- 把 Nginx 配置切到 [deploy/docker/nginx.conf](/Users/kun/dida/sym/deploy/docker/nginx.conf:1)，避免 `localhost` 跳转到线上域名

本地覆盖还会额外修正前端构建参数：

- 管理后台使用 `VITE_PUBLIC_PATH=/admin/`
- 管理后台 API 使用 `/api/v1`
- 官网 API 使用 `/api/v1`

## 2. 如何停掉本项目的 Docker？

停止并删除整个项目的容器网络：

```bash
docker compose --env-file .env.docker down
```

说明：

- 会停止并删除当前 Compose 项目的所有容器
- 不会删除 `postgres_data`、`redis_data`、`uploads_data`、`tmp_data` 这些数据卷

如果你只是想临时停服务，但不删容器，也可以执行：

```bash
docker compose --env-file .env.docker stop
```

## 3. 当我只改了前端文件时，怎么更新 Docker？

如果你改的是：

- `web/` 管理后台前端
- `official-web/` 官网前端
- 前端打包相关配置
- Nginx 静态资源或前端发布配置

执行：

```bash
docker compose --env-file .env.docker up -d --build nginx
```

说明：

- 当前项目的两个前端构建产物都被打进 `nginx` 镜像
- 只改前端时，通常只需要重建 `nginx`
- 不需要重建 `api`、`worker`、`beat`

## 4. 当我只改了后端文件时，怎么更新 Docker？

如果你改的是：

- `app/`
- `migrations/`
- `scripts/`
- `requirements.txt`
- `pyproject.toml`
- `run.py`

执行：

```bash
docker compose --env-file .env.docker up -d --build api worker beat
```

说明：

- `api`、`worker`、`beat` 共用同一个 Python 镜像
- 只改后端时，通常不需要重建 `nginx`
- 如果只是接口逻辑、任务逻辑、迁移脚本、Python 依赖变化，这条命令就够了

## 5. 当前后端文件都改了，怎么更新 Docker？

执行整套重建：

```bash
docker compose --env-file .env.docker up -d --build
```

说明：

- 会同时重建 `nginx` 和 `api/worker/beat`
- 适合同时改了前端和后端，或者你不想判断影响范围时使用

## 6. 如何重置数据？

这里的“重置数据”按“只清空数据库数据，不删除上传文件、不删除 Redis 卷”处理。

执行顺序：

### 第 1 步：停掉会写数据库的服务

```bash
docker compose --env-file .env.docker stop api worker beat
```

### 第 2 步：清空 PostgreSQL 的 `public` schema

```bash
docker compose --env-file .env.docker exec -T postgres psql -U sym -d sym -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
```

### 第 3 步：重新启动后端服务

```bash
docker compose --env-file .env.docker up -d api worker beat
```

说明：

- 当前项目启动 `api` 时会自动执行迁移和初始化逻辑
- 所以上面这套流程会让数据库重新建表，并重新生成项目默认初始化数据
- `nginx` 一般不需要重启

如果你也想顺手确认服务恢复正常：

```bash
docker compose --env-file .env.docker ps
```

风险提示：

- 这会清空数据库中的业务数据
- 不会删除 `uploads_data`
- 不会删除 `redis_data`
- 如果你要的是“彻底删掉全部持久化数据”，那不是这条 FAQ 的范围，应该走 `down -v`

## 7. 什么时候该用 `docker compose up -d --build`？

适合以下场景：

- 第一次启动项目
- 改了 `Dockerfile`
- 改了 Python 依赖，例如 `requirements.txt`
- 改了前端依赖或前端构建配置
- 同时改了前后端
- 你不确定哪些镜像需要重建

如果你明确知道只影响某几个服务，优先用更小范围的命令：

```bash
docker compose --env-file .env.docker up -d --build nginx
docker compose --env-file .env.docker up -d --build api worker beat
```

补充判断：

- 改 `web/` 或 `official-web/`：通常重建 `nginx`
- 改 `app/`、`migrations/`、`requirements.txt`：通常重建 `api worker beat`
- 改 `compose.yaml`：通常重新执行整套 `up -d --build`

## 8. 什么时候该用 `docker compose down`？

适合以下场景：

- 你要停掉整个项目
- 你要释放当前项目的容器和网络
- 你想用一套干净的容器重新 `up`

执行：

```bash
docker compose --env-file .env.docker down
```

如果你还要连数据卷一起删掉，才使用：

```bash
docker compose --env-file .env.docker down -v
```

说明：

- `down` 会停掉整个 Compose 项目
- `down -v` 会额外删除卷，包含数据库和 Redis 数据
- 生产环境一般不要随便执行 `down -v`

## 9. 什么时候该 `docker compose down xxx`？

结论：不要这样写，这个命令不对。

`docker compose down` 是针对整个 Compose 项目的，不支持只对单个服务写 `down xxx`。

如果你的目标是：

只停某个服务：

```bash
docker compose --env-file .env.docker stop nginx
docker compose --env-file .env.docker stop api
```

只重建某个服务：

```bash
docker compose --env-file .env.docker up -d --build nginx
docker compose --env-file .env.docker up -d --build api worker beat
```

只删除某个已经停止的容器：

```bash
docker compose --env-file .env.docker rm -f nginx
```

所以：

- 想停整个项目，用 `down`
- 想停单个服务，用 `stop`
- 想更新单个服务，用 `up -d --build <service>`
- 不要写 `docker compose down xxx`

## 10. 常用排查命令

查看整体状态：

```bash
docker compose --env-file .env.docker ps
```

看 Nginx 日志：

```bash
docker compose --env-file .env.docker logs -f nginx
```

看 API 日志：

```bash
docker compose --env-file .env.docker logs -f api
```

看 Worker 日志：

```bash
docker compose --env-file .env.docker logs -f worker
```

看 Beat 日志：

```bash
docker compose --env-file .env.docker logs -f beat
```
