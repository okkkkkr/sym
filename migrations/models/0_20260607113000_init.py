from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
CREATE TABLE IF NOT EXISTS "api" (
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "path" VARCHAR(100) NOT NULL,
    "method" VARCHAR(6) NOT NULL,
    "summary" VARCHAR(500) NOT NULL,
    "tags" VARCHAR(100) NOT NULL
);
CREATE INDEX IF NOT EXISTS "idx_api_created_78d19f" ON "api" ("created_at");
CREATE INDEX IF NOT EXISTS "idx_api_updated_643c8b" ON "api" ("updated_at");
CREATE INDEX IF NOT EXISTS "idx_api_path_9ed611" ON "api" ("path");
CREATE INDEX IF NOT EXISTS "idx_api_method_a46dfb" ON "api" ("method");
CREATE INDEX IF NOT EXISTS "idx_api_summary_400f73" ON "api" ("summary");
CREATE INDEX IF NOT EXISTS "idx_api_tags_04ae27" ON "api" ("tags");
COMMENT ON COLUMN "api"."path" IS 'API路径';
COMMENT ON COLUMN "api"."method" IS '请求方法';
COMMENT ON COLUMN "api"."summary" IS '请求简介';
COMMENT ON COLUMN "api"."tags" IS 'API标签';
CREATE TABLE IF NOT EXISTS "auditlog" (
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "user_id" INT NOT NULL,
    "username" VARCHAR(64) NOT NULL  DEFAULT '',
    "module" VARCHAR(64) NOT NULL  DEFAULT '',
    "summary" VARCHAR(128) NOT NULL  DEFAULT '',
    "method" VARCHAR(10) NOT NULL  DEFAULT '',
    "path" VARCHAR(255) NOT NULL  DEFAULT '',
    "status" INT NOT NULL  DEFAULT -1,
    "response_time" INT NOT NULL  DEFAULT 0,
    "request_args" JSONB,
    "response_body" JSONB
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
COMMENT ON COLUMN "auditlog"."user_id" IS '用户ID';
COMMENT ON COLUMN "auditlog"."username" IS '用户名称';
COMMENT ON COLUMN "auditlog"."module" IS '功能模块';
COMMENT ON COLUMN "auditlog"."summary" IS '请求描述';
COMMENT ON COLUMN "auditlog"."method" IS '请求方法';
COMMENT ON COLUMN "auditlog"."path" IS '请求路径';
COMMENT ON COLUMN "auditlog"."status" IS '状态码';
COMMENT ON COLUMN "auditlog"."response_time" IS '响应时间(单位ms)';
COMMENT ON COLUMN "auditlog"."request_args" IS '请求参数';
COMMENT ON COLUMN "auditlog"."response_body" IS '返回数据';
CREATE TABLE IF NOT EXISTS "banner" (
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "content" VARCHAR(255) NOT NULL,
    "note" VARCHAR(255),
    "priority" INT,
    "link_url" VARCHAR(500),
    "click_count" INT NOT NULL  DEFAULT 0,
    "is_active" BOOL NOT NULL  DEFAULT True
);
CREATE INDEX IF NOT EXISTS "idx_banner_created_423764" ON "banner" ("created_at");
CREATE INDEX IF NOT EXISTS "idx_banner_updated_d2df13" ON "banner" ("updated_at");
CREATE INDEX IF NOT EXISTS "idx_banner_priorit_aabc85" ON "banner" ("priority");
CREATE INDEX IF NOT EXISTS "idx_banner_click_c_516653" ON "banner" ("click_count");
CREATE INDEX IF NOT EXISTS "idx_banner_is_acti_40ea0b" ON "banner" ("is_active");
COMMENT ON COLUMN "banner"."content" IS '横幅内容';
COMMENT ON COLUMN "banner"."note" IS '活动备注';
COMMENT ON COLUMN "banner"."priority" IS '优先级';
COMMENT ON COLUMN "banner"."link_url" IS '跳转路径';
COMMENT ON COLUMN "banner"."click_count" IS '点击量';
COMMENT ON COLUMN "banner"."is_active" IS '是否启用';
CREATE TABLE IF NOT EXISTS "brand" (
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "name" VARCHAR(100) NOT NULL,
    "desc" VARCHAR(255),
    "search_count" INT NOT NULL  DEFAULT 0,
    "order" INT,
    "is_active" BOOL NOT NULL  DEFAULT True
);
CREATE INDEX IF NOT EXISTS "idx_brand_created_882788" ON "brand" ("created_at");
CREATE INDEX IF NOT EXISTS "idx_brand_updated_959589" ON "brand" ("updated_at");
CREATE INDEX IF NOT EXISTS "idx_brand_name_c4e2df" ON "brand" ("name");
CREATE INDEX IF NOT EXISTS "idx_brand_search__39fa28" ON "brand" ("search_count");
CREATE INDEX IF NOT EXISTS "idx_brand_order_0a0d90" ON "brand" ("order");
CREATE INDEX IF NOT EXISTS "idx_brand_is_acti_c5b780" ON "brand" ("is_active");
COMMENT ON COLUMN "brand"."name" IS '品牌名称';
COMMENT ON COLUMN "brand"."desc" IS '品牌描述';
COMMENT ON COLUMN "brand"."search_count" IS '搜索次数';
COMMENT ON COLUMN "brand"."order" IS '排序';
COMMENT ON COLUMN "brand"."is_active" IS '是否启用';
CREATE TABLE IF NOT EXISTS "category" (
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "name" VARCHAR(50) NOT NULL UNIQUE,
    "desc" VARCHAR(255),
    "order" INT,
    "is_active" BOOL NOT NULL  DEFAULT True
);
CREATE INDEX IF NOT EXISTS "idx_category_created_1d8a13" ON "category" ("created_at");
CREATE INDEX IF NOT EXISTS "idx_category_updated_446ede" ON "category" ("updated_at");
CREATE INDEX IF NOT EXISTS "idx_category_name_8b0cb9" ON "category" ("name");
CREATE INDEX IF NOT EXISTS "idx_category_order_ebae39" ON "category" ("order");
CREATE INDEX IF NOT EXISTS "idx_category_is_acti_16ce8c" ON "category" ("is_active");
COMMENT ON COLUMN "category"."name" IS '类目名称';
COMMENT ON COLUMN "category"."desc" IS '类目描述';
COMMENT ON COLUMN "category"."order" IS '排序';
COMMENT ON COLUMN "category"."is_active" IS '是否启用';
CREATE TABLE IF NOT EXISTS "channel_visit" (
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "visitor_id" VARCHAR(64) NOT NULL,
    "platform_name_snapshot" VARCHAR(100) NOT NULL,
    "custom_name" VARCHAR(50) NOT NULL,
    "visited_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "idx_channel_vis_visitor_f7f4a6" ON "channel_visit" ("visitor_id");
CREATE INDEX IF NOT EXISTS "idx_channel_vis_custom__82ab2d" ON "channel_visit" ("custom_name");
CREATE INDEX IF NOT EXISTS "idx_channel_vis_visited_b8048b" ON "channel_visit" ("visited_at");
COMMENT ON COLUMN "channel_visit"."visitor_id" IS '访客标识';
COMMENT ON COLUMN "channel_visit"."platform_name_snapshot" IS '渠道名称快照';
COMMENT ON COLUMN "channel_visit"."custom_name" IS '自定义标识';
COMMENT ON COLUMN "channel_visit"."visited_at" IS '访问时间';
CREATE TABLE IF NOT EXISTS "channel_visit_dedup" (
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "visitor_id" VARCHAR(64) NOT NULL,
    "custom_name" VARCHAR(50) NOT NULL,
    "last_counted_at" TIMESTAMPTZ NOT NULL,
    CONSTRAINT "uid_channel_vis_visitor_3d5832" UNIQUE ("visitor_id", "custom_name")
);
CREATE INDEX IF NOT EXISTS "idx_channel_vis_visitor_dac2c5" ON "channel_visit_dedup" ("visitor_id");
CREATE INDEX IF NOT EXISTS "idx_channel_vis_custom__bfc7c8" ON "channel_visit_dedup" ("custom_name");
CREATE INDEX IF NOT EXISTS "idx_channel_vis_last_co_c81d7c" ON "channel_visit_dedup" ("last_counted_at");
COMMENT ON COLUMN "channel_visit_dedup"."visitor_id" IS '访客标识';
COMMENT ON COLUMN "channel_visit_dedup"."custom_name" IS '自定义标识';
COMMENT ON COLUMN "channel_visit_dedup"."last_counted_at" IS '最后计数时间';
CREATE TABLE IF NOT EXISTS "contact" (
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "platform" VARCHAR(50) NOT NULL,
    "display_name" VARCHAR(100) NOT NULL,
    "contact_type" VARCHAR(30),
    "contact_value" VARCHAR(255),
    "link_url" VARCHAR(500),
    "qr_image_url" VARCHAR(500),
    "order" INT,
    "is_active" BOOL NOT NULL  DEFAULT True,
    "is_deleted" BOOL NOT NULL  DEFAULT False,
    "deleted_at" TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS "idx_contact_created_edee29" ON "contact" ("created_at");
CREATE INDEX IF NOT EXISTS "idx_contact_updated_b40825" ON "contact" ("updated_at");
CREATE INDEX IF NOT EXISTS "idx_contact_platfor_0b6de8" ON "contact" ("platform");
CREATE INDEX IF NOT EXISTS "idx_contact_display_f0b8bd" ON "contact" ("display_name");
CREATE INDEX IF NOT EXISTS "idx_contact_contact_1715cc" ON "contact" ("contact_type");
CREATE INDEX IF NOT EXISTS "idx_contact_order_ea68b2" ON "contact" ("order");
CREATE INDEX IF NOT EXISTS "idx_contact_is_acti_87f467" ON "contact" ("is_active");
CREATE INDEX IF NOT EXISTS "idx_contact_is_dele_808a7b" ON "contact" ("is_deleted");
CREATE INDEX IF NOT EXISTS "idx_contact_deleted_55743f" ON "contact" ("deleted_at");
COMMENT ON COLUMN "contact"."platform" IS '平台标识';
COMMENT ON COLUMN "contact"."display_name" IS '展示名称';
COMMENT ON COLUMN "contact"."contact_type" IS '联系方式类型';
COMMENT ON COLUMN "contact"."contact_value" IS '联系方式值';
COMMENT ON COLUMN "contact"."link_url" IS '跳转链接';
COMMENT ON COLUMN "contact"."qr_image_url" IS '二维码图片';
COMMENT ON COLUMN "contact"."order" IS '排序';
COMMENT ON COLUMN "contact"."is_active" IS '是否启用';
COMMENT ON COLUMN "contact"."is_deleted" IS '是否已删除';
COMMENT ON COLUMN "contact"."deleted_at" IS '删除时间';
CREATE TABLE IF NOT EXISTS "contact_click" (
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "visitor_id" VARCHAR(64) NOT NULL,
    "contact_id" BIGINT NOT NULL,
    "platform_snapshot" VARCHAR(50) NOT NULL,
    "display_name_snapshot" VARCHAR(100) NOT NULL,
    "contact_type_snapshot" VARCHAR(30),
    "contact_value_snapshot" VARCHAR(255),
    "link_url_snapshot" VARCHAR(500),
    "clicked_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "idx_contact_cli_visitor_c4d239" ON "contact_click" ("visitor_id");
CREATE INDEX IF NOT EXISTS "idx_contact_cli_contact_37c284" ON "contact_click" ("contact_id");
CREATE INDEX IF NOT EXISTS "idx_contact_cli_contact_a9c0ed" ON "contact_click" ("contact_type_snapshot");
CREATE INDEX IF NOT EXISTS "idx_contact_cli_clicked_e595ee" ON "contact_click" ("clicked_at");
COMMENT ON COLUMN "contact_click"."visitor_id" IS '访客标识';
COMMENT ON COLUMN "contact_click"."contact_id" IS '联系方式ID';
COMMENT ON COLUMN "contact_click"."platform_snapshot" IS '平台标识快照';
COMMENT ON COLUMN "contact_click"."display_name_snapshot" IS '展示名称快照';
COMMENT ON COLUMN "contact_click"."contact_type_snapshot" IS '联系方式类型快照';
COMMENT ON COLUMN "contact_click"."contact_value_snapshot" IS '联系方式值快照';
COMMENT ON COLUMN "contact_click"."link_url_snapshot" IS '跳转链接快照';
COMMENT ON COLUMN "contact_click"."clicked_at" IS '点击时间';
CREATE TABLE IF NOT EXISTS "contact_click_dedup" (
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "visitor_id" VARCHAR(64) NOT NULL,
    "contact_id" BIGINT NOT NULL,
    "last_counted_at" TIMESTAMPTZ NOT NULL,
    CONSTRAINT "uid_contact_cli_visitor_d0c8fc" UNIQUE ("visitor_id", "contact_id")
);
CREATE INDEX IF NOT EXISTS "idx_contact_cli_visitor_f9abae" ON "contact_click_dedup" ("visitor_id");
CREATE INDEX IF NOT EXISTS "idx_contact_cli_contact_cdcbe0" ON "contact_click_dedup" ("contact_id");
CREATE INDEX IF NOT EXISTS "idx_contact_cli_last_co_e39021" ON "contact_click_dedup" ("last_counted_at");
COMMENT ON COLUMN "contact_click_dedup"."visitor_id" IS '访客标识';
COMMENT ON COLUMN "contact_click_dedup"."contact_id" IS '联系方式ID';
COMMENT ON COLUMN "contact_click_dedup"."last_counted_at" IS '最后计数时间';
CREATE TABLE IF NOT EXISTS "dept" (
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "name" VARCHAR(20) NOT NULL UNIQUE,
    "desc" VARCHAR(500),
    "is_deleted" BOOL NOT NULL  DEFAULT False,
    "order" INT NOT NULL  DEFAULT 0,
    "parent_id" INT NOT NULL  DEFAULT 0
);
CREATE INDEX IF NOT EXISTS "idx_dept_created_4b11cf" ON "dept" ("created_at");
CREATE INDEX IF NOT EXISTS "idx_dept_updated_0c0bd1" ON "dept" ("updated_at");
CREATE INDEX IF NOT EXISTS "idx_dept_name_c2b9da" ON "dept" ("name");
CREATE INDEX IF NOT EXISTS "idx_dept_is_dele_466228" ON "dept" ("is_deleted");
CREATE INDEX IF NOT EXISTS "idx_dept_order_ddabe1" ON "dept" ("order");
CREATE INDEX IF NOT EXISTS "idx_dept_parent__a71a57" ON "dept" ("parent_id");
COMMENT ON COLUMN "dept"."name" IS '部门名称';
COMMENT ON COLUMN "dept"."desc" IS '备注';
COMMENT ON COLUMN "dept"."is_deleted" IS '软删除标记';
COMMENT ON COLUMN "dept"."order" IS '排序';
COMMENT ON COLUMN "dept"."parent_id" IS '父部门ID';
CREATE TABLE IF NOT EXISTS "deptclosure" (
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "ancestor" INT NOT NULL,
    "descendant" INT NOT NULL,
    "level" INT NOT NULL  DEFAULT 0
);
CREATE INDEX IF NOT EXISTS "idx_deptclosure_created_96f6ef" ON "deptclosure" ("created_at");
CREATE INDEX IF NOT EXISTS "idx_deptclosure_updated_41fc08" ON "deptclosure" ("updated_at");
CREATE INDEX IF NOT EXISTS "idx_deptclosure_ancesto_fbc4ce" ON "deptclosure" ("ancestor");
CREATE INDEX IF NOT EXISTS "idx_deptclosure_descend_2ae8b1" ON "deptclosure" ("descendant");
CREATE INDEX IF NOT EXISTS "idx_deptclosure_level_ae16b2" ON "deptclosure" ("level");
COMMENT ON COLUMN "deptclosure"."ancestor" IS '父代';
COMMENT ON COLUMN "deptclosure"."descendant" IS '子代';
COMMENT ON COLUMN "deptclosure"."level" IS '深度';
CREATE TABLE IF NOT EXISTS "home_layout" (
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "page_code" VARCHAR(50) NOT NULL  DEFAULT 'home',
    "status" VARCHAR(20) NOT NULL  DEFAULT 'draft',
    "version" INT NOT NULL  DEFAULT 0,
    "is_current" BOOL NOT NULL  DEFAULT False,
    "common_config" JSONB NOT NULL,
    "published_at" TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS "idx_home_layout_created_b9dda6" ON "home_layout" ("created_at");
CREATE INDEX IF NOT EXISTS "idx_home_layout_updated_58fda5" ON "home_layout" ("updated_at");
CREATE INDEX IF NOT EXISTS "idx_home_layout_page_co_735ee8" ON "home_layout" ("page_code");
CREATE INDEX IF NOT EXISTS "idx_home_layout_status_530117" ON "home_layout" ("status");
CREATE INDEX IF NOT EXISTS "idx_home_layout_version_b82634" ON "home_layout" ("version");
CREATE INDEX IF NOT EXISTS "idx_home_layout_is_curr_c97718" ON "home_layout" ("is_current");
CREATE INDEX IF NOT EXISTS "idx_home_layout_publish_4f8f7f" ON "home_layout" ("published_at");
COMMENT ON COLUMN "home_layout"."page_code" IS '页面标识';
COMMENT ON COLUMN "home_layout"."status" IS '状态';
COMMENT ON COLUMN "home_layout"."version" IS '版本号';
COMMENT ON COLUMN "home_layout"."is_current" IS '是否当前生效版本';
COMMENT ON COLUMN "home_layout"."common_config" IS '公共配置';
COMMENT ON COLUMN "home_layout"."published_at" IS '发布时间';
CREATE TABLE IF NOT EXISTS "home_layout_module" (
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "type" VARCHAR(50) NOT NULL,
    "sort" INT NOT NULL  DEFAULT 0,
    "is_enabled" BOOL NOT NULL  DEFAULT True,
    "title" VARCHAR(255) NOT NULL  DEFAULT '',
    "action" JSONB NOT NULL,
    "config" JSONB NOT NULL,
    "layout_id" BIGINT NOT NULL REFERENCES "home_layout" ("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "idx_home_layout_created_13d6bc" ON "home_layout_module" ("created_at");
CREATE INDEX IF NOT EXISTS "idx_home_layout_updated_20e112" ON "home_layout_module" ("updated_at");
CREATE INDEX IF NOT EXISTS "idx_home_layout_type_f88669" ON "home_layout_module" ("type");
CREATE INDEX IF NOT EXISTS "idx_home_layout_sort_49ce31" ON "home_layout_module" ("sort");
CREATE INDEX IF NOT EXISTS "idx_home_layout_is_enab_5d9b6a" ON "home_layout_module" ("is_enabled");
COMMENT ON COLUMN "home_layout_module"."type" IS '模块类型';
COMMENT ON COLUMN "home_layout_module"."sort" IS '模块排序';
COMMENT ON COLUMN "home_layout_module"."is_enabled" IS '是否启用';
COMMENT ON COLUMN "home_layout_module"."title" IS '模块标题';
COMMENT ON COLUMN "home_layout_module"."action" IS '模块操作配置';
COMMENT ON COLUMN "home_layout_module"."config" IS '模块配置';
CREATE TABLE IF NOT EXISTS "home_layout_item" (
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "sort" INT NOT NULL  DEFAULT 0,
    "image" VARCHAR(500) NOT NULL  DEFAULT '',
    "title" VARCHAR(255) NOT NULL  DEFAULT '',
    "description" VARCHAR(500) NOT NULL  DEFAULT '',
    "badge" VARCHAR(100) NOT NULL  DEFAULT '',
    "action" JSONB NOT NULL,
    "module_id" BIGINT NOT NULL REFERENCES "home_layout_module" ("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "idx_home_layout_created_9c8fdd" ON "home_layout_item" ("created_at");
CREATE INDEX IF NOT EXISTS "idx_home_layout_updated_14082f" ON "home_layout_item" ("updated_at");
CREATE INDEX IF NOT EXISTS "idx_home_layout_sort_753c60" ON "home_layout_item" ("sort");
COMMENT ON COLUMN "home_layout_item"."sort" IS '内容项排序';
COMMENT ON COLUMN "home_layout_item"."image" IS '图片地址';
COMMENT ON COLUMN "home_layout_item"."title" IS '主文案';
COMMENT ON COLUMN "home_layout_item"."description" IS '辅助文案';
COMMENT ON COLUMN "home_layout_item"."badge" IS '角标文案';
COMMENT ON COLUMN "home_layout_item"."action" IS '内容项操作配置';
CREATE TABLE IF NOT EXISTS "menu" (
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "name" VARCHAR(20) NOT NULL,
    "remark" JSONB,
    "menu_type" VARCHAR(7),
    "icon" VARCHAR(100),
    "path" VARCHAR(100) NOT NULL,
    "order" INT,
    "parent_id" INT NOT NULL  DEFAULT 0,
    "is_hidden" BOOL NOT NULL  DEFAULT False,
    "component" VARCHAR(100) NOT NULL,
    "keepalive" BOOL NOT NULL  DEFAULT True,
    "redirect" VARCHAR(100)
);
CREATE INDEX IF NOT EXISTS "idx_menu_created_b6922b" ON "menu" ("created_at");
CREATE INDEX IF NOT EXISTS "idx_menu_updated_e6b0a1" ON "menu" ("updated_at");
CREATE INDEX IF NOT EXISTS "idx_menu_name_b9b853" ON "menu" ("name");
CREATE INDEX IF NOT EXISTS "idx_menu_path_bf95b2" ON "menu" ("path");
CREATE INDEX IF NOT EXISTS "idx_menu_order_606068" ON "menu" ("order");
CREATE INDEX IF NOT EXISTS "idx_menu_parent__bebd15" ON "menu" ("parent_id");
COMMENT ON COLUMN "menu"."name" IS '菜单名称';
COMMENT ON COLUMN "menu"."remark" IS '保留字段';
COMMENT ON COLUMN "menu"."menu_type" IS '菜单类型';
COMMENT ON COLUMN "menu"."icon" IS '菜单图标';
COMMENT ON COLUMN "menu"."path" IS '菜单路径';
COMMENT ON COLUMN "menu"."order" IS '排序';
COMMENT ON COLUMN "menu"."parent_id" IS '父菜单ID';
COMMENT ON COLUMN "menu"."is_hidden" IS '是否隐藏';
COMMENT ON COLUMN "menu"."component" IS '组件';
COMMENT ON COLUMN "menu"."keepalive" IS '存活';
COMMENT ON COLUMN "menu"."redirect" IS '重定向';
CREATE TABLE IF NOT EXISTS "platform" (
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "platform_name" VARCHAR(100) NOT NULL,
    "custom_name" VARCHAR(50) NOT NULL UNIQUE,
    "click_count" INT NOT NULL  DEFAULT 0
);
CREATE INDEX IF NOT EXISTS "idx_platform_created_d8e9d2" ON "platform" ("created_at");
CREATE INDEX IF NOT EXISTS "idx_platform_updated_0075fd" ON "platform" ("updated_at");
CREATE INDEX IF NOT EXISTS "idx_platform_platfor_b05129" ON "platform" ("platform_name");
CREATE INDEX IF NOT EXISTS "idx_platform_custom__2b7d6d" ON "platform" ("custom_name");
CREATE INDEX IF NOT EXISTS "idx_platform_click_c_086eea" ON "platform" ("click_count");
COMMENT ON COLUMN "platform"."platform_name" IS '渠道名称';
COMMENT ON COLUMN "platform"."custom_name" IS '自定义标识';
COMMENT ON COLUMN "platform"."click_count" IS '渠道访问数据';
CREATE TABLE IF NOT EXISTS "product" (
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "category_id" BIGINT NOT NULL,
    "brand_id" BIGINT NOT NULL,
    "name" VARCHAR(100) NOT NULL,
    "product_code" VARCHAR(64),
    "desc" VARCHAR(255),
    "detail_description" JSONB NOT NULL,
    "cover_image_key" VARCHAR(500) NOT NULL,
    "image_keys" JSONB NOT NULL,
    "video_keys" JSONB NOT NULL,
    "click_count" INT NOT NULL  DEFAULT 0,
    "status" BOOL NOT NULL  DEFAULT True,
    "order" INT
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
COMMENT ON COLUMN "product"."category_id" IS '类目ID';
COMMENT ON COLUMN "product"."brand_id" IS '品牌ID';
COMMENT ON COLUMN "product"."name" IS '好物名称';
COMMENT ON COLUMN "product"."product_code" IS '好物识别码';
COMMENT ON COLUMN "product"."desc" IS '好物简介';
COMMENT ON COLUMN "product"."detail_description" IS '结构化详情';
COMMENT ON COLUMN "product"."cover_image_key" IS '封面图对象 Key';
COMMENT ON COLUMN "product"."image_keys" IS '图片对象 Key 列表';
COMMENT ON COLUMN "product"."video_keys" IS '视频对象 Key 列表';
COMMENT ON COLUMN "product"."click_count" IS '点击量';
COMMENT ON COLUMN "product"."status" IS '是否上架';
COMMENT ON COLUMN "product"."order" IS '排序';
CREATE TABLE IF NOT EXISTS "product_import_task" (
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "filename" VARCHAR(255) NOT NULL,
    "storage_key" VARCHAR(500) NOT NULL,
    "status" VARCHAR(17) NOT NULL  DEFAULT 'pending',
    "total_count" INT NOT NULL  DEFAULT 0,
    "processed_count" INT NOT NULL  DEFAULT 0,
    "success_count" INT NOT NULL  DEFAULT 0,
    "failed_count" INT NOT NULL  DEFAULT 0,
    "progress" INT NOT NULL  DEFAULT 0,
    "import_strategy" VARCHAR(11) NOT NULL  DEFAULT 'create_only',
    "error_message" TEXT,
    "result_summary" JSONB NOT NULL,
    "error_report_path" VARCHAR(500),
    "created_by" BIGINT NOT NULL,
    "started_at" TIMESTAMPTZ,
    "finished_at" TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS "idx_product_imp_created_b46973" ON "product_import_task" ("created_at");
CREATE INDEX IF NOT EXISTS "idx_product_imp_updated_dddb16" ON "product_import_task" ("updated_at");
CREATE INDEX IF NOT EXISTS "idx_product_imp_created_dac883" ON "product_import_task" ("created_by");
CREATE INDEX IF NOT EXISTS "idx_product_imp_started_d64f90" ON "product_import_task" ("started_at");
CREATE INDEX IF NOT EXISTS "idx_product_imp_finishe_12ad27" ON "product_import_task" ("finished_at");
COMMENT ON COLUMN "product_import_task"."filename" IS '原始ZIP文件名';
COMMENT ON COLUMN "product_import_task"."storage_key" IS '源文件存储定位信息';
COMMENT ON COLUMN "product_import_task"."status" IS '任务状态';
COMMENT ON COLUMN "product_import_task"."total_count" IS '模板总记录数';
COMMENT ON COLUMN "product_import_task"."processed_count" IS '已处理数量';
COMMENT ON COLUMN "product_import_task"."success_count" IS '成功数量';
COMMENT ON COLUMN "product_import_task"."failed_count" IS '失败数量';
COMMENT ON COLUMN "product_import_task"."progress" IS '进度百分比';
COMMENT ON COLUMN "product_import_task"."import_strategy" IS '导入策略';
COMMENT ON COLUMN "product_import_task"."error_message" IS '任务级错误摘要';
COMMENT ON COLUMN "product_import_task"."result_summary" IS '结果汇总';
COMMENT ON COLUMN "product_import_task"."error_report_path" IS '错误报告路径';
COMMENT ON COLUMN "product_import_task"."created_by" IS '发起人ID';
COMMENT ON COLUMN "product_import_task"."started_at" IS '开始时间';
COMMENT ON COLUMN "product_import_task"."finished_at" IS '完成时间';
CREATE TABLE IF NOT EXISTS "product_import_task_item" (
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "row_no" INT NOT NULL,
    "product_name" VARCHAR(100) NOT NULL,
    "status" VARCHAR(9) NOT NULL  DEFAULT 'pending',
    "message" TEXT,
    "category_name" VARCHAR(100),
    "brand_name" VARCHAR(100),
    "product_id" BIGINT,
    "duplicate_hint" BOOL NOT NULL  DEFAULT False,
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
COMMENT ON COLUMN "product_import_task_item"."row_no" IS 'Excel行号';
COMMENT ON COLUMN "product_import_task_item"."product_name" IS '好物名称';
COMMENT ON COLUMN "product_import_task_item"."status" IS '行级状态';
COMMENT ON COLUMN "product_import_task_item"."message" IS '处理结果信息';
COMMENT ON COLUMN "product_import_task_item"."category_name" IS '分类名称快照';
COMMENT ON COLUMN "product_import_task_item"."brand_name" IS '品牌名称快照';
COMMENT ON COLUMN "product_import_task_item"."product_id" IS '创建成功后的好物ID';
COMMENT ON COLUMN "product_import_task_item"."duplicate_hint" IS '是否疑似重复';
CREATE TABLE IF NOT EXISTS "role" (
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "name" VARCHAR(20) NOT NULL UNIQUE,
    "desc" VARCHAR(500)
);
CREATE INDEX IF NOT EXISTS "idx_role_created_7f5f71" ON "role" ("created_at");
CREATE INDEX IF NOT EXISTS "idx_role_updated_5dd337" ON "role" ("updated_at");
CREATE INDEX IF NOT EXISTS "idx_role_name_e5618b" ON "role" ("name");
COMMENT ON COLUMN "role"."name" IS '角色名称';
COMMENT ON COLUMN "role"."desc" IS '角色描述';
CREATE TABLE IF NOT EXISTS "site_config" (
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "logo_key" VARCHAR(500) NOT NULL  DEFAULT '',
    "about_title" VARCHAR(100) NOT NULL  DEFAULT '',
    "about_lines" JSONB NOT NULL,
    "footer_disclaimer" VARCHAR(500) NOT NULL  DEFAULT '',
    "share_base_url" VARCHAR(500) NOT NULL  DEFAULT ''
);
CREATE INDEX IF NOT EXISTS "idx_site_config_created_e149e1" ON "site_config" ("created_at");
CREATE INDEX IF NOT EXISTS "idx_site_config_updated_fd9299" ON "site_config" ("updated_at");
COMMENT ON COLUMN "site_config"."logo_key" IS '站点 Logo 对象 Key';
COMMENT ON COLUMN "site_config"."about_title" IS 'About 标题';
COMMENT ON COLUMN "site_config"."about_lines" IS 'About 文案段落';
COMMENT ON COLUMN "site_config"."footer_disclaimer" IS '底部声明';
COMMENT ON COLUMN "site_config"."share_base_url" IS '渠道分享基础链接';
CREATE TABLE IF NOT EXISTS "site_visit" (
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "visitor_id" VARCHAR(64) NOT NULL,
    "path" VARCHAR(255) NOT NULL  DEFAULT '/',
    "region" VARCHAR(100) NOT NULL  DEFAULT '',
    "user_agent" VARCHAR(500) NOT NULL  DEFAULT '',
    "visited_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "idx_site_visit_visitor_9826af" ON "site_visit" ("visitor_id");
CREATE INDEX IF NOT EXISTS "idx_site_visit_path_46ff76" ON "site_visit" ("path");
CREATE INDEX IF NOT EXISTS "idx_site_visit_region_e376d7" ON "site_visit" ("region");
CREATE INDEX IF NOT EXISTS "idx_site_visit_visited_ce9658" ON "site_visit" ("visited_at");
COMMENT ON COLUMN "site_visit"."visitor_id" IS '访客标识';
COMMENT ON COLUMN "site_visit"."path" IS '访问路径';
COMMENT ON COLUMN "site_visit"."region" IS '所属区域';
COMMENT ON COLUMN "site_visit"."user_agent" IS '用户代理';
COMMENT ON COLUMN "site_visit"."visited_at" IS '访问时间';
CREATE TABLE IF NOT EXISTS "tag" (
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "name" VARCHAR(100) NOT NULL UNIQUE,
    "remark" VARCHAR(255),
    "search_count" INT NOT NULL  DEFAULT 0,
    "sort" INT,
    "is_active" BOOL NOT NULL  DEFAULT True
);
CREATE INDEX IF NOT EXISTS "idx_tag_created_e4e466" ON "tag" ("created_at");
CREATE INDEX IF NOT EXISTS "idx_tag_updated_fb661e" ON "tag" ("updated_at");
CREATE INDEX IF NOT EXISTS "idx_tag_name_a7b9a6" ON "tag" ("name");
CREATE INDEX IF NOT EXISTS "idx_tag_search__566698" ON "tag" ("search_count");
CREATE INDEX IF NOT EXISTS "idx_tag_sort_73ff0f" ON "tag" ("sort");
CREATE INDEX IF NOT EXISTS "idx_tag_is_acti_50cf59" ON "tag" ("is_active");
COMMENT ON COLUMN "tag"."name" IS '标签名称';
COMMENT ON COLUMN "tag"."remark" IS '备注';
COMMENT ON COLUMN "tag"."search_count" IS '检索次数';
COMMENT ON COLUMN "tag"."sort" IS '排序';
COMMENT ON COLUMN "tag"."is_active" IS '是否启用';
CREATE TABLE IF NOT EXISTS "user" (
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "username" VARCHAR(20) NOT NULL UNIQUE,
    "alias" VARCHAR(30),
    "email" VARCHAR(255)  UNIQUE,
    "phone" VARCHAR(20),
    "password" VARCHAR(128),
    "is_active" BOOL NOT NULL  DEFAULT True,
    "is_superuser" BOOL NOT NULL  DEFAULT False,
    "last_login" TIMESTAMPTZ,
    "dept_id" INT
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
COMMENT ON COLUMN "user"."username" IS '用户名称';
COMMENT ON COLUMN "user"."alias" IS '姓名';
COMMENT ON COLUMN "user"."email" IS '邮箱';
COMMENT ON COLUMN "user"."phone" IS '电话';
COMMENT ON COLUMN "user"."password" IS '密码';
COMMENT ON COLUMN "user"."is_active" IS '是否激活';
COMMENT ON COLUMN "user"."is_superuser" IS '是否为超级管理员';
COMMENT ON COLUMN "user"."last_login" IS '最后登录时间';
COMMENT ON COLUMN "user"."dept_id" IS '部门ID';
CREATE TABLE IF NOT EXISTS "aerich" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "version" VARCHAR(255) NOT NULL,
    "app" VARCHAR(100) NOT NULL,
    "content" JSONB NOT NULL
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
CREATE UNIQUE INDEX IF NOT EXISTS "uidx_user_role_user_id_d0bad3" ON "user_role" ("user_id", "role_id");
"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
DROP TABLE IF EXISTS "user_role" CASCADE;
DROP TABLE IF EXISTS "role_api" CASCADE;
DROP TABLE IF EXISTS "role_menu" CASCADE;
DROP TABLE IF EXISTS "product_tag" CASCADE;
DROP TABLE IF EXISTS "category_hot_tag" CASCADE;
DROP TABLE IF EXISTS "brand_category" CASCADE;
DROP TABLE IF EXISTS "brand_hot_category" CASCADE;
DROP TABLE IF EXISTS "aerich" CASCADE;
DROP TABLE IF EXISTS "user" CASCADE;
DROP TABLE IF EXISTS "tag" CASCADE;
DROP TABLE IF EXISTS "site_visit" CASCADE;
DROP TABLE IF EXISTS "site_config" CASCADE;
DROP TABLE IF EXISTS "role" CASCADE;
DROP TABLE IF EXISTS "product_import_task_item" CASCADE;
DROP TABLE IF EXISTS "product_import_task" CASCADE;
DROP TABLE IF EXISTS "product" CASCADE;
DROP TABLE IF EXISTS "platform" CASCADE;
DROP TABLE IF EXISTS "menu" CASCADE;
DROP TABLE IF EXISTS "home_layout_item" CASCADE;
DROP TABLE IF EXISTS "home_layout_module" CASCADE;
DROP TABLE IF EXISTS "home_layout" CASCADE;
DROP TABLE IF EXISTS "deptclosure" CASCADE;
DROP TABLE IF EXISTS "dept" CASCADE;
DROP TABLE IF EXISTS "contact_click_dedup" CASCADE;
DROP TABLE IF EXISTS "contact_click" CASCADE;
DROP TABLE IF EXISTS "contact" CASCADE;
DROP TABLE IF EXISTS "channel_visit_dedup" CASCADE;
DROP TABLE IF EXISTS "channel_visit" CASCADE;
DROP TABLE IF EXISTS "category" CASCADE;
DROP TABLE IF EXISTS "brand" CASCADE;
DROP TABLE IF EXISTS "banner" CASCADE;
DROP TABLE IF EXISTS "auditlog" CASCADE;
DROP TABLE IF EXISTS "api" CASCADE;
"""
