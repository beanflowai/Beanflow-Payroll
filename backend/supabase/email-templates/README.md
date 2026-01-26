# BeanFlow Payroll Email Templates

This directory contains email templates for Supabase Auth and reference templates.

## Email Flow Overview

| 场景 | 发送方式 | 模板 |
|------|----------|------|
| 邀请新用户 | Supabase `invite_user_by_email()` | Supabase **Invite** 模板 |
| 邀请已存在用户 | **Resend API** (自定义) | `email_service.py` 中的模板 |
| 登录请求验证码 | Supabase `signInWithOtp()` | Supabase **Magic Link** 模板 |

## Supabase Templates

### Magic Link (`magic_link.html`)
- **用途**: 用户在登录页点击 "Send Verification Code" 时发送
- **内容**: 显示 OTP 验证码
- **配置位置**: Supabase Dashboard → Authentication → Email Templates → Magic link

### Invite (`invite.html`)
- **用途**: 邀请新用户（首次邀请，邮箱不在 Auth 系统中）
- **内容**: 欢迎信息 + 确认链接
- **配置位置**: Supabase Dashboard → Authentication → Email Templates → Invite user

### Confirm Signup (`confirm_signup.html`)
- **用途**: 新用户注册确认
- **配置位置**: Supabase Dashboard → Authentication → Email Templates → Confirm signup

## Custom Email (via Resend)

对于已存在用户的邀请，使用 `app/services/email_service.py` 中的 `send_employee_portal_invite_email()` 方法发送自定义邮件。

**配置环境变量**:
```env
RESEND_EMAIL_API_KEY=re_xxx
EMAIL_FROM_ADDRESS=noreply@beanflow.ai
EMAIL_FROM_NAME=BeanFlow
```

## How to Configure Supabase Templates

1. Go to **Authentication** → **Email Templates**
2. Copy the HTML content from the template file
3. Paste into the corresponding template editor
4. Click **Save changes**

## Template Variables (Supabase)

| Variable | Description |
|----------|-------------|
| `{{ .Token }}` | OTP verification code |
| `{{ .ConfirmationURL }}` | Magic link / confirmation URL |
| `{{ .Email }}` | User's email address |
| `{{ .SiteURL }}` | Configured site URL |
