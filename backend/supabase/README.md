# Supabase Database Migrations

此目录使用 **Supabase CLI** 管理数据库迁移。

## 前置要求

```bash
# 安装 Supabase CLI (macOS)
brew install supabase/tap/supabase

# 验证版本 (需要 v2.65.0+)
supabase --version
```

## 初始设置

```bash
cd backend/supabase

# 登录 Supabase
supabase login

# 展示所有当前账户的 projects
supabase projects list

# 链接到远程项目 (需要数据库密码)
# Beanflow-Payroll
supabase link --project-ref mzmhopogxtwchkidcgxv

```

数据库密码可在 Supabase Dashboard → Project Settings → Database → Database password 获取。

---

## 常用命令

### 查看 Migration 状态

```bash
supabase migration list
```

输出示例：
```
 Local          | Remote         | Time (UTC)
----------------|----------------|---------------------
 20251201000001 | 20251201000001 | 2025-12-01 00:00:01  ✓ 已同步
 20251205000010 |                | 2025-12-05 00:00:10  ← 待执行
```

### 创建新 Migration

```bash
supabase migration new my_migration_name
```

这会创建 `migrations/YYYYMMDDHHMMSS_my_migration_name.sql` 文件。

### 执行 Migration（推送到远程）

```bash
supabase db push
```

这会执行所有未应用的 migration。

### 回滚/修复 Migration

如果需要标记某个 migration 为已执行（手动执行后）：

```bash
supabase migration repair 20251205000010 --status applied
```

如果需要标记某个 migration 为未执行（回滚后）：

```bash
supabase migration repair 20251205000010 --status reverted
```

### 生成 Migration（从数据库差异）

```bash
# 对比本地和远程数据库，自动生成 migration
supabase db diff --use-migra -f my_changes
```

---

## 目录结构

```
backend/supabase/
├── config.toml              # Supabase CLI 配置
├── migrations/              # Migration SQL 文件
│   ├── 20251201000001_create_document_files_table.sql
│   ├── 20251201000002_fix_check_constraints_case.sql
│   ├── 20251201000003_create_task_progress_table.sql
│   ├── 20251201000004_allow_null_status_for_pdfs.sql
│   ├── 20251201000005_add_transaction_count_to_document_files.sql
│   ├── 20251205000006_create_document_folders_table.sql
│   ├── 20251205000007_add_folder_foreign_key.sql
│   ├── 20251205000008_create_ledger_metadata_table.sql
│   └── 20251205000009_create_company_info_table.sql
├── Scripts/                 # 数据迁移脚本 (Firestore → Supabase)
└── README.md               # 本文件
```

---

## Migration 文件命名规范

格式: `YYYYMMDDHHMMSS_description.sql`

- `YYYYMMDD`: 日期
- `HHMMSS`: 时间（用于排序，可使用序号如 000001）
- `description`: 简短描述（snake_case）

示例:
```
20251205143022_add_user_preferences_table.sql
20251206000001_add_index_on_created_at.sql
```

---

## 编写 Migration 最佳实践

### 1. 使用 IF NOT EXISTS / IF EXISTS

```sql
-- 创建表
CREATE TABLE IF NOT EXISTS my_table (...);

-- 删除表
DROP TABLE IF EXISTS my_table;

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_name ON my_table(column);
```

### 2. 包含回滚注释

在每个 migration 文件末尾添加回滚 SQL（注释形式）：

```sql
-- ============================================================================
-- ROLLBACK (手动执行)
-- ============================================================================
-- DROP TABLE IF EXISTS my_table CASCADE;
```

### 3. 启用 RLS

```sql
ALTER TABLE my_table ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can access own data" ON my_table
  FOR ALL
  USING (user_id = current_setting('app.current_user_id', TRUE));
```

---

## 故障排除

### 连接失败

```
failed SASL auth (invalid SCRAM server-final-message received from server)
```

**解决方案**: 升级 Supabase CLI 到最新版本

```bash
brew upgrade supabase
```

### Migration 不同步

如果手动在 Dashboard 执行了 SQL，需要标记为已执行：

```bash
supabase migration repair YYYYMMDDHHMMSS --status applied
```

### 查看详细日志

```bash
supabase migration list --debug
```

---

## 相关文档

- [Supabase CLI 官方文档](https://supabase.com/docs/guides/cli)
- [Database Migrations](https://supabase.com/docs/guides/cli/local-development#database-migrations)

---

_最后更新: 2025-12-05 - 集成 Supabase CLI 管理 migrations_
