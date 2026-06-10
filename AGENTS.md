# AGENTS.md

## 适用范围

- 本文件适用于仓库根目录及全部子目录。
- 当前不设置子目录级 `AGENTS.md`；三个子系统规模尚可由本文件统一导航。
- 若后续 `web/`、`official-web/` 或 `app/` 出现独立团队、独立发布流程或大量专属规则，再新增局部文件。
- 执行任务前先阅读与任务相关的代码、配置和文档，不凭目录名推断行为。
- 只修改完成任务所必需的文件，保留用户已有改动和未跟踪文件。

## 项目概览

- 项目名为 `SYM Admin`，后端包名为 `sym-admin`。
- 仓库同时包含后台 API、管理后台、公开官网、异步任务和部署配置。
- 后端入口为 `run.py`，应用对象为 `app:app`。
- 管理后台位于 `web/`，生产路径为 `/admin/`。
- 公开官网位于 `official-web/`，生产路径为 `/`。
- API 统一挂载在 `/api/v1/`。
- 默认后端监听 `0.0.0.0:9999`。
- Docker 对外端口为 `6868`，由 Nginx 提供官网、管理后台、API 反代和上传文件访问。
- 数据库为 PostgreSQL，Redis 用于 Celery Broker、结果存储及相关运行能力。
- 好物导入通过 Celery 执行，并依赖共享的 `uploads/` 与 `tmp/` 数据。

## 技术栈

### 后端

- Python 要求：`>=3.11`。
- Web 框架：`FastAPI 0.111.0`、`Uvicorn 0.34.0`。
- ORM 与迁移：`Tortoise ORM 0.23.0`、`Aerich 0.8.1`、`asyncpg 0.30.0`。
- 数据校验：`Pydantic 2.10.5`、`pydantic-settings 2.7.1`。
- 异步任务：`Celery 5.4.0`、`Redis 5.2.1`。
- 文件与导入：`openpyxl`、`python-multipart`，对象存储当前实现包含 Qiniu。
- 格式与静态检查：`Black`、`isort`、`Ruff`。

### 管理后台

- 目录：`web/`。
- 框架：`Vue 3`、`Vite 4`、`Vue Router 4`、`Pinia`。
- UI：`Naive UI`。
- 样式与图标：`Sass`、`UnoCSS`、`Iconify`。
- HTTP 封装位于 `web/src/utils/http/`，业务 API 入口位于 `web/src/api/index.js`。
- 包管理锁文件为 `web/pnpm-lock.yaml`。

### 公开官网

- 目录：`official-web/`。
- 框架：`Vue 3`、`Vite 8`、`Vue Router 5`。
- UI 依赖包含 `Ant Design Vue`。
- API 调用集中在 `official-web/src/services/`，当前使用原生 `fetch`。
- `package.json` 要求 Node.js `^20.19.0 || >=22.12.0`。
- 包管理锁文件为 `official-web/pnpm-lock.yaml`。

### 运行与部署

- 容器构建使用 Node.js `20.20.2`、Python `3.11`、Nginx `1.27`。
- Docker Compose 服务：`postgres`、`redis`、`api`、`worker`、`beat`、`nginx`。
- 非 Docker 生产部署使用 `systemd`、Nginx 和 `deploy/release.sh`。

## 仓库结构

- `app/api/`：FastAPI 路由；版本入口为 `app/api/v1/`。
- `app/controllers/`：业务访问与 CRUD 编排，不把复杂业务堆入路由层。
- `app/models/`：Tortoise ORM 模型、枚举和关系定义。
- `app/schemas/`：Pydantic 请求、响应和领域数据结构。
- `app/services/`：存储、媒体、好物导入解析与上传等服务。
- `app/tasks/`：Celery 任务。
- `app/core/`：应用初始化、鉴权、权限、异常、中间件、CRUD 与 Celery 配置。
- `app/settings/`：环境配置与 `TORTOISE_ORM` 配置。
- `migrations/models/`：Aerich 迁移文件。
- `scripts/`：一次性维护、模拟数据和清理脚本；运行前必须阅读脚本影响范围。
- `web/src/`：管理后台源码。
- `official-web/src/`：公开官网源码。
- `deploy/`：非 Docker 与 Docker 部署配置、Nginx、`systemd`、发布脚本。
- `docs/`：专项运维与数据库初始化文档；当前文件在工作区中未跟踪。
- `uploads/`：运行期上传数据，不提交。
- `tmp/`：好物导入等临时数据，不提交。
- `init-data.dump`：当前工作区存在的未跟踪数据库转储；用途需结合数据库手册确认，禁止随意修改或提交。

## 文档索引

