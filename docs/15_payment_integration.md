# Phase 6: Payment Integration (支付集成)

**Duration**: 2-3 weeks (未来阶段)
**Complexity**: Medium
**Prerequisites**: Phase 1-5 completed, Payroll Run 功能完成
**Status**: 📋 规划中

> **Last Updated**: 2025-12-17

---

## 🎯 Objectives

实现 Payroll 支付执行功能：
1. PAD (Pre-Authorized Debit) 从雇主公司账户扣款
2. EFT 向员工银行账户发放工资
3. CRA 汇款（CPP/EI/Tax 代扣代缴）

---

## 📊 现状分析

### 已实现功能
- ✅ 税务计算引擎 (CPP, EI, 联邦税, 省税)
- ✅ 员工管理 (CRUD, SIN 加密)
- ✅ Payroll Run 流程 (Draft → Calculate → Approve)
- ✅ Paystub PDF 生成
- ✅ Beancount 会计分录集成
- ✅ Remittance 报表

### 缺失功能
- ❌ 从公司账户扣款
- ❌ 向员工账户发薪
- ❌ 向 CRA 自动汇款

---

## 🏆 推荐方案：Plooto API

### 为什么选择 Plooto

| 因素 | Plooto | VoPay | 自建 |
|------|--------|-------|------|
| **月费** | $32 CAD | $500 CAD | $0 |
| **交易费** | $0.50/笔 | $0.50/笔 | N/A |
| **CRA 支付** | $3/笔 ✅ | 需确认 | ❌ |
| **适合规模** | 小企业 ✅ | 大企业 | - |
| **加拿大本土** | ✅ 多伦多 | ✅ | - |
| **API 可用** | ✅ | ✅ | - |
| **合规负担** | 低 | 低 | 高 |

### Plooto 公司背景

- **总部**: 加拿大多伦多
- **成立**: 2015 年
- **荣誉**: Deloitte Technology Fast 50™ Canada
- **目标客户**: 加拿大中小企业、会计师

### 支持的功能

- ✅ EFT 银行转账 (加拿大)
- ✅ PAD 预授权扣款
- ✅ CRA 支付 (Payroll Deductions, GST/HST, Corporate Tax)
- ✅ QuickBooks / Xero 集成
- ✅ API 访问

---

## 💰 成本估算

### 单次 Payroll Run (10 员工)

| 交易类型 | 数量 | 单价 | 小计 |
|----------|------|------|------|
| PAD 从公司扣款 | 1 | $0.50 | $0.50 |
| EFT 给员工发薪 | 10 | $0.50 | $5.00 |
| CRA 汇款 | 1 | $3.00 | $3.00 |
| **交易费小计** | | | **$8.50** |

### 月度成本

| 员工数 | 发薪频率 | 月费 | 交易费 | 月总计 |
|--------|----------|------|--------|--------|
| 10 | 每月 2 次 | $32 | $17 | **~$49** |
| 25 | 每月 2 次 | $32 | $32 | **~$64** |
| 50 | 每月 2 次 | $32 | $57 | **~$89** |

---

## 🏗️ 系统架构

### 支付流程

```
┌─────────────────────────────────────────────────────────────┐
│                    Beanflow Payroll                          │
│                                                              │
│  Payroll Run (Draft) → Calculate → Review → Approve          │
│                                                ↓             │
│                                    ┌──────────────────┐      │
│                                    │ Payment Service  │      │
│                                    │ (payment_service)│      │
│                                    └────────┬─────────┘      │
└─────────────────────────────────────────────┼───────────────┘
                                              │
                                              ↓
┌─────────────────────────────────────────────────────────────┐
│                      Plooto API                              │
│                                                              │
│   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐       │
│   │ PAD Debit   │   │ EFT Credit  │   │ CRA Payment │       │
│   │ (从公司扣款) │   │ (给员工发薪) │   │ (税务汇款)  │       │
│   └──────┬──────┘   └──────┬──────┘   └──────┬──────┘       │
└──────────┼─────────────────┼─────────────────┼──────────────┘
           │                 │                 │
           ↓                 ↓                 ↓
      公司银行账户      员工银行账户         CRA
```

### 状态流转

```
PayrollRun.status:
  draft → calculated → pending_approval → approved → payment_pending
                                                          ↓
                                              ┌───────────┴───────────┐
                                              ↓                       ↓
                                        payment_processing      payment_failed
                                              ↓                       ↓
                                        payment_completed        retry / manual
```

---

## 📦 实现阶段

### Stage 1: Plooto 账户设置

**任务**:
- [ ] 注册 Plooto 商户账户
- [ ] 获取 API credentials (Client ID, Secret)
- [ ] 设置 Sandbox 测试环境
- [ ] 配置 Webhook 回调 URL

**产出**:
- Plooto 账户就绪
- API 密钥存储在环境变量

---

### Stage 2: 后端 API 集成

**文件结构**:
```
backend/app/
├── services/payroll/
│   ├── payment_service.py        # 支付服务抽象层
│   └── plooto_integration.py     # Plooto API 实现
├── models/
│   └── payment.py                # 支付相关 Pydantic 模型
└── api/v1/
    └── payments.py               # 支付 API 端点 (可选)
```

