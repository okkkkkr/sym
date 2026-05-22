# 好物批量导入技术方案

## 一、方案目标

建设一套完整的好物批量导入系统，支持管理员上传不超过 200MB 的 ZIP 包，系统完成分片上传、断点续传、异步排队、结构校验、媒体上传、数据入库、失败回溯、任务重试与结果下载，并与当前项目中的好物数据模型、权限体系、菜单体系、对象存储和部署环境打通。

方案交付后，应具备以下能力：

- 支持 ZIP 包分片上传与断点续传
- 支持导入任务异步执行、排队、取消、重试
- 支持导入前预校验和导入后错误回溯
- 支持图片、视频批量上传到统一对象存储
- 支持按当前 Product 数据结构批量创建好物
- 支持任务中心、错误报告、模板下载、示例包下载
- 支持独立菜单页和现有好物管理页联动入口

## 二、适用范围

本方案适用于后台管理系统中的批量导入场景，当前聚焦好物导入，同时为后续品牌、标签、分类等批量能力预留统一平台入口。

本方案不包含以下高风险或低收益能力：

- 默认自动覆盖历史同名好物
- 品牌、分类、标签的模糊匹配
- 单独建设复杂富文本可视化导入编辑器

这些能力不是完整交付的必要条件，且会显著增加数据不确定性和维护成本。

## 三、业务规则

## 3.1 导入对象
导入对象为当前系统中的好物实体，对应现有 Product 模型能力，包含：

- 分类
- 品牌
- 名称
- 好物识别码自定义部分
- 简介
- 结构化详情
- 封面图
- 图片列表
- 视频列表
- 上下架状态
- 排序
- 标签

## 3.2 基本业务约束

- `category_id` 必填，且必须能由模板中的分类名称精确解析得到
- `brand_id` 必填，且品牌必须属于所选分类
- `cover_image_url` 必填，因此每个好物目录至少需要一张图片
- `detail_description` 为 JSON 数组结构，模板必须提供可映射方式
- 标签通过名称精确匹配，不允许模糊兜底
- 同名好物允许重复创建，但必须在导入报告中给出重复提示

## 3.3 重复策略

- 默认策略：新增记录，不覆盖历史数据
- 重复判定：对 `name` 做去首尾空格和规范化后精确匹配
- 辅助提示：同时记录重复项的分类、品牌是否一致
- 若后续需要覆盖策略，必须设计为用户显式选择的导入策略，不允许默认覆盖

## 四、管理端产品形态

## 4.1 菜单规划

建议新增一级菜单：`批量中心`

建议二级菜单如下：

- `好物批量导入`
- `导入任务记录`
- `品牌批量导入`，预留
- `标签批量导入`，预留

这样设计的原因：

- 批量导入是一套独立任务系统，不只是好物列表页上的一个按钮
- 后续存在扩展到更多实体的高概率需求
- 独立一级菜单更利于角色隔离和权限授权

## 4.2 与现有好物管理页的关系

即便批量导入采用独立一级菜单，也建议保留现有好物管理页中的快捷入口：

- 在好物管理页提供“去批量导入”入口
- 导入成功后支持跳回好物列表页并按任务结果筛选
- 单个好物编辑和批量导入共用相同的数据模型、上传能力和权限体系

## 4.3 页面结构

### 页面一：好物批量导入

建议包含以下区域：

- 导入说明区
- 模板下载区
- 示例 ZIP 下载区
- ZIP 上传区
- 导入策略区
- 最近任务概览区

### 页面二：导入任务记录

建议包含以下区域：

- 任务筛选区
- 任务列表区
- 任务详情抽屉或详情页
- 错误报告下载区
- 失败项重试区

## 五、导入文件规范

## 5.1 ZIP 结构规范

ZIP 根目录固定包含一个 Excel 文件和多个以好物名称命名的素材目录。

示例：

```text
好物批量导入.zip
├── product.xlsx
├── 好物A/
│   ├── 好物A_cover.jpg
│   ├── 好物A_1.jpg
│   ├── 好物A_2.png
│   └── 好物A_3.mp4
├── 好物B/
│   ├── 好物B_cover.png
│   └── 好物B_1.jpg
└── 好物C/
    ├── 好物C_1.jpg
    └── 好物C_2.mov
```

约束如下：

- ZIP 根目录必须存在 `product.xlsx`
- 每个素材目录名称必须与 Excel 中的 `name` 精确对应
- 目录层级只允许一层，不支持嵌套子目录
- 不允许目录穿越路径和非法文件名

