import { demoResearchRows, normalizeResearchRows, sortResearchRows } from "@/lib/finance-core-compat";

export const runtime = "nodejs";

function parsePlatforms(value) {
  const supported = new Set(["youtube", "tiktok", "facebook"]);
  const rows = Array.isArray(value) ? value : [];
  return rows.filter((item) => supported.has(item));
}

export async function POST(request) {
  const input = await request.json();
  const niche = String(input.niche || "").trim();
  const keyword = String(input.keyword || "").trim();
  const platforms = parsePlatforms(input.platforms);
  const sort = ["viral", "views", "engagement"].includes(input.sort) ? input.sort : "viral";
  if (!niche) return Response.json({ error: "Hãy nhập ngành hoặc chủ đề cần research." }, { status: 400 });

  const fallback = () => sortResearchRows(demoResearchRows({ niche, keyword, platforms }), sort);
  const token = request.headers.get("x-apify-token") || process.env.APIFY_API_TOKEN;
  if (!token) {
    return Response.json({ items: fallback(), mode: "demo", provider: "Finance-compatible demo dataset", note: "Demo giữ nguyên contract research; chưa gọi dịch vụ trả phí." });
  }

  if (platforms.length && !platforms.includes("youtube")) {
    return Response.json({ items: fallback(), mode: "demo", provider: "Finance-compatible demo dataset", warning: "Cloud connector hiện chỉ cấu hình YouTube; TikTok/Facebook live chạy bằng local-agent với URL kênh." });
  }

  try {
    const endpoint = new URL("https://api.apify.com/v2/acts/streamers~youtube-scraper/run-sync-get-dataset-items");
    endpoint.searchParams.set("token", token);
    endpoint.searchParams.set("timeout", "120");
    const channelUrls = Array.isArray(input.channelUrls) ? input.channelUrls.filter(Boolean) : [];
    const body = channelUrls.length
      ? { startUrls: channelUrls.map((url) => ({ url })), maxResults: 20, maxResultsShorts: 20, maxResultStreams: 0 }
      : { searchQueries: [keyword ? `${niche} ${keyword}` : niche], maxResults: 12, maxResultsShorts: 12, maxResultStreams: 0, dateFilter: "year" };
    const response = await fetch(endpoint, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
    if (!response.ok) throw new Error(`Apify HTTP ${response.status}`);
    const payload = await response.json();
    const rows = normalizeResearchRows(payload.map((row) => ({
      ...row,
      platform: "youtube",
      channel: row.channelName,
      url: row.url,
      views: row.viewCount,
      likes: row.likes || row.likeCount,
      comments: row.commentsCount || row.commentCount,
      shares: row.shareCount,
      thumbnail: row.thumbnailUrl,
    })), { niche }).filter((row) => row.views >= 3000);
    return Response.json({ items: rows.length ? sortResearchRows(rows, sort).slice(0, 20) : fallback(), mode: rows.length ? "live" : "demo", provider: rows.length ? "Apify YouTube Scraper" : "Finance-compatible demo dataset" });
  } catch (error) {
    return Response.json({ items: fallback(), mode: "demo", provider: "Finance-compatible demo dataset", warning: error.message });
  }
}
