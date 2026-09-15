import { buildDemoScript } from "./demo-data";

function cleanJsonBlock(text) {
  const fenced = text.match(/```(?:json)?\s*([\s\S]*?)```/i);
  const candidate = fenced ? fenced[1] : text.slice(text.indexOf("{"), text.lastIndexOf("}") + 1);
  return JSON.parse(candidate);
}

export async function generateScript(input) {
  const apiKey = process.env.KYMA_API_KEY;
  if (!apiKey) return buildDemoScript(input);

  const system = `Bạn là biên kịch video ngắn tiếng Việt cho thương hiệu cá nhân. Viết tự nhiên, có quan điểm, không sao chép nguồn tham chiếu, không hứa hẹn tuyệt đối. Chỉ trả JSON hợp lệ gồm hook, body, cta.`;
  const user = `Thương hiệu: ${input.brandName || "Chưa đặt tên"}\nNgách: ${input.niche}\nKhán giả: ${input.audience}\nGiọng thương hiệu: ${input.voice}\nChủ đề tham chiếu: ${input.trendTitle}\nHook tham chiếu: ${input.trendHook}\nYêu cầu: video 45-60 giây, một ý chính, hook dưới 18 từ, body có ví dụ hoặc bằng chứng, CTA mềm.`;

  const response = await fetch("https://kymaapi.com/v1/chat/completions", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${apiKey}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      model: process.env.KYMA_MODEL || "gemini-2.5-flash",
      messages: [
        { role: "system", content: system },
        { role: "user", content: user },
      ],
      temperature: 0.7,
    }),
  });

  if (!response.ok) throw new Error(`Kyma API trả về HTTP ${response.status}`);
  const payload = await response.json();
  const parsed = cleanJsonBlock(payload?.choices?.[0]?.message?.content || "");
  return {
    hook: String(parsed.hook || "").trim(),
    body: String(parsed.body || "").trim(),
    cta: String(parsed.cta || "").trim(),
    sourceMode: "live",
    model: process.env.KYMA_MODEL || "gemini-2.5-flash",
  };
}