## 5.2 Excel 模板规范

建议模板字段如下：

| 列名 | 是否必填 | 说明 |
| --- | --- | --- |
| `name` | 是 | 好物名称，必须与素材目录名一致 |
| `category_name` | 是 | 分类名称，精确匹配 |
| `brand_name` | 是 | 品牌名称，精确匹配，且必须属于分类 |
| `desc` | 否 | 好物简介 |
| `tag_names` | 否 | 标签名称，多值支持分号分隔 |
| `product_code_custom` | 否 | 识别码自定义数字部分 |
| `status` | 否 | 支持 `true/false`、`1/0`、`是/否` |
| `order` | 否 | 排序值，默认 0 |
| `detail_text` | 否 | 纯文本详情 |
| `detail_description_json` | 否 | 合法 JSON 数组，优先级高于 `detail_text` |

## 5.3 详情字段映射规则

- 若提供 `detail_description_json`，则直接使用
- 若未提供 `detail_description_json`，但提供了 `detail_text`，则自动包装为默认 JSON 结构
- 若两者都为空，则写入默认空数组或系统默认模板，具体以现有 Product 编辑页行为保持一致

默认包装结构建议如下：

```json
[
  {
    "type": "text",
    "title": "产品介绍",
    "content": "detail_text 的值"
  }
]
```

## 5.4 媒体识别规则

图片支持：

- `.jpg`
- `.jpeg`
- `.png`
- `.gif`
- `.webp`

视频支持：

- `.mp4`
- `.mov`
- `.avi`
- `.mkv`

## 5.5 封面规则

- 优先取文件名包含 `_cover` 的第一张图片作为封面
- 若不存在 `_cover` 图片，则取排序后的第一张图片作为封面
- 若目录下不存在任何图片，则该条记录导入失败
- `cover_image_url` 同时保留在 `image_urls` 数组中

## 六、系统架构设计

## 6.1 总体架构

整体链路建议如下：

```text
管理端上传 ZIP
  -> 分片上传接口
  -> 后端合并 ZIP
  -> 创建导入任务记录
  -> Celery 投递导入任务
  -> Worker 解压并校验
  -> 解析 Excel 和素材目录
  -> 上传媒体到对象存储
  -> 写入 Product 数据
  -> 更新任务状态与明细
  -> 提供任务列表、详情、错误报告下载
```

## 6.2 技术选型

| 用途 | 技术方案 |
| --- | --- |
| Web API | FastAPI |
| ORM | Tortoise ORM |
| Excel 解析 | openpyxl |
| ZIP 处理 | Python zipfile |
| 异步任务 | Celery |
| 任务中间件 | Redis |
| 对象存储 | 七牛 Kodo，带本地兜底实现 |
| 前端上传 | 分片上传方案 |
| 错误报告导出 | XLSX 或 CSV |
| 配置管理 | pydantic-settings |
| 日志 | loguru |

## 6.3 关键设计原则

- 上传链路和导入链路分离
- 导入任务与行级明细持久化
- 对象存储能力统一抽象，不把七牛逻辑散落在业务层
- 单条失败不影响整批任务
- 所有可感知状态都以数据库任务记录为准
- 前端进度显示与后端任务真实状态同步

## 七、后端设计

## 7.1 数据模型设计

### 表一：product_import_task

建议字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | bigint | 主键 |
| `filename` | varchar | 原始 ZIP 文件名 |
| `storage_key` | varchar | ZIP 文件定位信息 |
| `status` | varchar | `pending/uploading/queued/running/success/partial_failed/failed/canceled` |
| `total_count` | int | 模板总记录数 |
| `processed_count` | int | 已处理数 |
| `success_count` | int | 成功数 |
| `failed_count` | int | 失败数 |
| `progress` | int | 百分比 |
| `import_strategy` | varchar | 导入策略，如新增模式 |
| `error_message` | text | 任务级错误摘要 |
| `result_summary` | json | 结果汇总 |
| `error_report_path` | varchar | 错误报告地址 |
| `created_by` | bigint | 发起人 |
| `started_at` | datetime | 开始时间 |
| `finished_at` | datetime | 完成时间 |

### 表二：product_import_task_item

