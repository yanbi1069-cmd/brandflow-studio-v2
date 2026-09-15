const DEFAULT_LOCAL_AGENT_URL = "http://127.0.0.1:8765";

export function localAgentUrl() {
  const value = process.env.BRANDFLOW_LOCAL_AGENT_URL || DEFAULT_LOCAL_AGENT_URL;
  const url = new URL(value);
  if (url.protocol !== "http:" || !["127.0.0.1", "localhost"].includes(url.hostname)) {
    throw new Error("BRANDFLOW_LOCAL_AGENT_URL chỉ được trỏ tới localhost qua HTTP.");
  }
  return url.origin;
}

export async function localAgentJson(path, init = {}) {
  let response;
  try {
    response = await fetch(`${localAgentUrl()}${path}`, {
      ...init,
      cache: "no-store",
      headers: {
        "Content-Type": "application/json",
        "X-BrandFlow-Agent": "1",
        ...(init.headers || {}),
      },
    });
  } catch {
    throw new Error("Local-agent chưa chạy. Hãy dùng `npm run dev:full` hoặc chạy `python local-agent/app.py`.");
  }
  const data = await response.json().catch(() => ({}));
  if (!response.ok || data.ok === false) throw new Error(data.error || `Local-agent trả HTTP ${response.status}`);
  return data;
}