- 管理后台本地启动：阅读 `web/README.md`。
- 公开官网基础 Vite 命令：阅读 `official-web/README.md`；该文件仍是模板文档，不能作为项目架构依据。
- 单机 `Ubuntu/Debian` 部署、`systemd`、Nginx、发布与服务检查：阅读 `deploy/README.md`。
- Docker Compose 服务、数据卷、启动和日志：阅读 `deploy/docker/README.md`。
- Docker 更新范围、数据重置、迁移和常见问题：阅读 `docs/DOCKER-FAQ.md`。
- 服务器数据库初始化、迁移和 `init-data.dump` 使用：阅读 `docs/服务器数据库初始化迁移手册.md`。
- Agent 通用行为与本地回归要求：阅读 `.github/instructions/behavioral-guide.instructions.md`。
- 根目录项目概览文档 `README.md`：未找到。
- 独立 API 规范文档 `API.md`：未找到，以 `app/api/`、`app/schemas/` 和 `/openapi.json` 为准。
- 独立数据库设计文档 `DATABASE.md`：未找到，以 `app/models/` 和 `migrations/models/` 为准。
- `CHANGELOG.md`、`CONTRIBUTING.md`、`DEPLOYMENT.md`：未找到。

## 常用命令

### 后端

- 安装依赖优先使用锁文件：`uv sync`。
- 兼容部署方式：`pip install -r requirements.txt`。
- 启动 API：`python run.py` 或 `make start`。
- 启动 PostgreSQL 与 Redis：`make db-up`。
- 停止 PostgreSQL 与 Redis：`make db-down`。
- 生成迁移：`aerich migrate` 或 `make migrate`。
- 应用迁移：`aerich upgrade` 或 `make upgrade`。
- 检查格式：`make check-format`。
- Ruff 检查：`make lint`。
- 自动格式化：`make format`。
- `make install` 当前执行 `uv add pyproject.toml`，语义异常；不要将其作为可靠安装命令。
- `make test` 配置了 `pytest`，但依赖清单和仓库中均未找到 `pytest` 测试套件，执行前需要确认。

### 管理后台

- 安装：`cd web && pnpm install --frozen-lockfile`。
- 开发：`cd web && pnpm dev` 或 `make dev-admin`。
- 构建：`cd web && pnpm build` 或 `make build-admin`。
- Lint：`cd web && pnpm lint`。
- 自动修复：`cd web && pnpm lint:fix`。
- 格式化：`cd web && pnpm prettier`。

### 公开官网

- 安装：`cd official-web && pnpm install --frozen-lockfile`。
- 开发：`cd official-web && pnpm dev`。
- 构建：`cd official-web && pnpm build`。
- 预览：`cd official-web && pnpm preview`。
- `make dev-public` 与 `make build-public` 当前错误指向不存在的 `frontend/`，不要使用。

### Docker

- 完整构建启动：`docker compose --env-file .env.docker up -d --build`。
- 查看状态：`docker compose --env-file .env.docker ps`。
- 查看日志：`docker compose --env-file .env.docker logs -f api worker beat nginx`。
- 仅前端变化：`docker compose --env-file .env.docker up -d --build nginx`。
- 仅后端变化：`docker compose --env-file .env.docker up -d --build api worker beat`。
- 停止且保留数据卷：`docker compose --env-file .env.docker down`。
- `docker compose ... down -v` 会删除数据卷，未经明确授权禁止执行。

## 编码规范

### 通用

- 优先局部最小修改，不顺带重构无关代码。
- 变量和函数名表达业务含义，避免 `nextXxx`、`currentXxx`、`tempXxx` 等过程命名。
- 仅使用一次且不能提升可读性的值，不提取为中间变量。
- 函数主流程应可直接阅读，临时变量数量保持必要最少。
- 注释解释约束、原因和非显然行为，不复述代码。
- 新增依赖前先确认现有依赖无法满足，并同步更新对应锁文件或依赖清单。

### Python

- 行宽按 `pyproject.toml` 统一为 `120`。
- 使用 `Black`、`isort --profile black` 和 `Ruff`。
- 保持现有异步风格；数据库、文件和网络操作不得阻塞事件循环。
- 请求与响应结构放入 `app/schemas/`，持久化结构放入 `app/models/`。
- 复用现有 controller、service 和 `CRUDBase`，不要在路由中复制数据访问逻辑。
- 不使用可变默认参数；修改现有相关代码时一并评估风险。

### Vue 与 JavaScript

- 管理后台遵循 `web/.prettierrc.json`：单引号、无分号、`printWidth: 100`、LF。
- 管理后台遵循现有 ESLint 配置，不绕过规则或批量禁用检查。
- 公开官网保持现有 Composition API、service 和 component 分层。
- `computed` 只用于真正的派生状态，不用于简单转发或仅做空值兜底。
- 不为简单逻辑增加无意义的响应式包装。
- 复用现有组件、composable、store 和 HTTP 封装，避免创建平行实现。

