# 本地 Docker 对齐服务器配置与 Cloudflare R2 工作流

## 目的

本文记录一种用于准备服务器初始化数据的本地运行模式：

- 项目完整运行在本地 Docker Compose 中
- PostgreSQL、Redis 和 Celery 使用本地容器
- 业务配置以服务器配置为基线
- 图片、视频、Logo、二维码和首页装修图片直接上传到服务器共用的 Cloudflare R2 bucket
- 本地业务数据准备完成后，再单独执行 PostgreSQL 覆盖式迁移

该模式解决数据库迁移后媒体路径不可用的问题。数据库中保存的是 R2 对象 key，服务器导入数据库后可直接通过同一个 R2 公开域名访问媒体，不需要再同步 `uploads_data`。

## 配置关系

| 文件 | 职责 | 是否提交 |
| --- | --- | --- |
| `.env.server-docker` | 服务器业务配置、上传配置和 R2 配置基线 | 否 |
| `.env.docker` | 本地 PostgreSQL、Redis、Celery 和本地 `SECRET_KEY` | 否 |
| `.env.local-docker` | 脚本生成的本地 Docker 最终运行配置 | 否 |

生成脚本为 `scripts/build_local_docker_env.py`，输出文件由 `.gitignore` 中的 `.env.*` 规则保护。

### 合并规则

生成时先完整读取 `.env.server-docker`，再应用以下覆盖：

- `POSTGRES_HOST`
- `POSTGRES_PORT`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `POSTGRES_DB`
- `REDIS_URL`
- `CELERY_BROKER_URL`
- `CELERY_RESULT_BACKEND`
- `SECRET_KEY`

以上变量来自 `.env.docker`。这样既能保持服务器业务行为，又不会让本地容器连接服务器数据库或因 PostgreSQL 密码变化而无法访问已有本地数据卷。

脚本还会强制设置：

```env
APP_ENV=development
MEDIA_ORPHAN_CLEANUP_ENABLED=false
MEDIA_ORPHAN_CLEANUP_DRY_RUN=true
```

`APP_ENV=development` 保留本地调试和批量导入能力。关闭孤儿媒体清理是为了避免本地数据库引用集合不完整时删除生产 R2 中仅被服务器数据库引用的对象。

### 生成前校验

脚本要求服务器配置显式设置 `STORAGE_DRIVER=r2`，并检查以下变量非空：

- `R2_ENDPOINT_URL`
- `R2_BUCKET`
- `R2_ACCESS_KEY`
- `R2_SECRET_KEY`
- `R2_PUBLIC_BASE_URL`

本地基础设施变量或 R2 必填项缺失时，脚本会失败且不会覆盖已有 `.env.local-docker`。错误消息只显示缺失的变量名，不显示值。

## 首次启用

在项目根目录确认 `.env.server-docker` 和 `.env.docker` 已准备完成，然后执行：

```bash
python3 scripts/build_local_docker_env.py
docker compose --env-file .env.local-docker -f compose.yaml -f compose.local.yaml config --quiet
docker compose --env-file .env.local-docker -f compose.yaml -f compose.local.yaml up -d --build
```

`compose.local.yaml` 会让 `api`、`worker` 和 `beat` 统一加载 `.env.local-docker`，同时保持本地 Nginx 使用 `6868:80` 和本地 `/api/v1` 反向代理。

禁止执行 `docker compose down -v`。该命令会删除 PostgreSQL、Redis、上传目录和临时目录的数据卷。

## 日常使用

服务器配置更新后，重新生成并创建应用容器：

```bash
python3 scripts/build_local_docker_env.py
docker compose --env-file .env.local-docker -f compose.yaml -f compose.local.yaml up -d --force-recreate api worker beat
```

代码或前端发生变化时重新构建完整服务：

```bash
python3 scripts/build_local_docker_env.py
docker compose --env-file .env.local-docker -f compose.yaml -f compose.local.yaml up -d --build
```

查看状态与日志：

```bash
docker compose --env-file .env.local-docker -f compose.yaml -f compose.local.yaml ps
docker compose --env-file .env.local-docker -f compose.yaml -f compose.local.yaml logs -f api worker beat nginx
```

本地访问地址：

- 官网：`http://localhost:6868/`
- 管理后台：`http://localhost:6868/admin/`

## 验证清单

### 容器配置

检查非敏感运行状态：

