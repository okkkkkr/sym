# StorageProvider 配置说明

项目通过统一 `StorageProvider` 抽象管理商品图片、商品视频、站点 Logo、联系二维码和首页装修图片。

## 上传方式

管理后台统一把文件上传到后端 API，由后端根据 `STORAGE_DRIVER` 调用具体 provider。业务层只处理：

- `key`
- `url`
- `size`
- `mimeType`
- `storageDriver`

前端和业务代码不直接处理本地路径、对象存储地址或七牛上传凭证。

## 通用配置

```env
STORAGE_DRIVER=local
MEDIA_UPLOAD_MAX_FILE_SIZE=524288000
```

`STORAGE_DRIVER` 可选：

- `local`
- `r2`
- `s3`
- `qiniu`

旧变量 `STORAGE_PROVIDER` 仍作为兼容别名；新部署优先使用 `STORAGE_DRIVER`。

## Local

```env
STORAGE_DRIVER=local
LOCAL_STORAGE_ROOT=/opt/sym/uploads
LOCAL_STORAGE_PUBLIC_BASE_URL=/uploads
LOCAL_STORAGE_MAX_FILE_SIZE=524288000
```

本地存储会自动创建目录，并校验最终路径必须位于 `LOCAL_STORAGE_ROOT` 内，防止路径穿越。

## Cloudflare R2

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

R2 使用独立的 `r2` driver 和 `R2_*` 配置项。底层通过 Cloudflare R2 的对象存储 API 上传、删除和列举对象，业务层不复用 `S3_*` 变量。

`R2_PUBLIC_BASE_URL` 必须是可被浏览器访问的公开域名，推荐使用绑定到 R2 bucket 的 Cloudflare Custom Domain。项目保存数据库时仍保存对象 key，接口响应时再拼接为公开 URL。

## S3 Compatible

```env
STORAGE_DRIVER=s3
S3_ENDPOINT_URL=https://<endpoint>
S3_BUCKET=<bucket>
S3_REGION=auto
S3_ACCESS_KEY=<access-key>
S3_SECRET_KEY=<secret-key>
S3_PUBLIC_BASE_URL=https://<public-domain>
S3_FORCE_PATH_STYLE=false
```

适用于 AWS S3、MinIO 和其他 S3 Compatible 服务。Cloudflare R2 在本项目中使用独立的 `r2` driver。

## Qiniu

```env
STORAGE_DRIVER=qiniu
QINIU_ACCESS_KEY=<access-key>
QINIU_SECRET_KEY=<secret-key>
QINIU_BUCKET=<bucket>
QINIU_REGION=<region>
QINIU_PUBLIC_BASE_URL=https://<public-domain>
```

兼容旧配置：

```env
QINIU_DOMAIN=<domain>
QINIU_DOMAIN_SCHEME=https
```

如果 `QINIU_PUBLIC_BASE_URL` 未配置，会尝试使用旧的 `QINIU_DOMAIN` 和 `QINIU_DOMAIN_SCHEME` 拼接访问域名。

## 启动校验

API 与 Celery worker 启动时会校验当前 driver 必需配置。配置缺失会直接启动失败，错误信息只列出缺失变量名，不输出密钥值。

## 未引用媒体清理

```env
MEDIA_ORPHAN_CLEANUP_ENABLED=true
MEDIA_ORPHAN_CLEANUP_DRY_RUN=true
MEDIA_ORPHAN_RETENTION_HOURS=24
MEDIA_ORPHAN_CLEANUP_INTERVAL_SECONDS=21600
MEDIA_ORPHAN_CLEANUP_BATCH_SIZE=1000
MEDIA_ORPHAN_CLEANUP_PREFIXES=logo/,contacts/,home-layout/,items/images/,items/videos/
```

默认先以 `dry-run` 方式运行，只记录超过保留期且未被数据库引用的媒体对象，不实际删除。确认日志无误后，再把 `MEDIA_ORPHAN_CLEANUP_DRY_RUN` 切到 `false`。

## 迁移兼容

数据库继续保存对象 key，key 不包含 driver 前缀，例如：

- `items/images/img_20260622_abcd1234.jpg`
- `items/videos/vid_20260622_abcd1234.mp4`
- `logo/logo_20260622_abcd1234.png`

切换 provider 时，数据库和业务代码无需修改；但目标存储中必须提前存在相同 key 的文件对象，否则 URL 会生成成功但文件无法访问。

如果切换到 R2 后决定清理本地历史文件，需要先确认数据库中仍引用 `/uploads/...` 的旧资源会失效。确认清理后，按 Docker 或非 Docker 部署文档中的上传目录清理命令执行。
