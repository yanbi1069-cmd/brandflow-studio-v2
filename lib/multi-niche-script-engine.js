import { buildDomainContext, buildScriptBrief } from "./domain-engine";
import { buildFinanceCompatibleScripts, checkClaims } from "./finance-core-compat";

const BODY_PATTERNS = {
  "evidence-explainer": ({ niche, audience }) => `Phần lớn nội dung về ${niche} chỉ đưa ra kết luận. Nhưng ${audience} cần hiểu cơ chế phía sau và nhìn thấy một bằng chứng đủ rõ. Hãy bắt đầu từ tình huống thật, chỉ ra điểm nghẽn, rồi dùng một ví dụ, số liệu hoặc demo để chứng minh. Cuối cùng, đưa ra một bước nhỏ có thể thử ngay thay vì ép người xem tin.`,
  "observation-action": ({ niche }) => `Có một thay đổi đang diễn ra trong ${niche}: người xem không còn kiên nhẫn với nội dung chung chung. Một là, chọn đúng một vấn đề. Hai là, cho họ thấy bằng chứng ngay trên màn hình. Ba là, kết thúc bằng hành động đủ nhỏ để thực hiện hôm nay. Bạn không cần làm video phức tạp; chỉ cần mỗi cảnh đều phục vụ cho một ý.`,
  "challenge-reframe": ({ niche }) => `Niềm tin phổ biến là muốn làm tốt ${niche} thì phải nói thật nhiều kiến thức. Thực tế, lượng thông tin không tạo ra niềm tin; bằng chứng phù hợp mới làm được điều đó. Thay vì cố bao quát mọi thứ, hãy chọn một hiểu lầm, giải thích vì sao nó chưa đầy đủ và dùng một tình huống thật để mở ra góc nhìn mới.`,
  "jenga-tension": ({ niche }) => `Câu hỏi đầu tiên là: điều gì thực sự tạo ra kết quả trong ${niche}? Nếu là kiến thức, vì sao nhiều người biết mà vẫn không làm được? Nếu là công cụ, vì sao đổi công cụ vẫn gặp điểm nghẽn cũ? Và nếu là kỷ luật, kỷ luật cần bám vào hệ thống nào? Câu trả lời là kết quả đến từ sự khớp nhau giữa quyết định, bằng chứng và hành động lặp lại.`,
  "visual-metaphor": ({ niche }) => `Hãy hình dung ${niche} như một chiếc bình. Thông tin là nước, còn cấu trúc là hình dáng chiếc bình. Cứ đổ thêm nước không giúp người xem cầm chắc hơn. Khi bạn chia nội dung thành vấn đề, bằng chứng và hành động, cùng lượng kiến thức đó trở nên dễ hiểu và dễ nhớ hơn.`,
  "untold-story": ({ niche }) => `Ai cũng nhìn thấy phần nổi của ${niche}: kết quả cuối cùng. Điều ít người kể là chuỗi quyết định phía sau. Một thay đổi nhỏ ở cách chọn vấn đề dẫn tới cách thu thập bằng chứng khác, rồi kéo theo toàn bộ cách trình bày. Vì vậy, điều đáng học không phải bề ngoài của một video thành công mà là logic đã tạo ra nó.`,
  "case-study": ({ niche }) => `Trước đây, nội dung ${niche} được làm theo từng công cụ riêng lẻ nên mất thời gian và khó giữ chất lượng. Điểm nghẽn không nằm ở việc thiếu AI mà ở việc thiếu tiêu chuẩn bàn giao giữa các bước. Sau khi dùng một brief chung, checkpoint duyệt và preset edit, quy trình rõ hơn và mỗi lần sửa không phải làm lại từ đầu.`,
  "product-demo": ({ niche }) => `Đây là kết quả trước tiên: từ một chủ đề ${niche}, hệ thống tạo ra brief, kịch bản và production manifest trong cùng một luồng. Bước một, chọn ngành và đối tượng. Bước hai, chọn format và bằng chứng. Bước ba, chọn style edit rồi duyệt trước khi render. Công cụ không thay quyết định của bạn; nó giữ quy trình nhất quán.`
};

export function buildMultiNicheDemoScript(input = {}) {
  const context = buildDomainContext(input);
  const bodyBuilder = BODY_PATTERNS[context.format.id] || BODY_PATTERNS["evidence-explainer"];
  const brand = input.brandName || "thương hiệu của bạn";
  return {
    hook: `Nếu bạn làm ${context.niche} mà nội dung vẫn giống mọi người, có thể vấn đề nằm ở cách bạn chứng minh.`,
    body: bodyBuilder(context),
    cta: `Lưu lại nếu bạn muốn áp dụng khung này cho ${brand}.`,
    disclaimer: context.domain.disclaimer,
    formatId: context.format.id,
    domainId: context.domain.id,
    sourceMode: "demo",
    model: "BrandFlow multi-niche demo engine"
  };
}

export function buildMultiNicheDemoScripts(input = {}) {
  const context = buildDomainContext(input);
  const candidates = buildFinanceCompatibleScripts({
    video: { title: input.trendTitle, url: input.trendUrl },
    brand: { name: input.brandName, niche: context.niche, audience: context.audience, cta: input.cta },
    domain: context.domain,
    format: context.format,
  });
  return {candidates,sourceMode:"demo",model:"BrandFlow multi-niche demo engine",domainId:context.domain.id,formatId:context.format.id};
}

