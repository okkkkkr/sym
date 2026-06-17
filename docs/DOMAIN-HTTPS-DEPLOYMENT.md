# 域名与 HTTPS 部署步骤

本文档用于将生产访问入口切换为：

- 官网：`https://symluxlib.com`
- 官网跳转：`https://www.symluxlib.com` -> `https://symluxlib.com`
- 管理后台：`https://admin.symluxlib.com`
- API：`https://api.symluxlib.com/api/v1/...`

## 1. DNS

在域名服务商后台配置：

| 记录类型 | 主机记录 | 记录值 | 用途 |
| --- | --- | --- | --- |
| A | `@` | `45.221.114.153` | 官网 |
| A | `www` | `45.221.114.153` | 跳转到根域 |
| A | `admin` | `45.221.114.153` | 管理后台 |
| A | `api` | `45.221.114.153` | API |

DNS 只能解析到 IP，不能解析到业务端口。

## 2. 安全组

正式只开放：

| 端口 | 协议 | 来源 | 用途 |
| --- | --- | --- | --- |
| 80 | TCP | `0.0.0.0/0` | HTTP、Let's Encrypt 校验、跳转 HTTPS |
| 443 | TCP | `0.0.0.0/0` | HTTPS 正式访问 |

不要开放 `9999`、`5432`、`6379` 或旧的 `6868` 到公网。

## 3. 环境变量

生产 `.env.docker` 至少确认：

```env
APP_HOST=0.0.0.0
APP_PORT=9999
PUBLIC_SITE_URL=https://symluxlib.com
CORS_ORIGINS=["https://symluxlib.com","https://www.symluxlib.com","https://admin.symluxlib.com"]
```

真实密钥、数据库密码、对象存储密钥只写入服务器上的 `.env.docker`，不要提交 Git。

## 4. 首次启动 HTTP Bootstrap

首次部署时证书还不存在，必须先使用 HTTP bootstrap 配置：

```bash
docker compose --env-file .env.docker up -d --build
docker compose --env-file .env.docker ps
```

确认 ACME 目录可访问：

```bash
curl -I http://symluxlib.com/.well-known/acme-challenge/test
```

返回 404 可以接受，重点是请求能到达 Nginx，而不是连接失败。

## 5. 申请证书

DNS 生效且 80 端口可访问后执行：

```bash
docker compose --profile certbot --env-file .env.docker run --rm certbot certonly \
  --webroot \
  --webroot-path /var/www/certbot \
  -d symluxlib.com \
  -d www.symluxlib.com \
  -d admin.symluxlib.com \
  -d api.symluxlib.com \
  --agree-tos \
  --register-unsafely-without-email
```

成功后应生成：

```text
certbot/conf/live/symluxlib.com/fullchain.pem
certbot/conf/live/symluxlib.com/privkey.pem
```

## 6. 切换 HTTPS

证书成功后使用 HTTPS 覆盖配置启动 Nginx：

```bash
docker compose -f compose.yaml -f compose.https.yaml --env-file .env.docker up -d nginx
```

后续更新生产服务也建议继续带上覆盖文件：

```bash
docker compose -f compose.yaml -f compose.https.yaml --env-file .env.docker up -d --build
```

## 7. 自动续期

在服务器 crontab 或 systemd timer 中定期执行：

```bash
cd /path/to/sym
docker compose --profile certbot --env-file .env.docker run --rm certbot renew
docker compose -f compose.yaml -f compose.https.yaml --env-file .env.docker exec nginx nginx -s reload
```

## 8. 验收

```bash
curl -I https://symluxlib.com
curl -I https://www.symluxlib.com
curl -I https://admin.symluxlib.com
curl -I https://api.symluxlib.com/openapi.json
curl -I https://symluxlib.com/admin/
curl -I http://45.221.114.153:9999
curl -I http://45.221.114.153:6868
```

预期：

- `https://symluxlib.com` 返回官网。
- `https://www.symluxlib.com` 301 到 `https://symluxlib.com`。
- `https://admin.symluxlib.com` 返回管理后台。
- `https://api.symluxlib.com/openapi.json` 返回 API 文档 JSON。
- `https://symluxlib.com/admin/` 返回 404。
- `45.221.114.153:9999` 和 `45.221.114.153:6868` 公网不可访问。
