import { localAgentJson } from "@/lib/local-agent-client";

export const runtime = "nodejs";

export async function POST(request) {
  try {
    const input = await request.json();
    let projectId = String(input.projectId || "");
    if (!projectId && input.voiceSource !== "recorded") {
      const created = await localAgentJson("/api/projects", {
        method: "POST",
        body: JSON.stringify({ title: input.script?.hook || "No-face video", domain_id: input.domainId || "general", style_id: input.styleId || "editorial-proof" }),
      });
      projectId = created.project.id;
      const text = String(input.script?.text || [input.script?.hook, input.script?.body, input.script?.cta].filter(Boolean).join("\n\n")).trim();
      await localAgentJson("/api/scripts/approve", {
        method: "POST",
        body: JSON.stringify({ project_id: projectId, script_id: input.script?.id || "web-approved", text, approved_at: new Date().toISOString() }),
      });
    }
    if (!/^[a-f0-9]{12}$/i.test(projectId)) {
      return Response.json({ error: "Project ID không hợp lệ." }, { status: 400 });
    }
    const scenes = [input.script?.hook, input.script?.body, input.script?.cta]
      .filter(Boolean)
      .map((text) => ({ text }));
    const data = await localAgentJson("/api/noface", {
      method: "POST",
      body: JSON.stringify({
        project_id: projectId,
        voice_source: input.voiceSource || "tts",
        confirmed: Boolean(input.confirmed),
        heygen_key: request.headers.get("x-heygen-key") || "",
        voice_id: input.voiceId || "",
        avatar_ids: input.avatarIds?.length ? input.avatarIds : String(process.env.HEYGEN_AVATAR_ID || "").split(",").map((value) => value.trim()).filter(Boolean),
        test: Boolean(input.test),
        source_file: input.sourceFile || "",
        voice: input.voice || "vi-VN-HoaiMyNeural",
        speed: Number(input.speed || 1),
        style: input.styleId || "editorial-proof",
        target_seconds: Number(input.targetSeconds || 55),
        visual_mix: input.visualMix || "50 / 30 / 20",
        scenes,
      }),
    });
    return Response.json({ ...data, projectId }, { status: 202 });
  } catch (error) {
    return Response.json({ error: error.message || "Không thể chuẩn bị video no-face." }, { status: 502 });
  }
}