建议字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | bigint | 主键 |
| `task_id` | bigint | 关联任务 |
| `row_no` | int | Excel 行号 |
| `product_name` | varchar | 好物名称 |
| `status` | varchar | `pending/success/failed/skipped` |
| `message` | text | 行级处理结果 |
| `category_name` | varchar | 分类名称快照 |
| `brand_name` | varchar | 品牌名称快照 |
| `product_id` | bigint | 成功创建后的好物 ID |
| `duplicate_hint` | bool | 是否疑似重复 |

## 7.2 接口设计

### 上传与任务接口

1. `POST /product/import/upload-init`
   - 初始化上传任务
   - 返回上传 ID、分片参数、任务 ID

2. `POST /product/import/upload-chunk`
   - 上传分片

3. `POST /product/import/upload-complete`
   - 合并分片
   - 校验 ZIP
   - 创建任务并投递 Celery

4. `GET /product/import/tasks`
   - 查询任务列表

5. `GET /product/import/task`
   - 查询单个任务详情

6. `GET /product/import/task/items`
   - 查询任务行级明细

7. `POST /product/import/task/retry`
   - 重试整个任务或仅重试失败项

8. `POST /product/import/task/cancel`
   - 取消任务

9. `GET /product/import/task/errors`
   - 下载错误报告

### 模板与示例接口

10. `GET /product/import/template`
    - 下载 Excel 模板

11. `GET /product/import/example`
    - 下载示例 ZIP

## 7.3 导入执行流程

### 步骤1：分片上传 ZIP

- 前端先初始化上传任务
- 按分片大小上传 ZIP 内容
- 服务端记录分片状态
- 所有分片上传完成后进行合并
- 合并完成后创建业务导入任务

### 步骤2：投递异步任务

- 将任务状态置为 `queued`
- 通过 Celery 投递到 Redis
- Worker 拉取任务并置为 `running`

### 步骤3：解压与安全校验

- 解压 ZIP 到临时目录
- 校验 ZIP 中是否存在 `product.xlsx`
- 校验总文件数、总大小、单文件大小
- 拒绝非法路径、空文件、异常结构

### 步骤4：解析模板

- 使用 openpyxl 读取首个工作表
- 校验模板表头
- 跳过空行
- 构建分类、品牌、标签映射缓存

### 步骤5：行级预校验

- 校验名称、分类、品牌必填
- 校验品牌和分类归属关系
- 校验标签是否存在
- 校验状态与排序值合法性
- 校验 `detail_description_json` 是否为合法 JSON 数组
- 标记重复项提示，但不直接拦截导入

### 步骤6：扫描并上传素材

- 定位与 `name` 对应的素材目录
- 分类图片和视频
- 计算封面文件
- 通过统一存储服务上传文件
- 生成：
  - `cover_image_url`
  - `image_urls`
  - `video_urls`

### 步骤7：写入数据

- 构造符合 Product 创建契约的数据
- 写入 Product 主表
- 关联标签
- 更新任务明细状态

### 步骤8：生成结果与清理现场

- 汇总成功数、失败数、重复提示数
- 生成错误报告文件
- 更新主任务状态
- 清理临时解压目录和中间文件

## 7.4 导入策略设计

完整方案建议保留明确的导入策略字段，但首个落地策略只启用一种：

- `create_only`：只新增，不覆盖

未来可扩展：

- `skip_duplicate`：遇到重复直接跳过
- `replace_duplicate`：显式确认后覆盖

## 7.5 存储服务设计

建议抽象统一接口：

```python
class StorageService:
    async def upload_file(self, local_path: str, object_key: str) -> str:
        ...

    async def delete_file(self, object_key: str) -> None:
        ...
```

建议实现：

- `QiniuStorageService`：生产环境
- `LocalStorageService`：本地开发和测试环境

建议对象路径规则：

- `product-import/raw/{task_id}/source.zip`
- `products/{product_name}/{original_filename}`
- `product-import/error-report/{task_id}.xlsx`

## 八、前端设计

## 8.1 上传页面能力

- 分片上传 ZIP
- 续传已中断文件
- 上传进度显示
- 上传前校验文件类型和大小
- 上传后自动跳转任务详情或任务中心

## 8.2 任务中心能力

- 任务状态筛选
- 任务列表分页
- 任务进度条
- 任务结果摘要
- 错误报告下载
- 行级失败明细查看
- 整体重试和失败项重试
- 取消任务

## 8.3 页面交互建议

- 上传成功后立即显示任务已入队提示
- 运行中任务支持轮询或短间隔刷新
- 失败任务给出明确错误入口，不把错误只写在 toast 中
- 详情页支持展示模板错误、素材错误、数据错误三个维度

