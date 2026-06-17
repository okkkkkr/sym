# 七牛静态域名证书半自动续签手册

本文档只用于 `static.symluxlib.com`。

当前生产职责划分：

- 主站证书：`symluxlib.com`、`www.symluxlib.com`、`admin.symluxlib.com`、`api.symluxlib.com`
  - 由服务器上的 `certbot renew` 自动续期
- 静态资源证书：`static.symluxlib.com`
  - 由七牛接入流量
  - 由本机手工签发证书后上传到七牛

`static.symluxlib.com` 不要再加入服务器主站的 `certbot` 证书列表。

## 1. 适用前提

执行本手册前，需满足：

- `static.symluxlib.com` 已在域名 DNS 中配置为七牛要求的 `CNAME`
- 七牛侧已经绑定 `static.symluxlib.com`
- 服务器已安装 `acme.sh`
- 当前 DNS 面板支持新增 `TXT` 记录

## 2. 首次安装 acme.sh

如服务器尚未安装 `acme.sh`，执行：

```bash
curl https://get.acme.sh | sh
source ~/.bashrc
acme.sh --register-account --server letsencrypt
acme.sh --set-default-ca --server letsencrypt
```

如果当前 shell 不是 `bash`，请改为加载对应 shell 配置文件。

## 3. 发起证书签发

在服务器执行：

```bash
acme.sh --issue --server letsencrypt --dns -d static.symluxlib.com --yes-I-know-dns-manual-mode-enough-go-ahead-please
```

执行后会输出一条待添加的 `TXT` 记录，类似：

```text
Domain: _acme-challenge.static.symluxlib.com
TXT value: xxxxxxxxxxxxxxxxx
```

## 4. 在域名后台添加 TXT 记录

到域名 DNS 管理后台新增一条记录：

| 字段 | 值 |
| --- | --- |
| `Subdomain` / 主机记录 | `_acme-challenge.static` |
| `Record Type` / 记录类型 | `TXT` |
| `IP Address / Target Host` / 记录值 | 上一步输出的 `TXT value` |

注意：

- `Subdomain` 填 `_acme-challenge.static`
- 不是 `static`
- 也不是完整域名 `static.symluxlib.com`

保存后等待解析生效。

## 5. 确认 TXT 记录生效

在服务器执行：

```bash
dig @8.8.8.8 TXT _acme-challenge.static.symluxlib.com +short
dig @1.1.1.1 TXT _acme-challenge.static.symluxlib.com +short
```

预期返回刚才填入的 `TXT value`。

如果没有返回：

- 检查 DNS 后台字段是否填反
- 等待几分钟后重试
- 不要在未生效前继续下一步

## 6. 完成签发

确认 TXT 生效后执行：

```bash
acme.sh --renew --server letsencrypt -d static.symluxlib.com --yes-I-know-dns-manual-mode-enough-go-ahead-please
```

成功后，`acme.sh` 会输出证书路径，常见位置为：

```text
/root/.acme.sh/static.symluxlib.com_ecc/fullchain.cer
/root/.acme.sh/static.symluxlib.com_ecc/static.symluxlib.com.key
```

## 7. 导出为上传文件

为避免每次都直接操作 `~/.acme.sh` 目录，统一导出到固定位置：

```bash
mkdir -p ~/certs/static.symluxlib.com

cp /root/.acme.sh/static.symluxlib.com_ecc/fullchain.cer ~/certs/static.symluxlib.com/fullchain.pem
cp /root/.acme.sh/static.symluxlib.com_ecc/static.symluxlib.com.key ~/certs/static.symluxlib.com/privkey.pem

ls -l ~/certs/static.symluxlib.com
```

最终用于上传七牛的文件是：

- `~/certs/static.symluxlib.com/fullchain.pem`
- `~/certs/static.symluxlib.com/privkey.pem`

## 8. 上传到七牛

进入七牛 HTTPS 证书上传页面，填写：

| 字段 | 值 |
| --- | --- |
| 证书备注名 | 例如 `static-symluxlib-2026-06-17` |
| 证书内容 | `cat ~/certs/static.symluxlib.com/fullchain.pem` 输出全文 |
| 私钥内容 | `cat ~/certs/static.symluxlib.com/privkey.pem` 输出全文 |

查看内容命令：

```bash
cat ~/certs/static.symluxlib.com/fullchain.pem
cat ~/certs/static.symluxlib.com/privkey.pem
```

上传完成后，将新证书绑定到 `static.symluxlib.com`。

## 9. 验证

不要用根路径 `/` 验证，直接访问真实文件：

```bash
curl -I "https://static.symluxlib.com/实际文件路径"
```

例如：

```bash
curl -I "https://static.symluxlib.com/logo/logo_20260617_pql4f8fi.jpg"
```

返回 `200` 即表示证书和七牛绑定生效。

## 10. 后续每次续签的最短流程

### 10.1 申请新的 TXT 挑战值

```bash
acme.sh --issue --server letsencrypt --dns -d static.symluxlib.com --yes-I-know-dns-manual-mode-enough-go-ahead-please
```

### 10.2 到 DNS 后台更新 TXT 记录

- `Subdomain`：`_acme-challenge.static`
- `Record Type`：`TXT`
- 记录值：用本次新输出的 `TXT value`

### 10.3 确认 TXT 已生效

```bash
dig @8.8.8.8 TXT _acme-challenge.static.symluxlib.com +short
dig @1.1.1.1 TXT _acme-challenge.static.symluxlib.com +short
```

### 10.4 完成签发

```bash
acme.sh --renew --server letsencrypt -d static.symluxlib.com --yes-I-know-dns-manual-mode-enough-go-ahead-please
```

### 10.5 导出文件

```bash
cp /root/.acme.sh/static.symluxlib.com_ecc/fullchain.cer ~/certs/static.symluxlib.com/fullchain.pem
cp /root/.acme.sh/static.symluxlib.com_ecc/static.symluxlib.com.key ~/certs/static.symluxlib.com/privkey.pem
```

### 10.6 上传七牛并验证

- 上传 `fullchain.pem` 和 `privkey.pem`
- 绑定到 `static.symluxlib.com`
- 用真实文件 URL 验证

## 11. 建议周期

Let's Encrypt 证书通常有效期约 90 天，建议：

- 每 60 天处理一次
- 最晚在到期前 20 天完成更新

建议在日历或提醒工具中设置固定提醒：

```text
续签 static.symluxlib.com 七牛证书
```

## 12. 常见错误

### 12.1 `ZeroSSL` 要求先填邮箱

原因：`acme.sh` 默认切到 `ZeroSSL`。

处理：

```bash
acme.sh --set-default-ca --server letsencrypt
```

### 12.2 `dig TXT` 查不到记录

优先检查：

- DNS 后台是否把 `Subdomain` 和 `TXT value` 填反
- 是否真的保存成功
- 是否等待了足够的解析时间

### 12.3 七牛根路径返回 `404`

这不一定是故障。

对象存储/CDN 场景下，根路径没有默认文件是正常的。应以真实文件 URL 是否能正常访问为准。
