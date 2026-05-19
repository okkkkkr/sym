# 批量上传（ZIP 包，≤200MB）任务计划（含断点续传与消息队列）

## 一、实现目标
支持用户上传一个 ≤200MB 的 ZIP 压缩包，其中包含：
- 好物信息表格 `product.xlsx`
- 以好物名称命名的文件夹，内含封面、介绍图或视频。系统自动解析、上传媒体至七牛云 Kodo，最后写入数据库。


### 1.1 各端需求
- **管理系统前端**：新增批量管理一级菜单，批量管理菜单下新增好物一键导入二级菜单，提供文件上传功能，显示导入任务列表（状态、进度、错误日志等），能够下载导入结果，下载错误日志等。
- **后端 api**：接收文件，异步处理，提供查询接口获取导入任务状态、进度、错误日志等信息。

## 二、技术栈
| 用途 | 技术 |
| --- | --- |
| Web 框架 | FastAPI（异步） |
| ORM | Tortoise-ORM |
| 数据库 | SQLite / PostgreSQL |
| 对象存储 | 七牛云 Kodo SDK（同步，需线程池包装） |
| Excel 解析 | pandas / openpyxl |
| ZIP 解压 | Python 内置 `zipfile` |
| 基础异步任务 | FastAPI `BackgroundTasks` + `asyncio.Semaphore` |
| **可选 - 消息队列** | Celery + Redis（broker/backend） |
| **可选 - 断点续传** | 前端分片上传（resumable.js 或七牛 JS SDK）+ 后端合并 |
| 并发控制 | `asyncio.Semaphore` / Celery `worker_concurrency` |
| 阻塞操作隔离 | `concurrent.futures.ThreadPoolExecutor` |
| 状态缓存 | Redis（任务进度、分片信息） |
| 环境配置 | `python-dotenv` / `pydantic-settings` |
| 日志记录 | `loguru` |

## 三、ZIP 包内部格式规范

### 3.1 根目录结构示例
    好物批量导入.zip
    ├── product.xlsx              # 好物信息表（必须）
    ├── 好物A/                    # 以好物名称命名的文件夹
    │   ├── 好物A_cover.jpg       # 封面图（文件名包含 _cover）
    │   ├── 好物A_1.png           # 介绍图1
    │   ├── 好物A_2.mp4           # 介绍视频
    │   └── 好物A_3.jpg           # 介绍图2
    ├── 好物B/
    │   ├── 好物B_cover.png
    │   └── 好物B_1.jpg
    └── 好物C/
        └── 好物C_1.mp4

### 3.2 product.xlsx 表格要求
- **必须包含的列**：`name`（好物名称），值必须与顶层文件夹名称**完全一致**（大小写敏感）。
- **其他可选列**：如 `price`、`description`、`category`，可根据业务需求扩展。

### 3.3 素材文件夹规则
- 文件夹名称 = `name` 列值，位于 ZIP 根目录下。
- 文件夹内可包含任意数量的图片（`jpg/png`）或视频（`mp4/mov`等）。
- 文件名中的数字仅为避免重名，**无实际排序意义**。
- **特殊文件名识别**：只要文件名包含 `_cover`（如 `xxx_cover.jpg`、`cover.png`），即视为**封面素材**。若同一好物出现多个封面，取第一个（按字母序或读取顺序）。
- 其余文件统称为**普通素材**。

### 3.4 数据库字段映射
| 数据库字段 | 来源 | 说明 |
| --- | --- | --- |
| `name` | product.xlsx 的 `name` 列 | 好物名称 |
| `cover_url` | 封面素材上传后的 URL | 如果存在封面文件，则存入此字段，另外还需要存入 `intro_images` 中。 如果不存在封面文件，则取 `intro_images` 中的第一张图片 URL（如果存在） |
| `intro_images` (String Array) | 所有图片素材（封面、普通图片）按优先级排序后的 URL 列表。 | 用于前端展示介绍图 |
| `intro_videos` (String Array) | 所有视频素材按文件名排序后的 URL 列表 | 用于前端展示介绍视频 |

## 四、解析、上传与入库逻辑说明

### 4.1 整体流程（后台任务执行）
    解压 ZIP
      ↓
    读取 product.xlsx
      ↓
    遍历每一行（每个好物）
      ├── 根据 name 定位素材文件夹
      ├── 扫描文件夹内所有图片/视频文件
      ├── 分类：封面素材（文件名含 _cover）、视频、普通图片
      ├── 按优先级排序：视频 > 封面图 > 普通图片
    ├── 并发上传媒体文件到七牛云（线程池包装）
    ├── 分别收集上传后的图片与视频 URL 列表（`intro_images`、`intro_videos`）
    ├── 若存在封面图，取第一个的 URL 存入 `cover_url`；若不存在封面图但存在图片，则使用第一张成功上传的图片 URL 作为 `cover_url`（封面 URL 也应包含在 `intro_images` 中）
    └── 将好物数据（含 `cover_url`、`intro_images` 和 `intro_videos`）写入数据库

