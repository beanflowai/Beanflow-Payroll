# Backend Tools

## Tax Config Converter

将 CRA T4127 PDF 文档转换为 JSON 税务配置文件。

### 环境准备

```bash
# 安装 tools 依赖
cd backend
uv sync --extra tools
```

在 `backend/.env` 中配置 GLM API Key：

```env
GLM_API_KEY=your-api-key-here
```

> 工具会自动从 `.env` 文件加载 API Key，无需手动 export。

### 使用方法

#### 1. 分步转换（推荐）

支持断点续传，每一步完成后自动保存中间文件，中断后可从断点继续。

```bash
cd backend

# Step 1: PDF 提取（秒级，不需要 API）
uv run python -m tools.tax_config_converter convert \
  --pdf ../docs/tax-tables/2025/01/t4127-01-25e.pdf \
  --output tools/tax_config_converter/output/2025/ \
  --step extract

# Step 2: CPP/EI 解析（~40秒）
uv run python -m tools.tax_config_converter convert \
  --pdf ../docs/tax-tables/2025/01/t4127-01-25e.pdf \
  --output tools/tax_config_converter/output/2025/ \
  --step cpp-ei

# Step 3: Federal 解析（~1.5分钟）
uv run python -m tools.tax_config_converter convert \
  --pdf ../docs/tax-tables/2025/01/t4127-01-25e.pdf \
  --output tools/tax_config_converter/output/2025/ \
  --step federal

# Step 4: Provinces 解析（~4分钟）
uv run python -m tools.tax_config_converter convert \
  --pdf ../docs/tax-tables/2025/01/t4127-01-25e.pdf \
  --output tools/tax_config_converter/output/2025/ \
  --step provinces

# Step 5: 生成最终配置文件
uv run python -m tools.tax_config_converter convert \
  --pdf ../docs/tax-tables/2025/01/t4127-01-25e.pdf \
  --output tools/tax_config_converter/output/2025/ \
  --step generate
```

#### 2. 一键转换（自动断点续传）

```bash
cd backend

# 完整转换（自动跳过已完成的步骤）
uv run python -m tools.tax_config_converter convert \
  --pdf ../docs/tax-tables/2025/01/t4127-01-25e.pdf \
  --output config/tax_tables/2025/

# 带 verbose 输出
uv run python -m tools.tax_config_converter -v convert \
  --pdf ../docs/tax-tables/2025/01/t4127-01-25e.pdf \
  --output config/tax_tables/2025/
```

#### 3. 验证现有配置文件

```bash
cd backend

uv run python -m tools.tax_config_converter validate \
  --config config/tax_tables/2025/
```

#### 4. 提取 PDF 文本（调试用）

```bash
cd backend

# 查看 PDF 元数据和表格
uv run python -m tools.tax_config_converter extract \
  --pdf ../docs/tax-tables/2025/01/t4127-01-25e.pdf

# 保存到目录（生成 metadata.json + tables_extracted.json）
uv run python -m tools.tax_config_converter extract \
  --pdf ../docs/tax-tables/2025/01/t4127-01-25e.pdf \
  --output tools/tax_config_converter/output/2025/

# 导出特定表格到文件
uv run python -m tools.tax_config_converter extract \
  --pdf ../docs/tax-tables/2025/01/t4127-01-25e.pdf \
  --table 8.3 \
  --output /tmp/table_8.3.txt
```

### CLI 参数

```
usage: tax_config_converter [-h] [-v] {convert,validate,extract} ...

Commands:
  convert   - 转换 T4127 PDF 为 JSON 配置文件
  validate  - 验证现有 JSON 配置文件
  extract   - 提取 PDF 文本（调试用）

convert 参数:
  --pdf, -p        PDF 文件路径（必需）
  --output, -o     输出目录（必需）
  --edition, -e    版本类型: jan, jul, auto（默认: auto）
  --model, -m      GLM 模型（默认: glm-4.7）
  --no-thinking    禁用 GLM thinking 模式
  --skip-validation 跳过 schema 验证
  --dry-run        仅提取中间文件，不生成最终配置
  --step, -s       运行特定步骤: extract, cpp-ei, federal, provinces, generate, all（默认: all）

validate 参数:
  --config, -c     配置目录路径（必需）

extract 参数:
  --pdf, -p        PDF 文件路径（必需）
  --output, -o     输出路径（目录则生成 JSON，文件则生成文本）
  --table, -t      提取特定表格，如 8.1, 8.3（可选）
```

### 中间文件（断点续传）

转换过程会在 output 目录生成中间文件，支持断点续传：

| 文件 | 步骤 | 说明 |
|------|------|------|
| `metadata.json` | extract | PDF 元数据（edition, year, pages） |
| `tables_extracted.json` | extract | 提取的表格原文（7个表格） |
| `cpp_ei_parsed.json` | cpp-ei | GLM 解析的 CPP/EI 数据 |
| `federal_parsed.json` | federal | GLM 解析的联邦税数据 |
| `provinces_parsed.json` | provinces | GLM 解析的省税数据 |

如果步骤中断，重新运行相同命令会自动跳过已完成的步骤。

### 最终生成文件

每次完整转换生成 3 个配置文件：

| 文件 | 说明 |
|------|------|
| `cpp_ei.json` | CPP/CPP2/EI 费率和限额 |
| `federal_{jan,jul}.json` | 联邦税率表和抵免额 |
| `provinces_{jan,jul}.json` | 12省/地区税率表 |

### 源 PDF 位置

```
docs/tax-tables/
├── 2024/
│   ├── 01/t4127-01-24e.pdf  # January edition
│   └── 07/t4127-07-24e.pdf  # July edition
├── 2025/
│   ├── 01/t4127-01-25e.pdf
│   └── 07/t4127-07-25e.pdf
└── 2026/
    └── 01/t4127-01-26e.pdf
```

### 预期耗时

| 步骤 | 耗时 | 需要 API |
|------|------|----------|
| extract | ~1秒 | ❌ |
| cpp-ei | ~40秒 | ✓ |
| federal | ~1.5分钟 | ✓ |
| provinces | ~4分钟 | ✓ |
| generate | ~1秒 | ❌ |
| **总计** | **~6-7分钟** | |

### 验证流程

1. **Schema 验证**: 检查 JSON 格式是否符合 `config/tax_tables/schemas/*.schema.json`
2. **Sanity 检查**: 验证数值范围、顺序等逻辑
3. **PDOC 测试**: 运行 `pytest tests/payroll/pdoc/` 验证计算准确性