```bash
for service in api worker beat; do
  docker compose --env-file .env.local-docker -f compose.yaml -f compose.local.yaml exec -T "$service" \
    sh -lc 'printf "app_env=%s driver=%s cleanup=%s db_host=%s\n" \
    "$APP_ENV" "$STORAGE_DRIVER" "$MEDIA_ORPHAN_CLEANUP_ENABLED" "$POSTGRES_HOST"'
done
```

预期结果：

- `app_env=development`
- `driver=r2`
- `cleanup=false`
- `db_host=postgres`

### 上传链路

1. 登录本地管理后台。
2. 上传一张专用测试图片。
3. 确认接口返回 `storageDriver=r2`。
4. 确认返回 URL 使用 `R2_PUBLIC_BASE_URL` 配置的域名。
5. 刷新页面并确认浏览器可以继续访问图片。
6. 仅删除本次创建的测试资源。

部分 Cloudflare 安全规则可能对没有浏览器 `User-Agent` 的脚本请求返回 `403`，但浏览器访问正常。验证页面资源时应以真实浏览器结果为准；如果后端需要主动下载公开 URL，则需另外检查 Cloudflare WAF 或 Bot规则。

## 与数据库同步的关系

本工作流只负责准备本地运行环境和将新媒体写入 R2，不会自动同步数据库。

数据库迁移必须单独按照[服务器数据库初始化迁移手册](服务器数据库初始化迁移手册.md)执行。该流程会用本地数据库覆盖服务器目标库，不是增量同步，执行前必须：

1. 确认本地数据是最终初始化基线。
2. 确认本地和服务器代码版本一致。
3. 备份服务器当前数据库。
4. 停止服务器 API、worker 和 beat。
5. 获得明确的服务器数据覆盖授权。

只要数据库中的媒体字段保存的是当前 R2 对象 key，数据库导入服务器后通常不需要同步 `uploads_data`。历史 `/uploads/...` 记录仍依赖原本的本地文件，不会因为切换 R2 自动迁移。

## 风险与边界

- 本地与服务器共用同一个 R2 bucket，本地上传会立即写入生产媒体空间。
- 手动删除媒体会删除共用 bucket 中的对象，可能同时影响服务器页面。
- 禁用孤儿媒体定时清理不能阻止管理操作触发的单项删除。
- `.env.server-docker`、`.env.docker` 和 `.env.local-docker` 均包含敏感配置，禁止提交、复制到文档或输出到日志。
- 不要用整份服务器配置直接替换本地配置，否则可能连接生产数据库、Redis 或其他外部服务。
- 本模式不是双向同步机制；服务器产生的新数据库记录不会自动回到本地。

## 常见问题

### 容器仍显示 `driver=local`

通常是没有重新生成配置或应用容器仍使用旧环境。重新执行：

```bash
python3 scripts/build_local_docker_env.py
docker compose --env-file .env.local-docker -f compose.yaml -f compose.local.yaml up -d --force-recreate api worker beat
```

### PostgreSQL 认证失败

检查 `.env.docker` 中的 `POSTGRES_*` 是否仍与本地已有 `postgres_data` 对应。不要用服务器数据库密码覆盖本地密码；PostgreSQL 已有数据卷不会因修改容器环境变量自动修改数据库用户密码。

### 上传成功但图片无法访问

依次确认：

1. `R2_PUBLIC_BASE_URL` 已绑定到正确的 R2 bucket。
2. 接口返回的对象 key 与 R2 中对象一致。
3. 浏览器访问状态和 Cloudflare WAF/Bot规则。
4. 数据库保存的是对象 key，而不是错误的本地 `/uploads/...` 地址。

### 恢复为纯本地存储

先确认 `.env.docker` 使用 `STORAGE_PROVIDER=local` 或 `STORAGE_DRIVER=local`，然后生成本地覆盖文件并重新创建应用容器：

```bash
cp .env.docker .env.local-docker
docker compose --env-file .env.local-docker -f compose.yaml -f compose.local.yaml up -d --force-recreate api worker beat
```

该操作只改变后续上传位置，不会自动把 R2 历史对象下载到 `uploads_data`，也不会改写数据库中已有媒体 key。

## 本次改造记录

- 日期：2026-08-22
- 新增 `scripts/build_local_docker_env.py`，安全生成 `.env.local-docker`
- `compose.local.yaml` 改为让 API、worker、beat 使用生成配置
- 本地运行环境强制为 development，并禁用孤儿媒体清理
- 已验证本地 PostgreSQL 保持不变，真实 HTTP 图片上传进入 Cloudflare R2，公开 URL 可访问，测试对象可删除
