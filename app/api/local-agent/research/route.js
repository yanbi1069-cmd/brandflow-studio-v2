import { localAgentJson } from "@/lib/local-agent-client";

export const runtime = "nodejs";

export async function POST(request) {
  try {
    const input = await request.json();
    const data = await localAgentJson("/api/research", {
      method: "POST",
      body: JSON.stringify({
        ...input,
        mode: "live",
        apify_token: request.headers.get("x-apify-token") || "",
        kyma_key: request.headers.get("x-kyma-key") || "",
      }),
    });
    return Response.json(data, { status: 202 });
  } catch (error) {
    return Response.json({ error: error.message || "Không thể bắt đầu nghiên cứu." }, { status: 502 });
  }
}
