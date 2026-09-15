import { localAgentJson } from "@/lib/local-agent-client";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET() {
  try {
    const [health, settings] = await Promise.all([
      localAgentJson("/api/health"),
      localAgentJson("/api/settings"),
    ]);
    return Response.json({
      ok: true,
      agent: health,
      connections: settings.settings?.connections || {},
      defaults: {
        voiceConfigured: Boolean(process.env.HEYGEN_VOICE_ID),
        avatarConfigured: Boolean(process.env.HEYGEN_AVATAR_ID),
      },
    });
  } catch (error) {
    return Response.json({ ok: false, error: error.message }, { status: 503 });
  }
}
