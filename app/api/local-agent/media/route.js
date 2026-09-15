import { localAgentUrl } from "@/lib/local-agent-client";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET(request) {
  const projectId = request.nextUrl.searchParams.get("projectId") || "";
  const file = request.nextUrl.searchParams.get("file") || "";
  if (!/^[a-f0-9]{12}$/i.test(projectId) || !/^[a-zA-Z0-9._-]+$/.test(file)) return Response.json({ error: "Tham số media không hợp lệ." }, { status: 400 });
  try {
    const response = await fetch(`${localAgentUrl()}/api/media?project_id=${encodeURIComponent(projectId)}&file=${encodeURIComponent(file)}`, { cache: "no-store" });
    if (!response.ok) return Response.json({ error: "Không tìm thấy video từ local-agent." }, { status: response.status });
    return new Response(response.body, { status: 200, headers: { "Content-Type": response.headers.get("content-type") || "video/mp4", "Content-Disposition": `inline; filename="${file}"`, "Cache-Control": "no-store" } });
  } catch {
    return Response.json({ error: "Local-agent chưa chạy." }, { status: 503 });
  }
}
