import { localAgentJson } from "@/lib/local-agent-client";

export const runtime = "nodejs";

export async function POST(request) {
  try {
    const input = await request.json();
    if (!/^[a-f0-9]{12}$/i.test(String(input.projectId || ""))) {
      return Response.json({ error: "Project ID dựng video không hợp lệ." }, { status: 400 });
    }
    const data = await localAgentJson("/api/edit", {
      method: "POST",
      body: JSON.stringify({
        project_id: input.projectId,
        source_file: input.sourceFile,
        style_id: input.styleId,
        video_mode: input.videoMode,
        target_seconds: input.targetSeconds,
        version: input.version,
        feedback: input.feedback || "",
        footer: input.footer || "",
        text_overlay: input.textOverlay || {},
        pexels_key: request.headers.get("x-pexels-key") || "",
        pixabay_key: request.headers.get("x-pixabay-key") || "",
      }),
    });
    return Response.json(data, { status: 202 });
  } catch (error) {
    return Response.json({ error: error.message || "Không thể bắt đầu dựng video." }, { status: 502 });
  }
}