## 8.4 API 管理建议

管理端接口仍建议集中在 [web/src/api/index.js](web/src/api/index.js) 中维护，保持与现有管理端结构一致。

## 九、权限与菜单设计

## 9.1 菜单项

建议补齐以下菜单：

- `批量中心`
- `好物批量导入`
- `导入任务记录`

## 9.2 权限点

建议新增以下权限点：

- `post/api/v1/product/import/upload-init`
- `post/api/v1/product/import/upload-chunk`
- `post/api/v1/product/import/upload-complete`
- `get/api/v1/product/import/tasks`
- `get/api/v1/product/import/task`
- `get/api/v1/product/import/task/items`
- `get/api/v1/product/import/task/errors`
- `post/api/v1/product/import/task/retry`
- `post/api/v1/product/import/task/cancel`
- `get/api/v1/product/import/template`
- `get/api/v1/product/import/example`

## 十、配置与部署

## 10.1 Nginx 配置

建议补充：

```nginx
client_max_body_size 220m;
proxy_read_timeout 600s;
proxy_send_timeout 600s;
```

## 10.2 应用配置项

建议新增：

| 配置项 | 说明 |
| --- | --- |
| `PRODUCT_IMPORT_MAX_FILE_SIZE` | ZIP 最大文件大小 |
| `PRODUCT_IMPORT_TMP_DIR` | 导入临时目录 |
| `PRODUCT_IMPORT_CHUNK_SIZE` | 分片大小 |
| `PRODUCT_IMPORT_MAX_CONCURRENCY` | 任务并发上限 |
| `PRODUCT_IMPORT_MAX_WORKERS` | 媒体上传并发数 |
| `STORAGE_PROVIDER` | `local` 或 `qiniu` |
| `QINIU_ACCESS_KEY` | 七牛配置 |
| `QINIU_SECRET_KEY` | 七牛配置 |
| `QINIU_BUCKET` | 七牛配置 |
| `QINIU_DOMAIN` | 七牛域名 |
| `REDIS_URL` | Redis 连接地址 |
| `CELERY_BROKER_URL` | Celery broker |
| `CELERY_RESULT_BACKEND` | Celery result backend |

## 10.3 依赖建议

建议新增依赖：

- 七牛 SDK
- Celery
- Redis 客户端
- 前端分片上传依赖

不建议新增：

- pandas

原因是当前模板解析场景由 openpyxl 足够支撑，额外引入 pandas 收益有限。

## 十一、风险与控制措施

| 风险 | 说明 | 控制措施 |
| --- | --- | --- |
| 大文件上传失败 | 网络抖动、代理超时 | 分片上传、断点续传、Nginx 超时配置 |
| 任务丢失 | 仅依赖 Web 进程执行 | 使用 Celery + Redis |
| 数据写入不一致 | 行级失败中断整批 | 行级明细、逐条处理、错误报告 |
| 媒体上传失败 | 网络或对象存储异常 | 上传重试、失败记录、任务重试 |
| 模板错误频发 | 用户手工维护表格容易出错 | 模板下载、示例包、预校验、错误定位 |
| 菜单扩展性不足 | 后续更多批量场景接入困难 | 独立一级菜单“批量中心” |

## 十二、实施计划

### Phase1
- 完成对象存储适配层
- 完成单文件上传能力替换 mock 上传地址
- 完成 Redis、Celery、基础任务链路接入
- 完成导入任务表与明细表

### Phase2
- 完成 ZIP 分片上传、断点续传、分片合并
- 完成模板下载、示例 ZIP 下载
- 完成导入主流程、预校验、错误报告生成

### Phase3
- 完成批量中心菜单和管理端页面
- 完成任务中心、详情页、重试与取消
- 完成与现有好物管理页联动

### 验收标准

- 能成功上传并导入一个 200MB 以内的 ZIP 包
- 能在任务中心查看准确的状态、进度、成功数、失败数
- 能下载错误报告并定位到具体行
- 能重试失败任务或失败项
- 能在对象存储中正确生成媒体文件
- 能在好物管理页查询到导入结果
- 菜单、权限、角色授权链路完整可用

## 十三、最终结论

本方案建议以“批量中心”作为完整产品化落点，采用“分片上传 + Celery + Redis + 统一对象存储 + 任务中心”的总体架构，一次性补齐批量导入系统的核心能力。这样既能满足当前好物导入需求，也能为后续品牌、标签、分类等批量能力复用同一平台提供基础。