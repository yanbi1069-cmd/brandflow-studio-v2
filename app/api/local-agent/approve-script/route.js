import { localAgentJson } from "@/lib/local-agent-client";

export const runtime = "nodejs";

export async function POST(request) {
  try {
    const input = await request.json();
    if (!/^[a-f0-9]{12}$/i.test(String(input.projectId || ""))) return Response.json({ error: "Project ID không hợp lệ." }, { status: 400 });
    const text = String(input.script?.text || [input.script?.hook, input.script?.body, input.script?.cta].filter(Boolean).join("\n\n")).trim();
    if (!text) return Response.json({ error: "Kịch bản không được để trống." }, { status: 400 });
    const data = await localAgentJson("/api/scripts/approve", { method: "POST", body: JSON.stringify({ project_id: input.projectId, script_id: input.script?.id || "web-approved", text, approved_at: new Date().toISOString() }) });
    return Response.json(data);
  } catch (error) {
    return Response.json({ error: error.message || "Không thể duyệt kịch bản vào local-agent." }, { status: 502 });
  }
}
