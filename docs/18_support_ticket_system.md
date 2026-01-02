# Support Ticket System

## Overview

用户支持工单系统，允许用户提交问题报告、疑问等，支持文字描述和图片上传。

## Design Decision

### 为什么自建而非使用第三方开源系统？

| 方案 | 评估 |
|------|------|
| **FreeScout/Helpy** | 需额外部署 PHP 系统，与现有 Python/Svelte 技术栈不一致，认证同步复杂 |
| **osTicket** | 同样需要 PHP，用户需跳转外部系统，体验差 |
| **自建（推荐）** | 完全集成、技术栈统一、利用现有 Supabase Storage 和 RLS |

**结论**：需求简单（文字+图片），自建更合适。

---

## Functional Requirements

### 用户功能
- 提交 Ticket（标题、描述、上传图片）
- 查看自己的 Ticket 列表
- 查看 Ticket 详情和回复
- 只能看到自己提交的 Ticket（RLS 隔离）

### 管理员功能（后续可扩展）
- 查看所有 Ticket
- 回复 Ticket
- 更改 Ticket 状态

---

## Database Schema

### Tables

```sql
-- 工单主表
CREATE TABLE support_tickets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,           -- 提交者 (Supabase Auth UID)
    company_id UUID REFERENCES companies(id),
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    status TEXT DEFAULT 'open' CHECK (status IN ('open', 'in_progress', 'resolved', 'closed')),
    priority TEXT DEFAULT 'normal' CHECK (priority IN ('low', 'normal', 'high', 'urgent')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 附件表（图片）
CREATE TABLE ticket_attachments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ticket_id UUID REFERENCES support_tickets(id) ON DELETE CASCADE,
    file_name TEXT NOT NULL,
    storage_key TEXT NOT NULL,       -- Supabase Storage key
    file_size INTEGER,
    mime_type TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 回复表
CREATE TABLE ticket_replies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ticket_id UUID REFERENCES support_tickets(id) ON DELETE CASCADE,
    user_id TEXT NOT NULL,
    is_staff BOOLEAN DEFAULT FALSE,  -- 区分用户回复和管理员回复
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### RLS Policies

```sql
-- 用户只能查看和创建自己的 ticket
ALTER TABLE support_tickets ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own tickets" ON support_tickets
    FOR SELECT USING (auth.uid()::text = user_id);

CREATE POLICY "Users can insert own tickets" ON support_tickets
    FOR INSERT WITH CHECK (auth.uid()::text = user_id);

-- 附件和回复继承 ticket 的权限
ALTER TABLE ticket_attachments ENABLE ROW LEVEL SECURITY;
ALTER TABLE ticket_replies ENABLE ROW LEVEL SECURITY;
```

### Indexes

```sql
CREATE INDEX idx_tickets_user_id ON support_tickets(user_id);
CREATE INDEX idx_tickets_status ON support_tickets(status);
CREATE INDEX idx_tickets_created_at ON support_tickets(created_at DESC);
```

---

## API Design

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/tickets` | 创建 Ticket |
| `GET` | `/api/v1/tickets` | 获取用户的 Ticket 列表 |
| `GET` | `/api/v1/tickets/{id}` | 获取 Ticket 详情 |
| `POST` | `/api/v1/tickets/{id}/attachments` | 上传附件图片 |
| `POST` | `/api/v1/tickets/{id}/replies` | 添加回复 |

### Request/Response Models

```python
# 创建 Ticket
class TicketCreate(BaseModel):
    title: str
    description: str
    priority: str = "normal"

# Ticket 响应
class TicketResponse(BaseModel):
    id: UUID
    title: str
    description: str
    status: str
    priority: str
    createdAt: datetime
    updatedAt: datetime
    attachments: list[AttachmentResponse]
    replyCount: int

# 附件响应
class AttachmentResponse(BaseModel):
    id: UUID
    fileName: str
    storageKey: str
    fileSize: int | None
    mimeType: str | None
    url: str  # Signed URL for download
```

---

## File Storage

使用 **Supabase Storage**：

### Storage Path
```
tickets/{user_id}/{ticket_id}/{filename}
```

### Upload Flow
1. 前端通过 Supabase JS 客户端直接上传图片到 Storage
2. 上传成功后获取 storage key
3. 创建 Ticket 时将 storage key 保存到 `ticket_attachments` 表
4. 显示时通过 storage key 生成签名 URL

### Supported File Types
- Images: `image/jpeg`, `image/png`, `image/gif`, `image/webp`
- Max file size: 5MB per file
- Max files per ticket: 5

---

## Frontend Structure

### Routes

```
frontend/src/routes/(app)/support/
├── +page.svelte          # Ticket 列表页
├── new/
│   └── +page.svelte      # 新建 Ticket 页
└── [id]/
    └── +page.svelte      # Ticket 详情页
```

### Components

```
frontend/src/lib/components/support/
├── TicketList.svelte         # Ticket 列表组件
├── TicketCard.svelte         # 单个 Ticket 卡片
├── TicketForm.svelte         # 创建/编辑表单
├── TicketDetail.svelte       # 详情显示
├── ImageUploader.svelte      # 图片上传组件
└── ReplySection.svelte       # 回复区域
```

### Services & Types

```
frontend/src/lib/services/ticketService.ts   # API 调用
frontend/src/lib/types/ticket.ts             # TypeScript 类型
```

---

## UI Design

### Ticket List Page
- 显示用户所有 Ticket
- 按创建时间倒序
- 状态筛选：All / Open / In Progress / Resolved / Closed
- 每个卡片显示：标题、状态标签、创建时间、回复数

### New Ticket Page
- 表单字段：标题（必填）、描述（必填）、优先级（下拉）
- 图片上传区：拖拽或点击上传，支持多图
- 图片预览和删除

### Ticket Detail Page
- 显示完整描述
- 图片画廊（点击放大）
- 回复历史（时间线形式）
- 添加回复输入框

---

## Implementation Files

| Type | Path | Description |
|------|------|-------------|
| Migration | `backend/supabase/migrations/20260102200000_add_ticket_tables.sql` | 数据库结构 |
| Model | `backend/app/models/ticket.py` | Pydantic 模型 |
| API | `backend/app/api/v1/tickets.py` | API 端点 |
| Service | `backend/app/services/ticket_service.py` | 业务逻辑 |
| Types | `frontend/src/lib/types/ticket.ts` | TS 类型 |
| Service | `frontend/src/lib/services/ticketService.ts` | 前端 API |
| Pages | `frontend/src/routes/(app)/support/` | 页面组件 |
| Components | `frontend/src/lib/components/support/` | UI 组件 |

---

## Future Enhancements

- Email 通知（新回复时）
- 管理员面板
- Ticket 分类/标签
- 搜索功能
- 导出功能