function cleanJsonBlock(text) {
  const fenced = text.match(/```(?:json)?\s*([\s\S]*?)```/i);
  const raw = fenced ? fenced[1] : text;
  const arrayStart = raw.indexOf("[");
  const objectStart = raw.indexOf("{");
  const start = arrayStart >= 0 && (objectStart < 0 || arrayStart < objectStart) ? arrayStart : objectStart;
  const end = start === arrayStart ? raw.lastIndexOf("]") : raw.lastIndexOf("}");
  const candidate = raw.slice(start, end + 1);
  return JSON.parse(candidate);
}

function usefulText(value, minimum) {
  const text = String(value || "").trim();
  return text.length >= minimum && !/^[\s.…·_-]+$/.test(text);
}

export async function generateMultiNicheScript(input = {}, sessionKey = "") {
  const apiKey = sessionKey || process.env.KYMA_API_KEY;
  if (!apiKey) return buildMultiNicheDemoScripts(input);
  const context = buildDomainContext(input);
  const targetSeconds = Number(input.targetSeconds || 55);
  const system = `Bạn là biên kịch video ngắn tiếng Việt cho thương hiệu cá nhân đa ngành. Viết tự nhiên, nguyên bản, không sao chép nguồn, không bịa số liệu. Tuân thủ mọi ràng buộc theo ngành. Không bao giờ dùng dấu ba chấm, placeholder hoặc nội dung mẫu. Chỉ trả JSON object hợp lệ có field candidates là array đúng 3 phần tử; mỗi phần tử gồm id, angle, hook, body, cta, disclaimer và analysis gồm hook, body, visual, cta.`;
  const user = `${buildScriptBrief(input)}\nThương hiệu: ${input.brandName || "Chưa đặt tên"}\nChủ đề tham chiếu: ${input.trendTitle || "Tự chọn góc phù hợp"}\nLý do video nổi bật: ${input.trendHook || ""}\nThời lượng mục tiêu: ${targetSeconds} giây.\nYêu cầu: tạo đúng 3 hướng khác nhau gồm cảnh báo trực diện, phản trực giác và case study. Mỗi bản phải là kịch bản hoàn chỉnh có hook tối thiểu 12 ký tự, body tối thiểu 120 ký tự, CTA tối thiểu 8 ký tự; một ý chính, lời nói tự nhiên, có visual proof và CTA mềm. Không trả \"...\" ở bất kỳ field nào.`;
  const primaryModel = process.env.KYMA_SCRIPT_MODEL || process.env.KYMA_MODEL || "qwen-3.6-plus";
  const fallbackModel = process.env.KYMA_FALLBACK_MODEL || "deepseek-v4-flash";
  let rows;
  let usedModel = primaryModel;
  let lastError;
  for (const model of [...new Set([primaryModel, fallbackModel])]) {
    try {
      const response = await fetch("https://kymaapi.com/v1/chat/completions", {method:"POST",headers:{Authorization:`Bearer ${apiKey}`,"Content-Type":"application/json"},body:JSON.stringify({model,messages:[{role:"system",content:system},{role:"user",content:user}],temperature:0.65,max_tokens:3200,response_format:{type:"json_object"}})});
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const payload = await response.json();
      const parsed = cleanJsonBlock(payload?.choices?.[0]?.message?.content || "");
      const candidateRows = Array.isArray(parsed) ? parsed : parsed.candidates;
      if (!Array.isArray(candidateRows) || candidateRows.length !== 3) throw new Error("không trả đúng ba candidates");
      if (candidateRows.some((item) => !usefulText(item.angle, 4) || !usefulText(item.hook, 12) || !usefulText(item.body, 120) || !usefulText(item.cta, 8))) throw new Error("trả placeholder hoặc kịch bản quá ngắn");
      rows = candidateRows;
      usedModel = model;
      break;
    } catch (error) {
      lastError = error;
    }
  }
  if (!rows) throw new Error(`Kyma API không tạo được kịch bản đạt chuẩn: ${lastError?.message || "không rõ lỗi"}`);
  const candidates = rows.map((item,index)=>{
    const candidate={id:String(item.id||`script-${index+1}`),angle:String(item.angle||`Góc ${index+1}`),hook:String(item.hook||"").trim(),body:String(item.body||"").trim(),cta:String(item.cta||"").trim(),disclaimer:String(item.disclaimer||context.domain.disclaimer||"").trim(),formatId:context.format.id,domainId:context.domain.id};
    candidate.text=[candidate.hook,candidate.body,candidate.cta,candidate.disclaimer].filter(Boolean).join("\n\n");
    candidate.analysis=item.analysis||{hook:"Hook bám nguồn research đã duyệt.",body:"Một cơ chế có trình tự.",visual:context.domain.proofTypes?.[0]||"visual proof",cta:"CTA mềm theo thương hiệu."};
    candidate.claimCheck=checkClaims(candidate.text,context.domain);
    return candidate;
  });
  if (candidates.some(item=>!usefulText(item.hook,12)||!usefulText(item.body,120)||!usefulText(item.cta,8))) throw new Error("Một hoặc nhiều kịch bản không đạt chuẩn nội dung tối thiểu.");
  return {candidates,domainId:context.domain.id,formatId:context.format.id,sourceMode:"live",model:usedModel,modelRole:"script",fallbackModel};
}