## 架构规则

- API 调用链保持 `api -> controller -> model/service`，跨模块复杂逻辑放入 `service`。
- API 路由在 `app/api/v1/__init__.py` 注册，新增模块必须明确是否需要 `DependPermission`。
- 管理接口默认受 token 鉴权和基于 method/path 的权限控制。
- `/api/v1/base/` 包含登录与公开站点接口，变更时必须区分公开和受保护能力。
- 新增权限接口后，检查 API 刷新、角色绑定和菜单权限是否需要同步。
- Celery 任务必须可在独立进程中运行，不能依赖 API 进程内存状态。
- `api`、`worker`、`beat` 对好物导入文件的路径约定必须一致。
- 管理后台生产 `base` 为 `/admin/`，官网生产 `base` 为 `/`；路由和静态资源路径不得混用。
- 两个前端均通过 `/api` 访问后端，不在业务代码硬编码生产域名。

## 环境变量

- 后端由 `app/settings/config.py` 使用 `pydantic-settings` 读取根目录 `.env`。
- Docker 应用服务读取 `.env.docker`；Compose 变量替换也必须使用 `--env-file .env.docker`。
- `.env` 与 `.env.docker` 含敏感配置，不提交、不输出真实值。
- `.env.example` 与 `.env.docker.example` 当前均未找到，部署文档中的复制命令暂不可直接执行。
- 应用基础：`VERSION`、`APP_TITLE`、`PROJECT_NAME`、`APP_DESCRIPTION`、`DEBUG`、`APP_HOST`、`APP_PORT`。
- CORS：`CORS_ORIGINS`、`CORS_ALLOW_CREDENTIALS`、`CORS_ALLOW_METHODS`、`CORS_ALLOW_HEADERS`。
- PostgreSQL：`POSTGRES_HOST`、`POSTGRES_PORT`、`POSTGRES_USER`、`POSTGRES_PASSWORD`、`POSTGRES_DB`。
- Redis/Celery：`REDIS_URL`、`CELERY_BROKER_URL`、`CELERY_RESULT_BACKEND`。
- 鉴权：`SECRET_KEY`、`JWT_ALGORITHM`、`JWT_ACCESS_TOKEN_EXPIRE_MINUTES`。
- 导入任务：`PRODUCT_IMPORT_MAX_FILE_SIZE`、`PRODUCT_IMPORT_CHUNK_SIZE`、`PRODUCT_IMPORT_MAX_CONCURRENCY`、`PRODUCT_IMPORT_MAX_WORKERS`、`PRODUCT_IMPORT_CLEANUP_ENABLED`、`PRODUCT_IMPORT_CLEANUP_RETENTION_HOURS`、`PRODUCT_IMPORT_CLEANUP_INTERVAL_SECONDS`。
- 存储：`STORAGE_PROVIDER`、`QINIU_ACCESS_KEY`、`QINIU_SECRET_KEY`、`QINIU_BUCKET`、`QINIU_DOMAIN`、`QINIU_DOMAIN_SCHEME`、`QINIU_REGION`、`QINIU_IS_PRIVATE`、`QINIU_URL_EXPIRE_SECONDS`、`QINIU_UPLOAD_TIMEOUT_SECONDS`。
- 站点：`PUBLIC_SITE_URL`。
- 管理后台：`VITE_TITLE`、`VITE_PORT`、`VITE_PUBLIC_PATH`、`VITE_USE_PROXY`、`VITE_BASE_API`。
- 官网未找到独立环境变量文件；开发代理由 `official-web/vite.config.js` 指向 `http://localhost:9999`。

## 数据库规则

- 数据库仅使用 PostgreSQL；当前 ORM 配置未提供 SQLite 分支。
- 模型来源为 `app.models`，迁移工具同时注册 `aerich.models`。
- 时区配置为 `Asia/Shanghai`，`use_tz` 为 `False`；日期变更必须保持现有语义。
- 修改模型后必须生成并检查 Aerich 迁移，不手工假设生产库结构。
- 已提交迁移位于 `migrations/models/`，禁止修改已在线上执行的历史迁移来伪装新变更。
- 数据修复优先新增可审计脚本或迁移，执行前说明筛选条件、幂等性和回滚方式。
- 禁止擅自运行清库、删卷、`DROP SCHEMA`、全表删除或导入数据库转储。
- 使用 `init-data.dump` 前必须阅读 `docs/服务器数据库初始化迁移手册.md` 并确认目标数据库。

## API 规则