### 4.2 详细步骤

#### 步骤1：读取 product.xlsx
- 使用 `pandas.read_excel` 在线程池中执行。
- 校验必须包含 `name` 列，否则任务失败。
- 对每个 `name` 去除首尾空格，作为文件夹查找的关键词。

#### 步骤2：定位素材文件夹
- 在解压后的临时目录根目录下，查找与 `name` 完全匹配的文件夹。
- 若文件夹不存在，记录错误并跳过该好物。
- 使用 `os.listdir` 获取文件夹内所有文件，过滤出图片（`.jpg/.jpeg/.png/.gif/.bmp`）和视频（`.mp4/.mov/.avi/.mkv`）。

#### 步骤3：素材分类与排序
    # 伪代码逻辑
    cover_file = None
    videos = []
    images = []
    
    for file in all_files:
        if '_cover' in file.lower():   # 忽略大小写
            cover_file = file
        elif file.lower().endswith(('.mp4', '.mov', '.avi')):
            videos.append(file)
        else:
            images.append(file)
    
    videos.sort()
    images.sort()
    
    sorted_materials = []
    sorted_materials.extend(videos)      # 视频在最前
    if cover_file:
        sorted_materials.append(cover_file)  # 封面次之
    sorted_materials.extend(images)      # 普通图片最后

#### 步骤4：并发上传至七牛云
- 使用 `ThreadPoolExecutor`（建议 max_workers=4~6）并发上传。
- 上传路径规则：`products/{好物name}/{原文件名}`，避免重名。
- 每个文件上传成功后返回公开 URL：视频 URL 收集到 `intro_videos`（按文件名排序），图片（包含封面）收集到 `intro_images`（封面应位于图片数组前端）。
- 同时记录封面 URL：如果 `cover_file` 存在，取上传后对应的 URL 存入 `cover_url`；若不存在 `cover_file` 且 `intro_images` 非空，则取 `intro_images[0]` 作为 `cover_url`。

#### 步骤5：数据库写入
- 使用 Tortoise-ORM 异步创建 `Product` 记录。
- `intro_images` 与 `intro_videos` 字段均为 JSON 类型，分别存储图片与视频 URL 列表。
- 若某好物处理失败（如文件夹缺失、无任何素材），记录错误到 `ImportTask` 的错误日志中，并跳过该好物，继续处理下一个。
- 待所有好物处理完成后，更新 `ImportTask` 状态为完成，并记录成功与失败的统计信息，包含失败原因。

#### 步骤6：特殊规则确认
- **视频优先级最高**：即使视频文件名包含 `_cover`，依然视为视频（建议文档中提示用户避免混用）。
- **封面图同时出现在 `intro_images` 中**：满足图片内部的优先级（封面优先于普通图片）。视频与图片分开存放，视频整体优先级高于图片，但存储在独立字段 `intro_videos` 中。
- **多个封面文件**：取第一个（按文件名排序）。模板中应提醒用户只放一个封面。

### 4.3 注意事项
| 问题 | 解决方案 |
| --- | --- |
| **大小写敏感** | 建议在匹配时将 `name` 与文件夹名统一转换为小写比较，但保留原始名称用于上传路径。 |
| **文件名特殊字符** | 上传到七牛前对文件名进行 URL 编码或去除不安全字符（空格、中文转拼音）。 |
| **单好物素材过多** | 建议限制每个文件夹不超过 20 个文件，防止处理耗时过长。 |
| **视频上传耗时** | 控制线程池并发数（4~6），避免同时上传多个大文件导致网络拥塞。 |
| **优先级排序稳定性** | 使用自然排序（`natsorted` 或普通字符串排序），避免依赖 `os.listdir` 的随机顺序。 |
| **无封面素材** | 若没有含 `_cover` 的文件，但存在图片，则使用第一张成功上传的图片作为 `cover_url`；`intro_images` 仅包含普通图片，`intro_videos` 包含视频（若有）。 |
| **无任何素材** | 好物仍可入库（仅文字信息），`intro_images` 和 `intro_videos` 为空数组。 |
| **视频与图片混合** | 视频与图片分开存储：`intro_videos` 为所有视频（按文件名排序），`intro_images` 为封面（若有）再普通图片（按文件名排序）。 |

### 4.4 重复/冲突策略
- **判定方式**：通过对 `name` 进行规范化后的精确匹配（去首尾空格并转为小写、做 Unicode NFKC 归一化）来判断是否重复。优先不使用模糊匹配或媒体指纹，保持导入速度与确定性。
- **处理方式**：若判定为重复（名称匹配），将**创建一条新的记录**（不覆盖现有记录）；新记录与原记录可共存，媒体资源独立入库。重复项会被记录到导入结果/事件日志中以便追溯。
