import { generateScript } from "@/lib/script-engine";

export const runtime = "nodejs";

export async function POST(request) {
  try {
    const input = await request.json();
    if (!String(input.niche || "").trim()) {
      return Response.json({ error: "Thiếu ngành hoặc chủ đề video." }, { status: 400 });
    }
    return Response.json(await generateScript(input));
  } catch (error) {
    return Response.json({ error: error.message || "Không thể tạo kịch bản." }, { status: 500 });
  }
}
