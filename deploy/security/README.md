# 生产安全启用步骤

这些文件只提供项目内防护；脚本默认 dry-run，不会自行修改服务器或 Cloudflare。

1. 使用 `install -m 600 /dev/null .env.docker` 创建配置文件，参考 `app/settings/config.py` 和 Docker 部署文档填写随机 `SECRET_KEY`、数据库及 R2 凭据。生产 Compose 会强制 `APP_ENV=production` 与 `PRODUCT_IMPORT_ENABLED=false`。
2. 在项目根目录运行 `python -m scripts.check_product_import_shutdown`。只有输出无活跃任务后才能停用 ZIP 导入。
3. 使用 `htpasswd -B -c deploy/security/admin.htpasswd <admin-name>` 生成后台外层认证；不要提交该文件。`ADMIN_HTPASSWD_FILE` 会把它作为只读 Compose Secret 挂载到 Nginx。
4. 执行数据库备份，然后运行 `aerich upgrade`；首次管理员使用 `python scripts/create_admin.py` 创建，不再由启动流程生成默认账户。
5. 先运行防火墙 dry-run：`python deploy/security/render_nftables.py --ssh-ipv4 <管理员CIDR>`。保留一个已验证的备用 SSH 会话后，才追加 `--apply`。脚本只允许 Cloudflare CIDR 访问 80/443，只允许给定管理员 CIDR 访问 SSH。
6. 将 `sshd_config.conf` 安装为 sshd 配置片段，执行 `sshd -t` 成功后再 reload；确认密钥登录可用后才关闭旧会话。
7. 将 Fail2ban 的 `filter.d`、`action.d`、`jail.d` 文件复制到 `/etc/fail2ban/`。把 `jail.d/sym.local` 中 `/srv/sym` 改为实际部署目录。
8. 安装 `cloudflare_access_rule.py` 为 `/usr/local/libexec/sym-cloudflare-ban`，owner 为 root、模式 `0755`。创建 `/etc/fail2ban/cloudflare.env`，模式 `0600`：

   ```env
   CF_ZONE_ID=<zone-id>
   CF_API_TOKEN=<只授予 Firewall Access Rules Write 的受限 Token>
   ```

9. 在 `sym.local` 的 `ignoreip` 追加管理员、监控与可信出口 CIDR，然后运行 `fail2ban-client -t`、`fail2ban-regex` 验证过滤器，最后 reload Fail2ban。
10. Cloudflare 免费 Custom Rule 使用 `cloudflare-sensitive-expression.txt` 中的表达式并执行 Block。表达式不依赖付费正则能力，且保留 `/.well-known/acme-challenge/`。Cloudflare API 不可用时，Nginx 404/限流与 Redis 封锁仍独立生效。

Cloudflare 当前的 IP Access Rule API 即使使用 Zone endpoint，官方文档也要求 Token 具有 `Account Firewall Access Rules Write` 权限。脚本只访问 `CF_ZONE_ID` 指定的 Zone，但 Token 权限本身无法缩小为纯 Zone 权限。如果不能接受这一授权范围，不要启用 `sym-cloudflare` banaction；Nginx、Redis、Fail2ban 日志检测和源站防火墙仍可独立使用，边缘 IP 封禁改为人工维护。

发布使用 `NGINX_DEFAULT_CONF_FILE=nginx.https.conf`。先执行 `docker compose --env-file .env.docker config` 和容器内 `nginx -t`，再切换入口。`api.symluxlib.com` 应返回 404；官网仅可访问公开 `/api/v1/base/*`；后台页面和 API 必须先通过 Basic Auth。

R2 Token 只授予目标 Bucket 的对象读写/删除/列举能力，不授予账户级管理权限。Cloudflare IP 清单来源为官方地址，发布前比较 `https://www.cloudflare.com/ips-v4` 与 `ips-v6`，更新 `deploy/docker/cloudflare-real-ip.inc` 后再部署。