- API 根路径为 `/api/v1/`，OpenAPI 地址为 `/openapi.json`。
- 常规成功响应使用 `Success`：`code`、`msg`、`data`。
- 分页响应使用 `SuccessExtra`：额外包含 `total`、`page`、`page_size`。
- 常规失败响应使用 `Fail` 或统一异常处理，保持 `code`、`msg`、`data` 语义一致。
- 新增列表接口应复用现有分页、筛选、排序和 schema 模式。
- 删除接口需检查单项、批量和筛选范围语义，复用 `DeleteIdsIn` 时保持兼容。
- 不在响应、日志或异常消息中泄露 token、密码、存储密钥和数据库连接信息。
- 公开官网依赖的 `/api/v1/base/` 接口变更必须同步验证 `official-web/`。
- 管理接口变更必须同步检查 `web/src/api/`、页面调用和权限路径。

## 测试与验证

- 仓库当前未找到 Python 或前端自动化测试文件，也未找到可用测试配置。
- 后端修改至少运行 `make check-format` 和 `make lint`。
- 管理后台修改至少运行 `cd web && pnpm lint` 与 `cd web && pnpm build`。
- 公开官网修改至少运行 `cd official-web && pnpm build`。
- 模型或迁移修改需在 PostgreSQL 环境运行 `aerich upgrade`，并验证启动无迁移错误。
- Celery 修改需启动 `worker`；定时任务修改还需启动 `beat` 并检查日志。
- API 修改需启动后端，检查 `/openapi.json`，并调用受影响接口验证成功与失败路径。
- 前端交互修改需启动相应前端和 API，在浏览器回归相关页面。
- 涉及管理后台时，现有本地测试账号记录在 `.github/instructions/behavioral-guide.instructions.md`；禁止将凭据复制到新文档、代码或日志。
- Docker 相关修改至少运行 `docker compose --env-file .env.docker config`；条件允许时构建受影响服务。
- 无法执行某项验证时，最终回复必须说明原因和未覆盖风险。

## 安全规则

- 不读取、展示或提交 `.env`、`.env.docker` 中的真实秘密；只可列出变量名。
- `SECRET_KEY`、数据库密码、Qiniu 密钥和 token 必须从环境变量获取。
- 上传与压缩包处理必须校验体积、文件类型、文件名和解压路径，防止路径穿越。
- 用户输入不得直接拼接 SQL、文件路径、命令或未转义 HTML。
- 权限变更必须验证普通用户、无角色用户和超级管理员路径。
- 日志记录需避免请求体中的密码、token、密钥和大文件内容。
- 生产环境不得依赖开发 token、默认密码、宽泛 CORS 或 `DEBUG=True`。
- 删除、覆盖、迁移、导入和清理操作必须明确数据影响并获得授权。

## 禁止事项

- 禁止修改或删除与任务无关的用户改动、未跟踪文件和生成数据。
- 禁止提交 `node_modules/`、`dist/`、`build/`、`uploads/`、`tmp/`、数据库转储或真实环境文件。
- 禁止直接编辑 `web/dist/`、`web/build/`、`official-web/dist/` 等构建产物代替源码修改。
- 禁止绕过 `controller`、`service`、schema、权限和统一响应层实现临时接口。
- 禁止为小改动引入重复 helper、平行 API 客户端或无业务价值抽象。
- 禁止未经确认执行数据销毁命令、生产发布、远程推送或提交凭据。
- 禁止声称测试通过而未实际执行对应命令。
- 禁止根据过时 README 或 `Makefile` 目标猜测真实目录；以当前代码与配置为准。

## Agent 工作流程

1. 先判断任务复杂度：清晰局部任务为 L1；跨文件但边界明确为 L2；存在设计选择、数据风险或不确定性为 L3。
2. L1 直接执行；L2 先给 TODO 并等待确认；L3 一次性提出关键问题、给出选项和 TODO，确认后执行。
3. 开始前检查 `git status --short`，识别用户改动、未跟踪文件和任务边界。
4. 按「文档索引」读取相关说明，再查看入口、调用链、相邻实现和配置。
5. 明确影响范围：后端、管理后台、官网、数据库、Celery、部署和文档。
6. 优先复用现有模式，做局部最小修改；不确定时从代码和配置求证。
7. 修改后先运行最小相关检查，再按风险扩大到构建、接口、浏览器或 Docker 回归。
8. 对迁移、数据脚本、安全、权限和部署改动进行额外审查。
9. 最终检查 `git diff --check`、`git diff --stat` 和实际 diff，确认没有秘密、构建产物或无关改动。
10. 仅在用户明确要求时提交、推送、部署或执行破坏性操作。

## 完成任务后的回复格式

- `变更`：列出修改文件和实际行为变化。
- `验证`：列出已执行命令及结果，不只写“已测试”。
- `文档`：说明引用或更新了哪些现有文档；无文档变化可省略。
- `风险/未确认`：列出未执行验证、兼容性风险、环境依赖和需要用户确认的信息。
- 回复保持精炼；简单任务用短段落，复杂任务按以上四项组织。
- 不重复粘贴完整 diff，不复述已有文档的大段内容。
