# SYM 生产部署说明

这个目录存放的是单机 `Ubuntu/Debian` 非 Docker 部署所需的配置和脚本。

## 目录结构

- `/opt/sym`：仓库源码根目录
- `/opt/sym/.venv`：Python 虚拟环境
- `/opt/sym/.env`：后端运行配置
- `/opt/sym/web/dist`：管理后台构建产物
- `/opt/sym/official-web/dist`：官网构建产物
- `/opt/sym/uploads`：上传文件目录

## 首次部署

建议按下面的顺序分步骤执行，不要第一次就整段一起复制运行。每完成一步，先确认没有报错，再继续下一步。

### 第 1 步：创建部署用户和目录

```bash
sudo adduser --system --group --home /opt/sym sym
sudo mkdir -p /opt/sym /opt/sym/uploads /opt/sym/tmp
sudo chown -R sym:sym /opt/sym
```

### 第 2 步：拉取仓库代码

```bash
sudo -u sym git clone <your-repo-url> /opt/sym
cd /opt/sym
```

### 第 3 步：创建虚拟环境并安装后端依赖

```bash
sudo -u sym python3 -m venv .venv
sudo -u sym .venv/bin/pip install -r requirements.txt
sudo apt-get install -y ffmpeg
```

### 第 4 步：创建后端配置文件

```bash
sudo -u sym cp .env.example .env
```

这一步执行完后，先手动编辑 `/opt/sym/.env`，填入生产环境真实配置，再继续后面的步骤。

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

`R2_PUBLIC_BASE_URL` 应使用绑定到 R2 bucket 的公开访问域名。密钥只写入服务器 `.env`，不要提交到仓库。

### 第 5 步：安装前端构建工具并构建前端

```bash
sudo -u sym corepack enable
sudo -u sym corepack prepare pnpm@9.15.9 --activate
sudo -u sym bash -lc 'cd /opt/sym/web && pnpm install --frozen-lockfile && pnpm build'
sudo -u sym bash -lc 'cd /opt/sym/official-web && pnpm install --frozen-lockfile && pnpm build'
```

### 第 6 步：安装 systemd service

```bash
sudo cp deploy/systemd/sym-api.service /etc/systemd/system/
sudo cp deploy/systemd/sym-celery-worker.service /etc/systemd/system/
sudo cp deploy/systemd/sym-celery-beat.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now sym-api sym-celery-worker sym-celery-beat
```

### 第 7 步：安装 Nginx 配置

```bash
sudo cp deploy/nginx/sym.conf /etc/nginx/sites-available/sym.conf
sudo ln -sf /etc/nginx/sites-available/sym.conf /etc/nginx/sites-enabled/sym.conf
sudo nginx -t
sudo systemctl reload nginx
```

### 第 8 步：检查服务状态

```bash
sudo systemctl status sym-api
sudo systemctl status sym-celery-worker
sudo systemctl status sym-celery-beat
```

## 发布流程

首次部署完成后，后续发布通常只需要执行这一条：

```bash
cd /opt/sym
bash deploy/release.sh
```

如果这次修改了 Nginx 配置，再执行：

```bash
cd /opt/sym
bash deploy/release.sh --reload-nginx
```

### 清理本地历史上传文件

切到 R2 并确认不再需要历史 `/uploads/...` 文件后，可以清空本地上传目录：

```bash
sudo systemctl stop sym-api sym-celery-worker sym-celery-beat
sudo -u sym find /opt/sym/uploads -mindepth 1 -exec rm -rf {} +
sudo systemctl start sym-api sym-celery-worker sym-celery-beat
```

执行前需要确认数据库中旧的本地图片、视频、Logo、二维码和首页装修图记录已经可以废弃；清空后这些旧 `/uploads/...` URL 会返回 404。

## 验证方式

- `systemctl status sym-api`
- `systemctl status sym-celery-worker`
- `systemctl status sym-celery-beat`
- `journalctl -u sym-api -f`
- `journalctl -u sym-celery-worker -f`
- `journalctl -u sym-celery-beat -f`
- `curl http://127.0.0.1:9999/openapi.json`
- 通过 Nginx 访问 `/` 和 `/admin/`
