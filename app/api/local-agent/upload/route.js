import { localAgentJson, localAgentUrl } from "@/lib/local-agent-client";

export const runtime = "nodejs";
export const maxDuration = 300;

export async function POST(request) {
  try {
    const filename = decodeURIComponent(String(request.headers.get("x-filename") || "source.mp4")).replace(/[\r\n]/g, "").slice(0, 150);
    const title = decodeURIComponent(String(request.headers.get("x-title") || encodeURIComponent(filename))).slice(0, 180);
    const domainId = String(request.headers.get("x-domain-id") || "general");
    const styleId = String(request.headers.get("x-style-id") || "editorial-proof");
    const kind = String(request.headers.get("x-upload-kind") || "source");
    const length = Number(request.headers.get("content-length") || 0);
    if (!request.body || !length) return Response.json({ error: "File upload trống." }, { status: 400 });
    const created = await localAgentJson("/api/projects", {
      method: "POST",
      body: JSON.stringify({ title, domain_id: domainId, style_id: styleId }),
    });
    const projectId = created.project.id;
    const uploaded = await fetch(`${localAgentUrl()}/api/upload`, {
      method: "POST",
      headers: {
        "X-BrandFlow-Agent": "1",
        "X-Project-ID": projectId,
        "X-Filename": encodeURIComponent(filename),
        "X-Upload-Kind": kind,
        "Content-Type": request.headers.get("content-type") || "application/octet-stream",
        "Content-Length": String(length),
      },
      body: request.body,
      duplex: "half",
    });
    const data = await uploaded.json().catch(() => ({}));
    if (!uploaded.ok) throw new Error(data.error || `Local-agent upload HTTP ${uploaded.status}`);
    return Response.json({ ok: true, projectId, file: data.file, size: data.size }, { status: 201 });
  } catch (error) {
    return Response.json({ error: error.message || "Không thể tải file vào local-agent." }, { status: 502 });
  }
}
