# BeanFlow Payroll - 架构概览

**最后更新**: 2025-12-16
**版本**: v3.1 (Hybrid Architecture)

---

## 产品定位

BeanFlow Payroll 是一个**独立的薪资管理产品**，与 BeanFlow Bookkeeping 分开部署但共享基础设施。

| 方面 | BeanFlow Payroll | BeanFlow Bookkeeping |
|------|------------------|---------------------|
| **域名** | `payroll.beanflow.com` | `app.beanflow.com` |
| **前端** | 独立 SvelteKit 应用 (Port 5174) | 现有前端 (Port 5173) |
| **后端** | 共享 FastAPI `/payroll/` 路由 | 共享 FastAPI |
| **数据库** | 共享 Supabase，独立表 | 共享 Supabase |
| **认证** | 共享 Google OAuth | 共享 Google OAuth |

---

## 系统架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                     Frontend (SvelteKit 5)                       │
│                payroll.beanflow.com (Port 5174)                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   src/lib/services/              src/routes/(app)/               │
│   ├── employeeService.ts         ├── dashboard/                  │
│   ├── companyService.ts          ├── employees/                  │
│   └── payGroupService.ts         ├── payroll/                    │
│                                  ├── reports/                    │
│                                  └── settings/                   │
│                                                                  │
└─────────────┬────────────────────────────────┬──────────────────┘
              │                                │
              │ 简单 CRUD                       │ 复杂计算
              │ (直连)                          │ (API)
              ▼                                ▼
┌─────────────────────────────┐   ┌────────────────────────────────┐
│                             │   │                                │
│    Supabase Client          │   │     FastAPI Backend            │
│    (前端直连)                │   │     /api/v1/payroll/           │
│                             │   │                                │
│    - 员工 CRUD              │   │     - 税务计算引擎              │
│    - 公司设置               │   │     - CPP/EI 计算               │
│    - Pay Group 管理         │   │     - Paystub PDF 生成          │
│    - 实时订阅               │   │     - Beancount 集成            │
│    - RLS 多租户隔离          │   │     - 文件存储 (DO Spaces)      │
│                             │   │                                │
└─────────────┬───────────────┘   └──────────────┬─────────────────┘
              │                                  │
              └────────────────┬─────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                    PostgreSQL (Supabase)                         │
│                                                                  │
│   ┌───────────┐   ┌───────────┐   ┌─────────────┐               │
│   │ companies │──<│ pay_groups│   │  employees  │               │
│   └─────┬─────┘   └─────┬─────┘   └──────┬──────┘               │
│         │               │                │                       │
│         └───────────────┴────────────────┤                       │
│                                          │                       │
│   ┌─────────────┐                ┌───────┴───────┐               │
│   │payroll_runs │───────────────>│payroll_records│               │
│   └─────────────┘        1:N     └───────────────┘               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │  DigitalOcean Spaces │
                    │  (Paystub PDFs)      │
                    └─────────────────────┘
```

---

## 数据访问模式 (Hybrid Architecture)

采用**混合架构**：简单数据操作直连 Supabase，复杂计算走 FastAPI。

| 操作类型 | 访问方式 | 示例 | 安全机制 |
|---------|---------|------|---------|
| **简单 CRUD** | 前端 → Supabase 直连 | 员工列表、公司设置、Pay Group | RLS 策略 |
| **复杂计算** | 前端 → FastAPI → Supabase | 税务计算、Payroll Run 处理 | JWT + RLS |
| **敏感数据** | 前端 → FastAPI (加密) | SIN 加密/解密 | Fernet 加密 |
| **文件存储** | FastAPI → DO Spaces | Paystub PDF | Pre-signed URLs |

### 为什么采用混合架构？

| 直连 Supabase 的优势 | 走 API 的必要场景 |
|---------------------|------------------|
| 开发效率高 | 复杂业务逻辑 (税务计算) |
| 实时订阅支持 | 需要服务端加密 (SIN) |
| 减少 API 层代码 | 文件处理 (PDF 生成) |
| RLS 自动多租户隔离 | 外部集成 (Beancount) |

---

## 数据模型关系

```
┌─────────────┐
│   Company   │ 公司信息、CRA 汇款配置、Bookkeeping 集成
└──────┬──────┘
       │ 1:N
       ▼
┌─────────────┐
│  Pay Group  │ 政策模板：薪资周期、法定扣款默认值、福利配置
└──────┬──────┘
       │ (policy template - 通过属性匹配)
       │
       ▼
┌─────────────┐
│  Employee   │ 员工主数据：TD1 申报额、薪资、豁免状态
└──────┬──────┘
       │ 1:N
       ▼
┌───────────────┐     N:1     ┌──────────────┐
│Payroll Record │────────────>│ Payroll Run  │
└───────────────┘             └──────────────┘
  个人工资记录                   工资运行批次
  (收入、扣款、净薪)              (状态机、汇总)
