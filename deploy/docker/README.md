# SYM Docker 部署说明

这个目录存放的是 Docker / Docker Compose 部署所需的说明。

本地使用服务器业务配置并共用 Cloudflare R2 的完整流程，参见[本地 Docker 对齐服务器配置与 Cloudflare R2 工作流](../../docs/本地Docker对齐服务器配置与R2工作流.md)。

## 配置文件说明

- [compose.yaml](../../compose.yaml)：基础 Compose 配置，默认面向服务器部署。
- [compose.local.yaml](../../compose.local.yaml)：本地 Docker 覆盖配置，必须和基础配置一起使用，不单独执行。
- `compose.local.yaml` 当前覆盖了本地开发需要的关键行为：
  - API、worker、beat 统一加载本地生成的 `.env.local-docker`
  - Nginx 对外端口改为 `6868:80`
  - Nginx 使用 [nginx.conf](nginx.conf)，避免 `localhost` 被重定向到生产域名
  - 管理后台构建时使用 `VITE_PUBLIC_PATH=/admin/`，避免 `/admin/` 页面错误加载官网 `/assets/*`
  - 两个前端构建时都改为调用本地反代的 `/api/v1`

## 服务拆分

- `nginx`：对外提供官网、管理后台和 `/api/` 反代
- `api`：FastAPI 接口服务
- `worker`：Celery 异步任务消费者
- `beat`：Celery 定时任务调度器
- `api` / `worker` / `beat` 共用同一套 Python 运行镜像，当前包含 `ffmpeg`，供视频异步压缩使用
- `postgres`：PostgreSQL 数据库
- `redis`：Redis 与 Celery Broker

## 首次部署

### 第 1 步：准备环境变量

```bash
cp .env.docker.example .env.docker
```

然后手动编辑 `.env.docker`，填入生产环境真实配置。

生产环境必须显式配置：

```env
APP_ENV=production
```

该配置会隐藏管理后台“批量中心”，并使好物批量导入相关接口返回 `404`。

如果静态上传资源使用 Cloudflare R2，至少配置：

```env
STORAGE_DRIVER=r2
R2_ENDPOINT_URL=https://<account-id>.r2.cloudflarestorage.com
R2_BUCKET=<bucket>
R2_REGION=auto
R2_ACCESS_KEY=<access-key-id>
R2_SECRET_KEY=<secret-access-key>
R2_PUBLIC_BASE_URL=https://<public-domain>
R2_FORCE_PATH_STYLE=true
```

`R2_PUBLIC_BASE_URL` 应使用绑定到 R2 bucket 的公开访问域名。密钥只写入 `.env.docker`，不要提交到仓库。

### 本地 Docker 对齐服务器业务配置

需要在本地使用服务器业务配置和同一个 Cloudflare R2 bucket 时，保留以下两个源文件：

- `.env.server-docker`：服务器业务、上传和 R2 配置基线
- `.env.docker`：本地 PostgreSQL、Redis、Celery 和本地 `SECRET_KEY`

生成本地 Docker 最终配置：

```bash
python3 scripts/build_local_docker_env.py
```

脚本输出 `.env.local-docker`，该文件不会提交到 Git。生成规则如下：

- 业务和 R2 配置来自 `.env.server-docker`
- `POSTGRES_*`、`REDIS_URL`、`CELERY_*` 和 `SECRET_KEY` 来自 `.env.docker`
- 本地强制设置 `APP_ENV=development`，避免继承服务器配置后被判定为生产环境
- 本地强制设置 `MEDIA_ORPHAN_CLEANUP_ENABLED=false`，防止本地数据库视角不完整时误删生产 R2 对象
- 本地不继承 `PRODUCT_IMPORT_MAX_FILE_SIZE`，使用应用默认的 10 GiB 批量导入上限

本地构建启动：

```bash
docker compose --env-file .env.local-docker -f compose.yaml -f compose.local.yaml up -d --build
```

本地会直接向服务器使用的 R2 bucket 写入媒体。手动删除媒体仍可能删除共用 bucket 中的对象；数据库同步到服务器必须另行按《服务器数据库初始化迁移手册》执行。

### 第 2 步：构建并启动全部服务

`api`、`worker`、`beat` 使用固定的非 root 用户 `10001:10001`。首次从旧版本升级时，先迁移现有共享卷属主：

```bash
docker compose --env-file .env.docker run --rm --user root --no-deps \
  --entrypoint sh api -c 'chown -R 10001:10001 /opt/sym/uploads /opt/sym/tmp'
```

该命令只修改文件属主，不删除卷内数据。新建数据卷无需执行。

```bash
docker compose --env-file .env.docker up -d --build
```

上面这条命令默认使用基础配置，适合服务器部署。

本地开发如果需要保留生产向 `compose.yaml`，并把 Nginx 入口改为 `6868`，使用叠加配置：

```bash
python3 scripts/build_local_docker_env.py
docker compose --env-file .env.local-docker -f compose.yaml -f compose.local.yaml up -d --build
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

服务器部署继续使用基础配置：

```bash
docker compose --env-file .env.docker -f compose.yaml up -d --build
```

本地叠加配置重建：

```bash
python3 scripts/build_local_docker_env.py
docker compose --env-file .env.local-docker -f compose.yaml -f compose.local.yaml up -d --build
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
- `uploads_data`：本地上传文件；使用 `STORAGE_DRIVER=r2` 后，新媒体和导入错误报告会写入 R2，通常只保留为空卷或历史兼容目录
- `tmp_data`：商品导入等临时文件

`api`、`worker`、`beat` 共用 `uploads_data` 和 `tmp_data`。R2 模式下仍保留 `uploads_data` 挂载，避免 Nginx `/uploads/` 配置和历史路径突然断裂。

### 清理本地历史上传文件

切到 R2 并确认不再需要历史 `/uploads/...` 文件后，可以只清空 `uploads_data`，不要使用 `down -v`，否则会同时删除数据库和 Redis 卷。

```bash
docker compose --env-file .env.docker stop api worker beat nginx
docker compose --env-file .env.docker run --rm --no-deps --entrypoint sh api -lc 'find /opt/sym/uploads -mindepth 1 -exec rm -rf {} +'
docker compose --env-file .env.docker up -d api worker beat nginx
```

执行前需要确认数据库中旧的本地图片、视频、Logo、二维码和首页装修图记录已经可以废弃；清空后这些旧 `/uploads/...` URL 会返回 404。

## 验证方式

- `docker compose --env-file .env.docker ps`
- `docker compose --env-file .env.local-docker -f compose.yaml -f compose.local.yaml ps`
- `docker compose --env-file .env.docker logs -f api`
- `docker compose --env-file .env.docker logs -f worker`
- `docker compose --env-file .env.docker logs -f beat`
- 打开 `/` 和 `/admin/`
- 访问 `/api/v1/*` 接口
