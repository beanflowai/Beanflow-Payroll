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

#### 1. 转换 PDF 到 JSON

```bash
cd backend

# 完整转换（生成3个文件）
uv run python -m tools.tax_config_converter convert \
  --pdf ../docs/tax-tables/2025/01/t4127-01-25e.pdf \
  --output config/tax_tables/2025/

# Dry-run 模式（仅提取不写文件）
uv run python -m tools.tax_config_converter -v convert \
  --pdf ../docs/tax-tables/2025/01/t4127-01-25e.pdf \
  --output tools/tax_config_converter/output/2025/ \
  --dry-run

# 指定版本类型
uv run python -m tools.tax_config_converter convert \
  --pdf ../docs/tax-tables/2025/07/t4127-07-25e.pdf \
  --output config/tax_tables/2025/ \
  --edition jul
```

**预期耗时：**
- CPP/EI 提取: ~40秒
- Federal 提取: ~1.5分钟
- Provinces 提取: ~4分钟（12个省份）
- 总计: 约 6-7 分钟

#### 2. 验证现有配置文件

```bash
cd backend

# 验证配置目录
uv run python -m tools.tax_config_converter validate \
  --config config/tax_tables/2025/
```

#### 3. 提取 PDF 文本（调试用）

```bash
cd backend

# 查看 PDF 元数据和表格
uv run python -m tools.tax_config_converter extract \
  --pdf ../docs/tax-tables/2025/01/t4127-01-25e.pdf

# 导出特定表格
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
  --dry-run        仅提取不写文件

validate 参数:
  --config, -c     配置目录路径（必需）

extract 参数:
  --pdf, -p        PDF 文件路径（必需）
  --output, -o     输出文件路径（可选）
  --table, -t      提取特定表格，如 8.1, 8.3（可选）
```

### 生成的文件

每次转换生成 3 个文件：

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

### 验证流程

1. **Schema 验证**: 检查 JSON 格式是否符合 `config/tax_tables/schemas/*.schema.json`
2. **Sanity 检查**: 验证数值范围、顺序等逻辑
3. **PDOC 测试**: 运行 `pytest tests/payroll/pdoc/` 验证计算准确性
