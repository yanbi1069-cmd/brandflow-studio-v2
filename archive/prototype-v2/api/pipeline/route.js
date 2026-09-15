export async function POST(request) {
  const project = await request.json();
  const jobId = `BF-${Date.now().toString(36).toUpperCase()}`;
  return Response.json({
    jobId,
    status: "ready",
    mode: process.env.HEYGEN_API_KEY ? "production-ready" : "demo",
    manifest: {
      schemaVersion: "1.0",
      createdAt: new Date().toISOString(),
      project: {
        id: jobId,
        brand: project.brand,
        niche: project.niche,
        format: "vertical-9:16",
        targetDurationSec: 55,
      },
      source: project.source,
      script: project.script,
      production: project.production,
      qa: {
        captionSafeArea: true,
        maxCaptionLines: 2,
        requireNoFlashFrames: true,
        requireVoiceAlignment: true,
        maxDurationSec: 60,
      },
    },
  });
}
