import { localAgentJson } from "@/lib/local-agent-client";

export const runtime = "nodejs";

function envAvatarIds() {
  return String(process.env.HEYGEN_AVATAR_ID || "").split(/[\r\n,]+/).map((item) => item.trim()).filter(Boolean);
}

export async function POST(request) {
  try {
    const input = await request.json();
    if (!input.confirmed) return Response.json({ error: "Cần xác nhận sử dụng credit HeyGen ngay lúc render." }, { status: 409 });
    const scriptText = String(input.script?.text || [input.script?.hook, input.script?.body, input.script?.cta].filter(Boolean).join("\n\n")).trim();
    if (!scriptText) return Response.json({ error: "Chưa có kịch bản đã duyệt." }, { status: 400 });
    const voiceId = String(input.voiceId || process.env.HEYGEN_VOICE_ID || "").trim();
    const avatarIds = Array.isArray(input.avatarIds) && input.avatarIds.length ? input.avatarIds : envAvatarIds();
    if (!voiceId || !avatarIds.length) return Response.json({ error: "Thiếu HEYGEN_VOICE_ID hoặc HEYGEN_AVATAR_ID trong .env.local." }, { status: 400 });

    const created = await localAgentJson("/api/projects", {
      method: "POST",
      body: JSON.stringify({ title: input.title || input.script?.hook || "BrandFlow HeyGen", selected_video: input.source || null, domain_id: input.domainId, style_id: input.styleId }),
    });
    const projectId = created.project.id;
    await localAgentJson("/api/scripts/approve", {
      method: "POST",
      body: JSON.stringify({ project_id: projectId, script_id: input.script?.id || "web-approved", text: scriptText, approved_at: new Date().toISOString() }),
    });
    const submitted = await localAgentJson("/api/heygen", {
      method: "POST",
      body: JSON.stringify({ project_id: projectId, confirmed: true, heygen_key: request.headers.get("x-heygen-key") || "", voice_id: voiceId, avatar_ids: avatarIds, speed: Number(input.speed || 1), target_seconds: Number(input.targetSeconds || 55), requested_engine: "photo-avatar-iii", fallback_allowed: false, test: Boolean(input.test), scenes: [input.script?.hook, input.script?.body, input.script?.cta].filter(Boolean).map((text) => ({ text })) }),
    });
    return Response.json({ ok: true, projectId, job: submitted.job }, { status: 202 });
  } catch (error) {
    return Response.json({ error: error.message || "Không thể gửi HeyGen job." }, { status: 502 });
  }
}
