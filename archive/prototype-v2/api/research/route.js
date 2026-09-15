import { tailorTrends } from "@/lib/demo-data";

export const runtime = "nodejs";

function parseDuration(value = "") {
  const parts = String(value).split(":").map(Number);
  return parts.reduce((total, part) => total * 60 + (Number.isFinite(part) ? part : 0), 0);
}

export async function POST(request) {
  const { niche = "" } = await request.json();
  if (!niche.trim()) return Response.json({ error: "Hãy nhập ngành hoặc chủ đề cần research." }, { status: 400 });

  const token = process.env.APIFY_API_TOKEN;
  if (!token) return Response.json({ items: tailorTrends(niche), mode: "demo" });

  try {
    const endpoint = new URL("https://api.apify.com/v2/acts/streamers~youtube-scraper/run-sync-get-dataset-items");
    endpoint.searchParams.set("token", token);
    endpoint.searchParams.set("timeout", "120");
    const response = await fetch(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        searchQueries: [niche],
        maxResults: 8,
        maxResultsShorts: 12,
        maxResultStreams: 0,
        videoType: "video",
        dateFilter: "year",
      }),
    });
    if (!response.ok) throw new Error(`Apify HTTP ${response.status}`);
    const rows = await response.json();
    const items = rows
      .map((row, index) => {
        const views = Number(row.viewCount || 0);
        const subscribers = Number(row.numberOfSubscribers || 0);
        return {
          id: row.id || `live-${index}`,
          title: row.title || "Video không có tiêu đề",
          channel: row.channelName || "YouTube",
          views,
          subscribers,
          breakout: subscribers ? Math.round((views / subscribers) * 10) / 10 : 0,
          duration: row.duration || "—",
          durationSeconds: parseDuration(row.duration),
          hook: row.title || "",
          angle: "Nguồn đang tăng trưởng",
          url: row.url || "",
          thumbnail: row.thumbnailUrl || "",
        };
      })
      .filter((item) => item.views >= 3000)
      .sort((a, b) => b.breakout - a.breakout)
      .slice(0, 6);
    return Response.json({ items: items.length ? items : tailorTrends(niche), mode: items.length ? "live" : "demo" });
  } catch (error) {
    return Response.json({ items: tailorTrends(niche), mode: "demo", warning: error.message });
  }
}