**核心接口**:
```python
# payment_service.py
class PaymentService:
    async def initiate_payroll_payment(
        self,
        payroll_run_id: UUID,
        company_bank_account: BankAccount,
        employee_payments: list[EmployeePayment],
        cra_remittance: CRARemittance
    ) -> PaymentBatch:
        """发起一次完整的 Payroll 支付"""
        pass

    async def check_payment_status(
        self,
        payment_batch_id: UUID
    ) -> PaymentStatus:
        """查询支付状态"""
        pass

    async def handle_webhook(
        self,
        event: PlootoWebhookEvent
    ) -> None:
        """处理 Plooto 回调"""
        pass
```

**任务**:
- [ ] 调研 Plooto API 文档
- [ ] 实现 `PlootoClient` 基础类
- [ ] 实现 PAD 扣款接口
- [ ] 实现 EFT 发薪接口 (批量)
- [ ] 实现 CRA 支付接口
- [ ] Webhook 回调处理
- [ ] 错误处理和重试逻辑

---

### Stage 3: 数据库扩展

**新增表**:
```sql
-- 支付批次记录
CREATE TABLE payment_batches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    payroll_run_id UUID REFERENCES payroll_runs(id),

    -- Plooto 关联
    plooto_batch_id TEXT,

    -- 金额汇总
    total_amount DECIMAL(12,2) NOT NULL,
    company_debit_amount DECIMAL(12,2),
    employee_credit_total DECIMAL(12,2),
    cra_payment_amount DECIMAL(12,2),

    -- 状态
    status TEXT NOT NULL DEFAULT 'pending',
    -- pending, processing, completed, failed, cancelled

    -- 时间戳
    initiated_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 单笔支付记录
CREATE TABLE payment_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    payment_batch_id UUID REFERENCES payment_batches(id),

    -- 类型: pad_debit, eft_credit, cra_payment
    transaction_type TEXT NOT NULL,

    -- 收款方
    recipient_type TEXT, -- employee, cra, company
    recipient_id UUID,   -- employee_id if applicable

    -- Plooto 关联
    plooto_transaction_id TEXT,

    -- 金额
    amount DECIMAL(12,2) NOT NULL,
    currency TEXT DEFAULT 'CAD',

    -- 状态
    status TEXT NOT NULL DEFAULT 'pending',
    error_message TEXT,

    -- 时间戳
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

**任务**:
- [ ] 创建 migration 文件
- [ ] 添加 RLS 策略
- [ ] 更新 Pydantic 模型

---

### Stage 4: 前端集成

**文件结构**:
```
frontend/src/lib/
├── services/
│   └── paymentService.ts         # 支付 API 客户端
├── types/
│   └── payment.ts                # 支付类型定义
└── components/payroll/
    ├── PaymentStatusBadge.svelte # 支付状态显示
    └── PaymentConfirmModal.svelte # 支付确认弹窗
```

**UI 变更**:
- [ ] Payroll Run 审批页面添加「发起支付」按钮
- [ ] 支付确认弹窗 (显示金额明细)
- [ ] 支付状态实时显示
- [ ] 支付历史记录页面

---

### Stage 5: 测试与上线

**测试流程**:
1. Sandbox 环境完整流程测试
2. 小额真实支付测试 ($1)
3. 完整 Payroll Run 测试
4. 错误场景测试 (余额不足、账户错误等)

**任务**:
- [ ] 编写单元测试
- [ ] Sandbox 集成测试
- [ ] 生产环境配置
- [ ] 监控和告警设置

---

## 🔐 安全考虑

### 银行账户信息
- 公司银行账户信息加密存储
- 员工银行账户信息通过 Plooto 管理 (减少 PCI 合规负担)

### API 密钥
- 存储在环境变量，不提交到代码库
- 生产/测试环境分离

### 支付授权
- 双重确认 (计算 → 审批 → 支付确认)
- 支付操作记录审计日志

---

## 📚 参考链接

- [Plooto 官网](https://www.plooto.com)
- [Plooto 定价](https://www.plooto.com/pricing)
- [Plooto CRA 支付](https://www.plooto.com/features/online-cra-payments)
- [Plooto API 文档](https://www.plooto.com) *(待获取正式 API 文档链接)*
- [Payments Canada PAD 规则](https://www.payments.ca/sites/default/files/h1eng.pdf)

---

## 🔄 备选方案

如果 Plooto 不满足需求，可考虑：

| 方案 | 优点 | 缺点 |
|------|------|------|
| **VoPay** | API 更强大，同日到账 | 月费 $500 起 |
| **Rotessa** | 免费/低成本 | 仅支持收款，不支持发薪 |
| **直接银行集成** | 无中间商 | 开发复杂，需单独谈判 |
| **自打印支票** | 最便宜 | 麻烦，需要 MICR 打印机 |

---

## ✅ 完成标准

- [ ] 可以从公司账户发起 PAD 扣款
- [ ] 可以批量向员工发放 EFT 工资
- [ ] 可以自动向 CRA 汇款
- [ ] 支付状态可追踪
- [ ] 支付失败有告警和重试机制
- [ ] 支付记录与 Beancount 分录联动

---

**Next**: 此阶段为未来规划，待核心 Payroll 功能稳定后实施。
