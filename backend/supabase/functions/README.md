# Supabase Edge Functions

This directory contains Supabase Edge Functions for BeanFlow Payroll.

## Functions

### send-welcome-email

Sends a welcome email to new users when they register.

**Trigger:** Database Webhook on `auth.users` INSERT

## Deployment

### 1. Install Supabase CLI

```bash
npm install -g supabase
```

### 2. Login to Supabase

```bash
supabase login
```

### 3. Link to your project

```bash
cd payroll/backend
supabase link --project-ref <your-project-ref>
```

### 4. Set secrets

```bash
supabase secrets set RESEND_API_KEY=re_xxxxx
```

### 5. Deploy the function

```bash
supabase functions deploy send-welcome-email
```

## Configure Database Webhook

After deploying the function, configure the Database Webhook in Supabase Dashboard:

1. Go to **Database** → **Webhooks**
2. Click **Create a new webhook**
3. Configure:
   - **Name:** `send-welcome-email`
   - **Table:** `auth.users`
   - **Events:** `INSERT`
   - **Type:** `Supabase Edge Function`
   - **Function:** `send-welcome-email`
4. Click **Create webhook**

## Local Development

```bash
# Start local Supabase
supabase start

# Serve functions locally
supabase functions serve send-welcome-email --env-file .env.local
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `RESEND_API_KEY` | Resend API key for sending emails |

## Testing

You can test the function by creating a new user in your Supabase project or by invoking it directly:

```bash
curl -X POST 'https://<project-ref>.supabase.co/functions/v1/send-welcome-email' \
  -H 'Authorization: Bearer <anon-key>' \
  -H 'Content-Type: application/json' \
  -d '{
    "type": "INSERT",
    "table": "users",
    "schema": "auth",
    "record": {
      "id": "test-user-id",
      "email": "test@example.com",
      "created_at": "2024-01-01T00:00:00Z"
    },
    "old_record": null
  }'
```
