from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "api" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "created_at" TIMESTAMP NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "path" VARCHAR(100) NOT NULL  /* API路径 */,
    "method" VARCHAR(6) NOT NULL  /* 请求方法 */,
    "summary" VARCHAR(500) NOT NULL  /* 请求简介 */,
    "tags" VARCHAR(100) NOT NULL  /* API标签 */
);
CREATE INDEX IF NOT EXISTS "idx_api_created_78d19f" ON "api" ("created_at");
CREATE INDEX IF NOT EXISTS "idx_api_updated_643c8b" ON "api" ("updated_at");
CREATE INDEX IF NOT EXISTS "idx_api_path_9ed611" ON "api" ("path");
CREATE INDEX IF NOT EXISTS "idx_api_method_a46dfb" ON "api" ("method");
CREATE INDEX IF NOT EXISTS "idx_api_summary_400f73" ON "api" ("summary");
CREATE INDEX IF NOT EXISTS "idx_api_tags_04ae27" ON "api" ("tags");
CREATE TABLE IF NOT EXISTS "auditlog" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "created_at" TIMESTAMP NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "user_id" INT NOT NULL  /* 用户ID */,
    "username" VARCHAR(64) NOT NULL  DEFAULT '' /* 用户名称 */,
    "module" VARCHAR(64) NOT NULL  DEFAULT '' /* 功能模块 */,
    "summary" VARCHAR(128) NOT NULL  DEFAULT '' /* 请求描述 */,
    "method" VARCHAR(10) NOT NULL  DEFAULT '' /* 请求方法 */,
    "path" VARCHAR(255) NOT NULL  DEFAULT '' /* 请求路径 */,
    "status" INT NOT NULL  DEFAULT -1 /* 状态码 */,
    "response_time" INT NOT NULL  DEFAULT 0 /* 响应时间(单位ms) */,
    "request_args" JSON   /* 请求参数 */,
    "response_body" JSON   /* 返回数据 */
);
CREATE INDEX IF NOT EXISTS "idx_auditlog_created_cc33d0" ON "auditlog" ("created_at");
CREATE INDEX IF NOT EXISTS "idx_auditlog_updated_2f871f" ON "auditlog" ("updated_at");
CREATE INDEX IF NOT EXISTS "idx_auditlog_user_id_4b93fa" ON "auditlog" ("user_id");
CREATE INDEX IF NOT EXISTS "idx_auditlog_usernam_b187b3" ON "auditlog" ("username");
CREATE INDEX IF NOT EXISTS "idx_auditlog_module_04058b" ON "auditlog" ("module");
CREATE INDEX IF NOT EXISTS "idx_auditlog_summary_3e27da" ON "auditlog" ("summary");
CREATE INDEX IF NOT EXISTS "idx_auditlog_method_4270a2" ON "auditlog" ("method");
CREATE INDEX IF NOT EXISTS "idx_auditlog_path_b99502" ON "auditlog" ("path");
CREATE INDEX IF NOT EXISTS "idx_auditlog_status_2a72d2" ON "auditlog" ("status");
CREATE INDEX IF NOT EXISTS "idx_auditlog_respons_8caa87" ON "auditlog" ("response_time");
CREATE TABLE IF NOT EXISTS "banner" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "created_at" TIMESTAMP NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "content" VARCHAR(255) NOT NULL  /* 横幅内容 */,
    "note" VARCHAR(255)   /* 活动备注 */,
    "priority" INT NOT NULL  DEFAULT 0 /* 优先级 */,
    "link_url" VARCHAR(500)   /* 跳转路径 */,
    "click_count" INT NOT NULL  DEFAULT 0 /* 点击量 */,
    "is_active" INT NOT NULL  DEFAULT 1 /* 是否启用 */
);
CREATE INDEX IF NOT EXISTS "idx_banner_created_423764" ON "banner" ("created_at");
CREATE INDEX IF NOT EXISTS "idx_banner_updated_d2df13" ON "banner" ("updated_at");
CREATE INDEX IF NOT EXISTS "idx_banner_priorit_aabc85" ON "banner" ("priority");
CREATE INDEX IF NOT EXISTS "idx_banner_click_c_516653" ON "banner" ("click_count");
CREATE INDEX IF NOT EXISTS "idx_banner_is_acti_40ea0b" ON "banner" ("is_active");
CREATE TABLE IF NOT EXISTS "brand" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "created_at" TIMESTAMP NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "name" VARCHAR(100) NOT NULL  /* 品牌名称 */,
    "desc" VARCHAR(255)   /* 品牌描述 */,
    "search_count" INT NOT NULL  DEFAULT 0 /* 搜索次数 */,
    "order" INT NOT NULL  DEFAULT 0 /* 排序 */,
    "is_active" INT NOT NULL  DEFAULT 1 /* 是否启用 */
);
CREATE INDEX IF NOT EXISTS "idx_brand_created_882788" ON "brand" ("created_at");
CREATE INDEX IF NOT EXISTS "idx_brand_updated_959589" ON "brand" ("updated_at");
CREATE INDEX IF NOT EXISTS "idx_brand_name_c4e2df" ON "brand" ("name");
CREATE INDEX IF NOT EXISTS "idx_brand_search__39fa28" ON "brand" ("search_count");
CREATE INDEX IF NOT EXISTS "idx_brand_order_0a0d90" ON "brand" ("order");
CREATE INDEX IF NOT EXISTS "idx_brand_is_acti_c5b780" ON "brand" ("is_active");
CREATE TABLE IF NOT EXISTS "category" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "created_at" TIMESTAMP NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "name" VARCHAR(50) NOT NULL UNIQUE /* 类目名称 */,
    "desc" VARCHAR(255)   /* 类目描述 */,
    "order" INT NOT NULL  DEFAULT 0 /* 排序 */,
    "is_active" INT NOT NULL  DEFAULT 1 /* 是否启用 */
);
CREATE INDEX IF NOT EXISTS "idx_category_created_1d8a13" ON "category" ("created_at");
CREATE INDEX IF NOT EXISTS "idx_category_updated_446ede" ON "category" ("updated_at");
CREATE INDEX IF NOT EXISTS "idx_category_name_8b0cb9" ON "category" ("name");
CREATE INDEX IF NOT EXISTS "idx_category_order_ebae39" ON "category" ("order");
CREATE INDEX IF NOT EXISTS "idx_category_is_acti_16ce8c" ON "category" ("is_active");
CREATE TABLE IF NOT EXISTS "contact" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "created_at" TIMESTAMP NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "platform" VARCHAR(50) NOT NULL  /* 平台标识 */,
    "display_name" VARCHAR(100) NOT NULL  /* 展示名称 */,
    "contact_type" VARCHAR(30)   /* 联系方式类型 */,
    "contact_value" VARCHAR(255)   /* 联系方式值 */,
    "link_url" VARCHAR(500)   /* 跳转链接 */,
    "qr_image_url" VARCHAR(500)   /* 二维码图片 */,
    "order" INT NOT NULL  DEFAULT 0 /* 排序 */,
    "is_active" INT NOT NULL  DEFAULT 1 /* 是否启用 */
);
CREATE INDEX IF NOT EXISTS "idx_contact_created_edee29" ON "contact" ("created_at");
CREATE INDEX IF NOT EXISTS "idx_contact_updated_b40825" ON "contact" ("updated_at");
CREATE INDEX IF NOT EXISTS "idx_contact_platfor_0b6de8" ON "contact" ("platform");
CREATE INDEX IF NOT EXISTS "idx_contact_display_f0b8bd" ON "contact" ("display_name");
CREATE INDEX IF NOT EXISTS "idx_contact_contact_1715cc" ON "contact" ("contact_type");
CREATE INDEX IF NOT EXISTS "idx_contact_order_ea68b2" ON "contact" ("order");
CREATE INDEX IF NOT EXISTS "idx_contact_is_acti_87f467" ON "contact" ("is_active");
CREATE TABLE IF NOT EXISTS "dept" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "created_at" TIMESTAMP NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "name" VARCHAR(20) NOT NULL UNIQUE /* 部门名称 */,
    "desc" VARCHAR(500)   /* 备注 */,
    "is_deleted" INT NOT NULL  DEFAULT 0 /* 软删除标记 */,
    "order" INT NOT NULL  DEFAULT 0 /* 排序 */,
    "parent_id" INT NOT NULL  DEFAULT 0 /* 父部门ID */
);
CREATE INDEX IF NOT EXISTS "idx_dept_created_4b11cf" ON "dept" ("created_at");
CREATE INDEX IF NOT EXISTS "idx_dept_updated_0c0bd1" ON "dept" ("updated_at");
CREATE INDEX IF NOT EXISTS "idx_dept_name_c2b9da" ON "dept" ("name");
CREATE INDEX IF NOT EXISTS "idx_dept_is_dele_466228" ON "dept" ("is_deleted");
CREATE INDEX IF NOT EXISTS "idx_dept_order_ddabe1" ON "dept" ("order");
CREATE INDEX IF NOT EXISTS "idx_dept_parent__a71a57" ON "dept" ("parent_id");
CREATE TABLE IF NOT EXISTS "deptclosure" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "created_at" TIMESTAMP NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "ancestor" INT NOT NULL  /* 父代 */,
    "descendant" INT NOT NULL  /* 子代 */,
    "level" INT NOT NULL  DEFAULT 0 /* 深度 */
);
CREATE INDEX IF NOT EXISTS "idx_deptclosure_created_96f6ef" ON "deptclosure" ("created_at");
CREATE INDEX IF NOT EXISTS "idx_deptclosure_updated_41fc08" ON "deptclosure" ("updated_at");
CREATE INDEX IF NOT EXISTS "idx_deptclosure_ancesto_fbc4ce" ON "deptclosure" ("ancestor");
CREATE INDEX IF NOT EXISTS "idx_deptclosure_descend_2ae8b1" ON "deptclosure" ("descendant");
CREATE INDEX IF NOT EXISTS "idx_deptclosure_level_ae16b2" ON "deptclosure" ("level");
CREATE TABLE IF NOT EXISTS "menu" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "created_at" TIMESTAMP NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "name" VARCHAR(20) NOT NULL  /* 菜单名称 */,
    "remark" JSON   /* 保留字段 */,
    "menu_type" VARCHAR(7)   /* 菜单类型 */,
    "icon" VARCHAR(100)   /* 菜单图标 */,
    "path" VARCHAR(100) NOT NULL  /* 菜单路径 */,
    "order" INT NOT NULL  DEFAULT 0 /* 排序 */,
    "parent_id" INT NOT NULL  DEFAULT 0 /* 父菜单ID */,
    "is_hidden" INT NOT NULL  DEFAULT 0 /* 是否隐藏 */,
    "component" VARCHAR(100) NOT NULL  /* 组件 */,
    "keepalive" INT NOT NULL  DEFAULT 1 /* 存活 */,
    "redirect" VARCHAR(100)   /* 重定向 */
);
CREATE INDEX IF NOT EXISTS "idx_menu_created_b6922b" ON "menu" ("created_at");
CREATE INDEX IF NOT EXISTS "idx_menu_updated_e6b0a1" ON "menu" ("updated_at");
CREATE INDEX IF NOT EXISTS "idx_menu_name_b9b853" ON "menu" ("name");
CREATE INDEX IF NOT EXISTS "idx_menu_path_bf95b2" ON "menu" ("path");
CREATE INDEX IF NOT EXISTS "idx_menu_order_606068" ON "menu" ("order");
CREATE INDEX IF NOT EXISTS "idx_menu_parent__bebd15" ON "menu" ("parent_id");
CREATE TABLE IF NOT EXISTS "product" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "created_at" TIMESTAMP NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "category_id" BIGINT NOT NULL  /* 类目ID */,
    "brand_id" BIGINT NOT NULL  /* 品牌ID */,
    "name" VARCHAR(100) NOT NULL  /* 好物名称 */,
    "product_code" VARCHAR(64)   /* 好物识别码 */,
    "desc" VARCHAR(255)   /* 好物简介 */,
    "detail_description" JSON NOT NULL  /* 结构化详情 */,
    "cover_image_url" VARCHAR(500) NOT NULL  /* 封面图 */,
    "image_urls" JSON NOT NULL  /* 图片列表 */,
    "video_urls" JSON NOT NULL  /* 视频列表 */,
    "click_count" INT NOT NULL  DEFAULT 0 /* 点击量 */,
    "status" INT NOT NULL  DEFAULT 1 /* 是否上架 */,
    "order" INT NOT NULL  DEFAULT 0 /* 排序 */
);
CREATE INDEX IF NOT EXISTS "idx_product_created_9eb6f4" ON "product" ("created_at");
CREATE INDEX IF NOT EXISTS "idx_product_updated_2f7d71" ON "product" ("updated_at");
CREATE INDEX IF NOT EXISTS "idx_product_categor_2b519b" ON "product" ("category_id");
CREATE INDEX IF NOT EXISTS "idx_product_brand_i_fbdc11" ON "product" ("brand_id");
CREATE INDEX IF NOT EXISTS "idx_product_name_683352" ON "product" ("name");
CREATE INDEX IF NOT EXISTS "idx_product_product_e35c67" ON "product" ("product_code");
CREATE INDEX IF NOT EXISTS "idx_product_click_c_abe3fc" ON "product" ("click_count");
CREATE INDEX IF NOT EXISTS "idx_product_status_cb6e1f" ON "product" ("status");
CREATE INDEX IF NOT EXISTS "idx_product_order_2e8699" ON "product" ("order");
CREATE TABLE IF NOT EXISTS "product_import_task" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "created_at" TIMESTAMP NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "filename" VARCHAR(255) NOT NULL  /* 原始ZIP文件名 */,
    "storage_key" VARCHAR(500) NOT NULL  /* 源文件存储定位信息 */,
    "status" VARCHAR(14) NOT NULL  DEFAULT 'pending' /* 任务状态 */,
    "total_count" INT NOT NULL  DEFAULT 0 /* 模板总记录数 */,
    "processed_count" INT NOT NULL  DEFAULT 0 /* 已处理数量 */,
    "success_count" INT NOT NULL  DEFAULT 0 /* 成功数量 */,
    "failed_count" INT NOT NULL  DEFAULT 0 /* 失败数量 */,
    "progress" INT NOT NULL  DEFAULT 0 /* 进度百分比 */,
    "import_strategy" VARCHAR(11) NOT NULL  DEFAULT 'create_only' /* 导入策略 */,
    "error_message" TEXT   /* 任务级错误摘要 */,
    "result_summary" JSON NOT NULL  /* 结果汇总 */,
    "error_report_path" VARCHAR(500)   /* 错误报告路径 */,
    "created_by" BIGINT NOT NULL  /* 发起人ID */,
    "started_at" TIMESTAMP   /* 开始时间 */,
    "finished_at" TIMESTAMP   /* 完成时间 */
);
CREATE INDEX IF NOT EXISTS "idx_product_imp_created_b46973" ON "product_import_task" ("created_at");
CREATE INDEX IF NOT EXISTS "idx_product_imp_updated_dddb16" ON "product_import_task" ("updated_at");
CREATE INDEX IF NOT EXISTS "idx_product_imp_created_dac883" ON "product_import_task" ("created_by");
CREATE INDEX IF NOT EXISTS "idx_product_imp_started_d64f90" ON "product_import_task" ("started_at");
CREATE INDEX IF NOT EXISTS "idx_product_imp_finishe_12ad27" ON "product_import_task" ("finished_at");
CREATE TABLE IF NOT EXISTS "product_import_task_item" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "created_at" TIMESTAMP NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "row_no" INT NOT NULL  /* Excel行号 */,
    "product_name" VARCHAR(100) NOT NULL  /* 好物名称 */,
    "status" VARCHAR(7) NOT NULL  DEFAULT 'pending' /* 行级状态 */,
    "message" TEXT   /* 处理结果信息 */,
    "category_name" VARCHAR(100)   /* 分类名称快照 */,
    "brand_name" VARCHAR(100)   /* 品牌名称快照 */,
    "product_id" BIGINT   /* 创建成功后的好物ID */,
    "duplicate_hint" INT NOT NULL  DEFAULT 0 /* 是否疑似重复 */,
    "task_id" BIGINT NOT NULL REFERENCES "product_import_task" ("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "idx_product_imp_created_5ab24c" ON "product_import_task_item" ("created_at");
CREATE INDEX IF NOT EXISTS "idx_product_imp_updated_841a59" ON "product_import_task_item" ("updated_at");
CREATE INDEX IF NOT EXISTS "idx_product_imp_row_no_03937c" ON "product_import_task_item" ("row_no");
CREATE INDEX IF NOT EXISTS "idx_product_imp_product_7fdb89" ON "product_import_task_item" ("product_name");
CREATE INDEX IF NOT EXISTS "idx_product_imp_categor_7b371b" ON "product_import_task_item" ("category_name");
CREATE INDEX IF NOT EXISTS "idx_product_imp_brand_n_56a180" ON "product_import_task_item" ("brand_name");
CREATE INDEX IF NOT EXISTS "idx_product_imp_product_500481" ON "product_import_task_item" ("product_id");
CREATE INDEX IF NOT EXISTS "idx_product_imp_duplica_95ee6a" ON "product_import_task_item" ("duplicate_hint");
CREATE TABLE IF NOT EXISTS "role" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "created_at" TIMESTAMP NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "name" VARCHAR(20) NOT NULL UNIQUE /* 角色名称 */,
    "desc" VARCHAR(500)   /* 角色描述 */
);
CREATE INDEX IF NOT EXISTS "idx_role_created_7f5f71" ON "role" ("created_at");
CREATE INDEX IF NOT EXISTS "idx_role_updated_5dd337" ON "role" ("updated_at");
CREATE INDEX IF NOT EXISTS "idx_role_name_e5618b" ON "role" ("name");
CREATE TABLE IF NOT EXISTS "site_visit" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "visitor_id" VARCHAR(64) NOT NULL  /* 访客标识 */,
    "path" VARCHAR(255) NOT NULL  DEFAULT '/' /* 访问路径 */,
    "region" VARCHAR(100) NOT NULL  DEFAULT '' /* 所属区域 */,
    "user_agent" VARCHAR(500) NOT NULL  DEFAULT '' /* 用户代理 */,
    "visited_at" TIMESTAMP NOT NULL  DEFAULT CURRENT_TIMESTAMP /* 访问时间 */
);
CREATE INDEX IF NOT EXISTS "idx_site_visit_visitor_9826af" ON "site_visit" ("visitor_id");
CREATE INDEX IF NOT EXISTS "idx_site_visit_path_46ff76" ON "site_visit" ("path");
CREATE INDEX IF NOT EXISTS "idx_site_visit_region_e376d7" ON "site_visit" ("region");
CREATE INDEX IF NOT EXISTS "idx_site_visit_visited_ce9658" ON "site_visit" ("visited_at");
CREATE TABLE IF NOT EXISTS "tag" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "created_at" TIMESTAMP NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "name" VARCHAR(100) NOT NULL UNIQUE /* 标签名称 */,
    "remark" VARCHAR(255)   /* 备注 */,
    "search_count" INT NOT NULL  DEFAULT 0 /* 检索次数 */,
    "sort" INT NOT NULL  DEFAULT 0 /* 排序 */,
    "is_active" INT NOT NULL  DEFAULT 1 /* 是否启用 */
);
CREATE INDEX IF NOT EXISTS "idx_tag_created_e4e466" ON "tag" ("created_at");
CREATE INDEX IF NOT EXISTS "idx_tag_updated_fb661e" ON "tag" ("updated_at");
CREATE INDEX IF NOT EXISTS "idx_tag_name_a7b9a6" ON "tag" ("name");
CREATE INDEX IF NOT EXISTS "idx_tag_search__566698" ON "tag" ("search_count");
CREATE INDEX IF NOT EXISTS "idx_tag_sort_73ff0f" ON "tag" ("sort");
CREATE INDEX IF NOT EXISTS "idx_tag_is_acti_50cf59" ON "tag" ("is_active");
CREATE TABLE IF NOT EXISTS "user" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "created_at" TIMESTAMP NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "username" VARCHAR(20) NOT NULL UNIQUE /* 用户名称 */,
    "alias" VARCHAR(30)   /* 姓名 */,
    "email" VARCHAR(255)  UNIQUE /* 邮箱 */,
    "phone" VARCHAR(20)   /* 电话 */,
    "password" VARCHAR(128)   /* 密码 */,
    "is_active" INT NOT NULL  DEFAULT 1 /* 是否激活 */,
    "is_superuser" INT NOT NULL  DEFAULT 0 /* 是否为超级管理员 */,
    "last_login" TIMESTAMP   /* 最后登录时间 */,
    "dept_id" INT   /* 部门ID */
);
CREATE INDEX IF NOT EXISTS "idx_user_created_b19d59" ON "user" ("created_at");
CREATE INDEX IF NOT EXISTS "idx_user_updated_dfdb43" ON "user" ("updated_at");
CREATE INDEX IF NOT EXISTS "idx_user_usernam_9987ab" ON "user" ("username");
CREATE INDEX IF NOT EXISTS "idx_user_alias_6f9868" ON "user" ("alias");
CREATE INDEX IF NOT EXISTS "idx_user_email_1b4f1c" ON "user" ("email");
CREATE INDEX IF NOT EXISTS "idx_user_phone_4e3ecc" ON "user" ("phone");
CREATE INDEX IF NOT EXISTS "idx_user_is_acti_83722a" ON "user" ("is_active");
CREATE INDEX IF NOT EXISTS "idx_user_is_supe_b8a218" ON "user" ("is_superuser");
CREATE INDEX IF NOT EXISTS "idx_user_last_lo_af118a" ON "user" ("last_login");
CREATE INDEX IF NOT EXISTS "idx_user_dept_id_d4490b" ON "user" ("dept_id");
CREATE TABLE IF NOT EXISTS "aerich" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "version" VARCHAR(255) NOT NULL,
    "app" VARCHAR(100) NOT NULL,
    "content" JSON NOT NULL
);
CREATE TABLE IF NOT EXISTS "brand_hot_category" (
    "brand_id" BIGINT NOT NULL REFERENCES "brand" ("id") ON DELETE CASCADE,
    "category_id" BIGINT NOT NULL REFERENCES "category" ("id") ON DELETE CASCADE
);
CREATE UNIQUE INDEX IF NOT EXISTS "uidx_brand_hot_c_brand_i_b9fb73" ON "brand_hot_category" ("brand_id", "category_id");
CREATE TABLE IF NOT EXISTS "brand_category" (
    "brand_id" BIGINT NOT NULL REFERENCES "brand" ("id") ON DELETE CASCADE,
    "category_id" BIGINT NOT NULL REFERENCES "category" ("id") ON DELETE CASCADE
);
CREATE UNIQUE INDEX IF NOT EXISTS "uidx_brand_categ_brand_i_5563b7" ON "brand_category" ("brand_id", "category_id");
CREATE TABLE IF NOT EXISTS "category_hot_tag" (
    "category_id" BIGINT NOT NULL REFERENCES "category" ("id") ON DELETE CASCADE,
    "tag_id" BIGINT NOT NULL REFERENCES "tag" ("id") ON DELETE CASCADE
);
CREATE UNIQUE INDEX IF NOT EXISTS "uidx_category_ho_categor_eaab38" ON "category_hot_tag" ("category_id", "tag_id");
CREATE TABLE IF NOT EXISTS "product_tag" (
    "product_id" BIGINT NOT NULL REFERENCES "product" ("id") ON DELETE CASCADE,
    "tag_id" BIGINT NOT NULL REFERENCES "tag" ("id") ON DELETE CASCADE
);
CREATE UNIQUE INDEX IF NOT EXISTS "uidx_product_tag_product_1dd626" ON "product_tag" ("product_id", "tag_id");
CREATE TABLE IF NOT EXISTS "role_menu" (
    "role_id" BIGINT NOT NULL REFERENCES "role" ("id") ON DELETE CASCADE,
    "menu_id" BIGINT NOT NULL REFERENCES "menu" ("id") ON DELETE CASCADE
);
CREATE UNIQUE INDEX IF NOT EXISTS "uidx_role_menu_role_id_90801c" ON "role_menu" ("role_id", "menu_id");
CREATE TABLE IF NOT EXISTS "role_api" (
    "role_id" BIGINT NOT NULL REFERENCES "role" ("id") ON DELETE CASCADE,
    "api_id" BIGINT NOT NULL REFERENCES "api" ("id") ON DELETE CASCADE
);
CREATE UNIQUE INDEX IF NOT EXISTS "uidx_role_api_role_id_ba4286" ON "role_api" ("role_id", "api_id");
CREATE TABLE IF NOT EXISTS "user_role" (
    "user_id" BIGINT NOT NULL REFERENCES "user" ("id") ON DELETE CASCADE,
    "role_id" BIGINT NOT NULL REFERENCES "role" ("id") ON DELETE CASCADE
);
CREATE UNIQUE INDEX IF NOT EXISTS "uidx_user_role_user_id_d0bad3" ON "user_role" ("user_id", "role_id");"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """
