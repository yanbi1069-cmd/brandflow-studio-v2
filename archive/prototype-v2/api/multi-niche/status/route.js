export const runtime = "nodejs";

export async function GET() {
  const services = {
    research: { provider: "Apify", configured: Boolean(process.env.APIFY_API_TOKEN) },
    script: { provider: "Kyma", configured: Boolean(process.env.KYMA_API_KEY) },
    avatar: { provider: "HeyGen", configured: Boolean(process.env.HEYGEN_API_KEY) }
  };
  return Response.json({
    mode: Object.values(services).some((item) => item.configured) ? "hybrid" : "demo",
    services,
    note: "API keys are never returned. Configured only indicates whether a local environment variable exists."
  });
}