```

### 表关系说明

| 关系 | 说明 |
|------|------|
| Company → Pay Groups | 一个公司可以有多个薪资组 (按员工类型/支付周期) |
| Company → Employees | 一个公司有多个员工 |
| Pay Group → Employee | 通过 `pay_frequency` + `employment_type` 匹配 |
| Payroll Run → Records | 一次工资运行包含多个员工记录 |
| Employee → Records | 一个员工有多条历史工资记录 |

---

## 技术栈

| 层 | 技术 | 版本 | 备注 |
|---|------|------|------|
| **Frontend** | SvelteKit | 5.x | Runes 语法 (`$state`, `$derived`) |
| **UI** | Tailwind CSS | 3.x | 共享设计系统 |
| **Backend** | FastAPI | 0.109+ | Python async |
| **Runtime** | Python | 3.12 | uv 包管理 |
| **Database** | PostgreSQL | 15 | via Supabase |
| **Auth** | Supabase Auth | - | Google OAuth |
| **Tax Config** | JSON | - | 年度更新友好 |
| **File Storage** | DigitalOcean Spaces | - | S3 兼容 |

---

## 目录结构

```
BeanFlow-Payroll/
├── backend/
│   ├── app/
│   │   ├── api/v1/
│   │   │   └── payroll.py           # REST API 端点 (TODO)
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   └── payroll.py           # Pydantic 模型 ✅
│   │   └── services/payroll/
│   │       ├── __init__.py
│   │       ├── tax_tables.py        # 税表加载器 ✅
│   │       ├── cpp_calculator.py    # CPP 计算 (TODO)
│   │       ├── ei_calculator.py     # EI 计算 (TODO)
│   │       └── payroll_engine.py    # 计算引擎 (TODO)
│   ├── config/
│   │   └── tax_tables/2025/
│   │       ├── federal.json         # 联邦税表 ✅
│   │       ├── cpp_ei.json          # CPP/EI 配置 ✅
│   │       └── provinces.json       # 省税表 ✅
│   └── supabase/migrations/
│       ├── 20251216_create_payroll_tables.sql    # 核心表 ✅
│       └── 20251216_add_companies_pay_groups.sql # 扩展表 ✅
│
├── frontend/
│   └── src/lib/
│       ├── api/
│       │   └── supabase.ts          # Supabase 客户端
│       ├── stores/
│       │   └── auth.svelte.ts       # 认证状态
│       ├── types/
│       │   ├── employee.ts          # 员工类型 ✅
│       │   ├── payroll.ts           # 工资类型 ✅
│       │   ├── company.ts           # 公司类型 ✅
│       │   └── pay-group.ts         # 薪资组类型 ✅
│       └── services/
│           ├── employeeService.ts   # 员工 CRUD ✅
│           ├── companyService.ts    # 公司 CRUD ✅
│           └── payGroupService.ts   # 薪资组 CRUD ✅
│
└── docs/
    ├── 00_architecture_overview.md  # 本文档
    ├── 01_phase1_data_layer.md      # Phase 1 实现详情
    ├── 02_phase2_calculations.md    # 计算引擎设计
    ├── 03_phase3_paystub.md         # Paystub 生成
    ├── 04_phase4_api_integration.md # API 集成
    ├── 13_database_schema.md        # 数据库详情
    ├── implementation_checklist.md  # 进度跟踪
    └── ui/                          # UI 设计文档
```

---

## 实现状态

### Phase 1: Data Layer ✅ (已完成 ~70%)

| 任务 | 状态 | 文件 |
|------|------|------|
| 数据库 Schema | ✅ | `migrations/20251216_*.sql` |
| Tax Tables (JSON) | ✅ | `config/tax_tables/2025/` |
| Tax Loader (Python) | ✅ | `services/payroll/tax_tables.py` |
| Pydantic Models | ✅ | `models/payroll.py` |
| Frontend Types | ✅ | `types/*.ts` |
| Frontend Services | ✅ | `services/*Service.ts` |

### Phase 2: Calculations (TODO)

- [ ] CPP Calculator
- [ ] EI Calculator
- [ ] Federal Tax Calculator
- [ ] Provincial Tax Calculator
- [ ] Payroll Engine

### Phase 3-5: (TODO)

见 `implementation_checklist.md`

---

## 安全设计

### 多租户隔离

所有表使用 `user_id` 字段 + RLS 策略：

```sql
CREATE POLICY "Users can access own data"
    ON table_name
    FOR ALL
    USING (user_id = current_setting('app.current_user_id', TRUE));
```

### SIN 加密

- 存储: Fernet 对称加密 (AES-128-CBC)
- 显示: 掩码格式 `***-***-XXX`
- 解密: 仅在 FastAPI 后端进行

### 文件访问

- Paystub PDF 存储在 DO Spaces
- 使用 Pre-signed URL (15 分钟有效期)
- 路径格式: `{bucket}/{user_id}/payroll/paystubs/{year}/{employee_id}_{pay_date}.pdf`

---

## 快速链接

| 文档 | 说明 |
|------|------|
| [implementation_checklist.md](./implementation_checklist.md) | 进度跟踪 |
| [01_phase1_data_layer.md](./01_phase1_data_layer.md) | Phase 1 详情 |
| [13_database_schema.md](./13_database_schema.md) | 数据库设计 |
| [02_phase2_calculations.md](./02_phase2_calculations.md) | 计算引擎设计 |
| [ui/](./ui/) | UI 设计文档 |

---

## 变更记录

| 日期 | 版本 | 变更 |
|------|------|------|
| 2025-12-16 | v3.1 | 创建架构概览；采用混合架构 (前端直连 + API) |
| 2025-12-16 | v3.0 | 添加 Company/Pay Groups 实体 |
| 2025-12-07 | v2.0 | 迁移到 Supabase 架构 |
