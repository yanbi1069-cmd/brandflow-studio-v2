import { localAgentJson } from "@/lib/local-agent-client";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET(_request, { params }) {
  try {
    const { jobId } = await params;
    if (!/^[a-f0-9]{12}$/i.test(jobId)) return Response.json({ error: "Job ID không hợp lệ." }, { status: 400 });
    const data = await localAgentJson(`/api/jobs/${jobId}`);
    return Response.json(data);
  } catch (error) {
    return Response.json({ error: error.message }, { status: 502 });
  }
}
