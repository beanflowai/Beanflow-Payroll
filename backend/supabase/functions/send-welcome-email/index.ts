// Supabase Edge Function: Send Welcome Email
// Triggered by Database Webhook when a new user is created in auth.users

import { serve } from "https://deno.land/std@0.168.0/http/server.ts";

const RESEND_API_KEY = Deno.env.get("RESEND_API_KEY");

interface WebhookPayload {
  type: "INSERT" | "UPDATE" | "DELETE";
  table: string;
  record: {
    id: string;
    email: string;
    created_at: string;
    raw_user_meta_data?: {
      full_name?: string;
      name?: string;
      avatar_url?: string;
      provider?: string;
      [key: string]: unknown;
    };
    [key: string]: unknown;
  };
  schema: string;
  old_record: null | Record<string, unknown>;
}

function createWelcomeEmailText(userName?: string): string {
  const videoUrl = "https://youtu.be/_yjmnaa1wk8";
  const supportUrl = "https://support.beanflow.ai";
  const greeting = userName ? `Hi ${userName},` : "Hi,";

  return `${greeting}

I'm Martin, founder of BeanFlow — thanks so much for signing up!

We started BeanFlow Payroll because running payroll in Canada shouldn't require a CPA degree.
CPP, EI, and federal/provincial taxes are complicated — we handle the complexity so you can focus on your team, not paperwork.

Getting started takes just 5 simple steps:

1. Create your company profile
2. Set up pay groups (weekly, bi-weekly, monthly)
3. Add your employees
4. Assign them to pay groups
5. Run your first payroll

📺 Watch our quick setup video:
${videoUrl}

We just launched and are actively improving BeanFlow every day.
If you have any questions or run into any issues, please submit a ticket at:
👉 ${supportUrl}
 — we'll get back to you quickly.

P.S. I'd love to learn more about you — what made you look for a new payroll solution?
Was it cost, complexity, or something else? Just hit "Reply" — I read and reply to every email.

Cheers,
Martin
Founder, BeanFlow`;
}

async function sendWelcomeEmail(email: string, userName?: string): Promise<{ success: boolean; error?: string }> {
  if (!RESEND_API_KEY) {
    console.error("RESEND_API_KEY not configured");
    return { success: false, error: "RESEND_API_KEY not configured" };
  }

  const textContent = createWelcomeEmailText(userName);

  try {
    const res = await fetch("https://api.resend.com/emails", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${RESEND_API_KEY}`,
      },
      body: JSON.stringify({
        from: "Martin Sun <martin.sun@beanflow.ai>",
        to: [email],
        subject: "Welcome to BeanFlow Payroll 👋 Let's get your first payroll running",
        text: textContent,
      }),
    });

    if (!res.ok) {
      const errorData = await res.text();
      console.error("Resend API error:", errorData);
      return { success: false, error: `Resend API error: ${res.status}` };
    }

    const data = await res.json();
    console.log("Email sent successfully:", data);
    return { success: true };
  } catch (error) {
    console.error("Failed to send email:", error);
    return { success: false, error: String(error) };
  }
}

serve(async (req) => {
  // Handle CORS preflight
  if (req.method === "OPTIONS") {
    return new Response("ok", {
      headers: {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "POST, OPTIONS",
        "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
      },
    });
  }

  try {
    // Parse the webhook payload
    const payload: WebhookPayload = await req.json();

    console.log("Received webhook:", {
      type: payload.type,
      table: payload.table,
      userId: payload.record?.id,
      email: payload.record?.email,
      userName: payload.record?.raw_user_meta_data?.full_name || payload.record?.raw_user_meta_data?.name,
    });

    // Only process INSERT events on auth.users
    if (payload.type !== "INSERT") {
      return new Response(
        JSON.stringify({ message: "Ignored: not an INSERT event" }),
        { status: 200, headers: { "Content-Type": "application/json" } }
      );
    }

    const { email, id: userId, raw_user_meta_data } = payload.record;
    const userName = raw_user_meta_data?.full_name || raw_user_meta_data?.name;

    if (!email) {
      console.warn(`User ${userId} has no email, skipping welcome email`);
      return new Response(
        JSON.stringify({ message: "Skipped: no email address" }),
        { status: 200, headers: { "Content-Type": "application/json" } }
      );
    }

    // Send welcome email
    const result = await sendWelcomeEmail(email, userName);

    if (result.success) {
      console.log(`Welcome email sent to user ${userId} (${email})${userName ? ` (${userName})` : ''}`);
      return new Response(
        JSON.stringify({ success: true, message: "Welcome email sent" }),
        { status: 200, headers: { "Content-Type": "application/json" } }
      );
    } else {
      console.error(`Failed to send welcome email to ${userId}: ${result.error}`);
      return new Response(
        JSON.stringify({ success: false, error: result.error }),
        { status: 200, headers: { "Content-Type": "application/json" } }
      );
    }
  } catch (error) {
    console.error("Error processing webhook:", error);
    return new Response(
      JSON.stringify({ error: String(error) }),
      { status: 500, headers: { "Content-Type": "application/json" } }
    );
  }
});
