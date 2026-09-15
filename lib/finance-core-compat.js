const NUMBER_KEYS = {
  views: ["views", "view_count", "viewCount", "play_count"],
  likes: ["likes", "like_count", "likeCount", "digg_count"],
  comments: ["comments", "comment_count", "commentsCount"],
  shares: ["shares", "share_count", "repost_count", "shareCount"],
};

function metric(item, keys) {
  for (const key of keys) {
    const value = Number(item?.[key]);
    if (Number.isFinite(value) && value >= 0) return value;
  }
  return 0;
}

export function compactNumber(value = 0) {
  const number = Number(value) || 0;
  if (number >= 1_000_000) return `${(number / 1_000_000).toFixed(number >= 10_000_000 ? 0 : 1)}M`;
  if (number >= 1_000) return `${(number / 1_000).toFixed(number >= 100_000 ? 0 : 1)}K`;
  return String(number);
}

export function platformFromUrl(url = "") {
  const value = String(url).toLowerCase();
  if (value.includes("youtube.com") || value.includes("youtu.be")) return "youtube";
  if (value.includes("tiktok.com")) return "tiktok";
  if (value.includes("facebook.com") || value.includes("fb.watch")) return "facebook";
  return "unknown";
}

function viralReason(row) {
  const reasons = [];
  const title = row.title.toLowerCase();
  if (["vì sao", "sai lầm", "đừng", "cách", "why", "how"].some((token) => title.includes(token))) reasons.push("hook tạo tò mò hoặc nêu pain point rõ");
  if (row.engagementPct >= 5) reasons.push("tỷ lệ tương tác cao");
  if (row.comments >= 500) reasons.push("chủ đề kích thích thảo luận");
  if (row.shares >= 1000) reasons.push("giá trị lưu và chia sẻ tốt");
  return `${(reasons.length ? reasons : ["hiệu suất nổi bật trong nhóm video được quét"]).join(", ")}.`;
}

export function normalizeResearchRows(items = [], options = {}) {
  const niche = options.niche || "thương hiệu cá nhân";
  const normalized = items.map((item, index) => {
    const views = metric(item, NUMBER_KEYS.views);
    const likes = metric(item, NUMBER_KEYS.likes);
    const comments = metric(item, NUMBER_KEYS.comments);
    const shares = metric(item, NUMBER_KEYS.shares);
    const url = String(item.webpage_url || item.url || "");
    const engagementPct = views ? Math.round(((likes + comments + shares) / views) * 10_000) / 100 : 0;
    return {
      id: String(item.id || `video-${index + 1}`),
      platform: String(item.platform || platformFromUrl(url) || "unknown"),
      channel: String(item.channel || item.channelName || item.uploader || item.authorMeta?.name || "Không rõ kênh"),
      niche,
      title: String(item.title || item.description || "Video không có tiêu đề").slice(0, 180),
      url,
      views,
      viewsText: compactNumber(views),
      likes,
      likesText: compactNumber(likes),
      comments,
      commentsText: compactNumber(comments),
      shares,
      sharesText: compactNumber(shares),
      engagementPct,
      timestamp: item.timestamp || item.release_timestamp || item.date || "",
      thumbnail: item.thumbnail || item.thumbnailUrl || "",
      duration: item.duration || "—",
      demo: Boolean(item.demo),
    };
  });
  const populatedViews = normalized.map((row) => row.views).filter(Boolean).sort((a, b) => a - b);
  const median = populatedViews.length ? populatedViews[Math.floor(populatedViews.length / 2)] : 1;
  return normalized.map((row) => {
    const relative = row.views / Math.max(1, median);
    const viralScore = Math.min(100, Math.round(45 + Math.min(relative, 4) * 10 + Math.min(row.engagementPct, 10) * 1.5));
    return { ...row, viralScore, viralReason: viralReason({ ...row, viralScore }) };
  });
}

const DEMO_METRICS = [
  ["youtube", "Chuyên gia hệ thống", 482000, 18400, 1200, 3800],
  ["tiktok", "Góc nhìn thực chiến", 1200000, 74000, 2800, 11600],
  ["facebook", "Cộng đồng chuyên môn", 316000, 9700, 846, 2100],
  ["youtube", "Giải thích bằng dữ liệu", 628000, 22600, 1800, 5400],
  ["tiktok", "Một phút dễ hiểu", 864000, 51000, 2100, 8200],
  ["facebook", "Case study Việt Nam", 271000, 8900, 704, 1900],
];

export function demoResearchRows({ niche = "thương hiệu cá nhân", keyword = "", platforms = [] } = {}) {
  const topics = [
    `3 sai lầm phổ biến khi làm ${niche}`,
    `Đừng bắt đầu ${niche} trước khi hiểu điều này`,
    `Vì sao cách làm ${niche} cũ không còn hiệu quả?`,
    `Cách giải thích ${niche} bằng một bằng chứng`,
    `Một thay đổi nhỏ tạo khác biệt trong ${niche}`,
    `Case study: biến kiến thức ${niche} thành hành động`,
  ];
  const rows = DEMO_METRICS.map(([platform, channel, views, likes, comments, shares], index) => ({
    id: `demo-${index + 1}`,
    platform,
    channel,
    title: keyword ? `${topics[index]} · ${keyword}` : topics[index],
    url: platform === "youtube" ? `https://youtube.com/watch?v=demo-${index + 1}` : platform === "tiktok" ? `https://tiktok.com/@demo/video/${index + 1}` : `https://facebook.com/reel/demo-${index + 1}`,
    views,
    likes,
    comments,
    shares,
    duration: `00:${42 + index * 2}`,
    demo: true,
  }));
  const allowed = platforms.length ? rows.filter((row) => platforms.includes(row.platform)) : rows;
  return normalizeResearchRows(allowed, { niche });
}

const RISK_RULES = [
  { id: "absolute-result", pattern: /\b(cam kết|đảm bảo|chắc chắn|100\s*%)\b.*\b(kết quả|lợi nhuận|khỏi|thắng|tăng)\b/i, label: "Cam kết kết quả tuyệt đối" },
  { id: "finance-action", pattern: /\b(mua ngay|bán ngay|all[- ]?in|không thể thua|không bao giờ lỗ)\b/i, label: "Chỉ dẫn giao dịch hoặc tuyên bố rủi ro cao" },
  { id: "medical-diagnosis", pattern: /\b(chắc chắn mắc|tự điều trị|thay thế bác sĩ|chữa khỏi hoàn toàn)\b/i, label: "Chẩn đoán hoặc điều trị thiếu thẩm quyền" },
  { id: "fabricated-proof", pattern: /\b(ai cũng|mọi khách hàng|tất cả học viên)\b.*\b(thành công|đạt được|hài lòng)\b/i, label: "Khái quát hóa bằng chứng hoặc testimonial" },
];

export function checkClaims(text = "", domain = {}) {
  const warnings = RISK_RULES.filter((rule) => rule.pattern.test(text)).map((rule) => ({ level: "warning", label: rule.label, rule: rule.id }));
  if (!warnings.length) warnings.push({ level: "ok", label: `Chưa phát hiện claim rủi ro tự động; vẫn cần kiểm tra ${domain.name || "theo ngành"}.`, rule: "manual-review" });
  return warnings;
}

function scriptText({ hook, body, cta, disclaimer }) {
  return [hook, body, cta, disclaimer].filter(Boolean).join("\n\n");
}

export function buildFinanceCompatibleScripts({ video = {}, brand = {}, domain = {}, format = {} } = {}) {
  const niche = brand.niche || domain.niche || "lĩnh vực của bạn";
  const audience = brand.audience || domain.audience || "khách hàng mục tiêu";
  const topic = video.title || niche;
  const cta = brand.cta || `Theo dõi ${brand.name || "kênh"} để xem thêm nội dung thực hành.`;
  const disclaimer = domain.disclaimer || "";
  const variants = [
    {
      id: "script-1",
      angle: "Cảnh báo trực diện",
      hook: `Nếu bạn vẫn nhìn “${topic}” theo cách cũ, có thể bạn đang bỏ qua điều quan trọng nhất.`,
      body: `Trong ${niche}, vấn đề không phải thiếu thông tin mà là thiếu một bằng chứng giúp ${audience} hiểu điều gì đang xảy ra. Hãy bắt đầu bằng một tình huống thật, chỉ ra điểm nghẽn, rồi dùng ${domain.proofTypes?.[0] || "một ví dụ cụ thể"} để chứng minh. Chỉ giữ một cơ chế và một hành động có thể thử ngay.`,
    },
    {
      id: "script-2",
      angle: "Phản trực giác",
      hook: `Điều nhiều người tin về “${topic}” chưa chắc là điều tạo ra quyết định đúng.`,
      body: `Càng cố nói nhiều kiến thức về ${niche}, người xem càng khó biết phần nào đáng tin. Cách tốt hơn là chọn một hiểu lầm, nêu rõ điều kiện áp dụng và đưa ${domain.proofTypes?.[1] || "bằng chứng trực quan"} lên màn hình. Khi người xem tự nhìn thấy cơ chế, niềm tin đến từ lập luận chứ không phải lời khẳng định.`,
    },
    {
      id: "script-3",
      angle: "Case study nhanh",
      hook: `Một thay đổi nhỏ trong cách xử lý “${topic}” có thể loại bỏ phần lớn lần làm lại.`,
      body: `Trước đây, research, kịch bản và edit về ${niche} thường dùng ba tiêu chuẩn khác nhau. Khi nguồn tham chiếu, claim, visual proof và CTA cùng nằm trong một brief, mọi cảnh đều phục vụ chung một mục tiêu. Bài học không phải dùng thêm công cụ, mà là giữ đúng hợp đồng bàn giao giữa từng bước.`,
    },
  ];
  return variants.map((item) => {
    const full = scriptText({ ...item, cta, disclaimer });
    return {
      ...item,
      cta,
      disclaimer,
      text: full,
      formatId: format.id || "evidence-explainer",
      analysis: {
        hook: "Tạo tension trong 3 giây đầu và bám video research đã duyệt.",
        body: `Một cơ chế, có trình tự và dùng ${domain.proofTypes?.join(", ") || "visual proof"}.`,
        visual: domain.proofTypes?.[0] || "Bằng chứng phù hợp với ngách",
        cta: "CTA mềm, khớp mục tiêu thương hiệu.",
      },
      claimCheck: checkClaims(full, domain),
    };
  });
}

const PROOF_CUES = /\b(\d+(?:[.,]\d+)?\s*%?|số liệu|dữ liệu|nghiên cứu|báo cáo|biểu đồ|chart|kết quả|bằng chứng|so sánh|tăng|giảm|chi phí|doanh thu|lợi nhuận|nguồn)\b/i;
const CONTEXT_CUES = /\b(khi|lúc|trước đây|hằng ngày|mỗi ngày|trải nghiệm|câu chuyện|khách hàng|đội ngũ|quy trình|thực tế|tình huống|bắt đầu|thực hiện|làm việc)\b/i;
const METAPHOR_CUES = /\b(giống như|tựa như|hình dung|chiếc|cánh cửa|cây cầu|nút thắt|đòn bẩy)\b/i;
const OPINION_CUES = /\b(tôi nghĩ|theo tôi|quan điểm|điều quan trọng|hãy nhớ|bài học)\b/i;

function classifyVisualRole(spokenMeaning, index, total) {
  if (index === 0 || index === total - 1 || OPINION_CUES.test(spokenMeaning)) return "presenter";
  if (PROOF_CUES.test(spokenMeaning)) return "proof";
  if (METAPHOR_CUES.test(spokenMeaning)) return "metaphor";
  if (CONTEXT_CUES.test(spokenMeaning)) return "context";
  return "presenter";
}

function visualRoute(role, index, domain, videoMode) {
  if (role === "proof") return {
    assetSource: domain.proofTypes?.[index % Math.max(1, domain.proofTypes?.length)] || "owned-proof",
    stockProviders: [],
    cutReason: "Luận điểm cần bằng chứng trực quan thay vì stock trang trí.",
    fallback: "presenter-fullscreen-with-proof-typography",
  };
  if (role === "context") return {
    assetSource: "owned-assets",
    stockProviders: ["pexels", "pixabay"],
    cutReason: "Câu mô tả bối cảnh hoặc hành động phù hợp B-roll đời sống.",
    fallback: "presenter-fullscreen-with-caption",
  };
  if (role === "metaphor") return {
    assetSource: "designed-visual-metaphor",
    stockProviders: [],
    cutReason: "Ẩn dụ cần một đạo cụ hoặc hành động khớp chính xác với ý thoại.",
    fallback: "presenter-fullscreen-with-keyword-typography",
  };
  return {
    assetSource: videoMode === "noface" ? "brand-typography" : "approved-source-video",
    stockProviders: [],
    cutReason: "Giữ người nói để duy trì niềm tin, chuyển ý hoặc CTA.",
    fallback: "brand-typography-with-caption",
  };
}

export function buildEditPlan({ script = {}, style = {}, domain = {}, version = 1, videoMode = "avatar" } = {}) {
  const bodyParts = String(script.body || "").split(/(?<=[.!?])\s+/).filter(Boolean);
  const segments = [script.hook, ...bodyParts, script.cta].filter(Boolean);
  const duration = 55;
  const weights = segments.map((_, index) => index === 0 ? 3 : index === segments.length - 1 ? 6 : Math.max(6, Math.floor((duration - 9) / Math.max(1, segments.length - 2))));
  const scale = duration / weights.reduce((sum, value) => sum + value, 0);
  let cursor = 0;
  const beats = segments.map((spokenMeaning, index) => {
    const start = Math.round(cursor * 10) / 10;
    cursor += weights[index] * scale;
    const end = index === segments.length - 1 ? duration : Math.round(cursor * 10) / 10;
    const role = classifyVisualRole(spokenMeaning, index, segments.length);
    const route = visualRoute(role, index, domain, videoMode);
    return {
      id: `beat-${index + 1}`,
      start,
      end,
      spokenMeaning,
      visualRole: role,
      assetSource: route.assetSource,
      stockProviders: route.stockProviders,
      cutReason: route.cutReason,
      sourceOrder: role === "context" ? ["owned-assets", "pexels", "pixabay", route.fallback] : [route.assetSource, route.fallback],
      minimumHoldSec: role === "context" ? 1.5 : role === "proof" ? 2 : 0.9,
      captionTreatment: style.caption || "clean-two-line",
      textEffect: style.textEffects?.[index % Math.max(1, style.textEffects?.length)] || "fade-rise",
      transition: style.transitions?.[index % Math.max(1, style.transitions?.length)] || "clean-cut",
      audioCue: index === 0 ? "hook-impact" : index === segments.length - 1 ? "cta-confirm" : "none",
      fallback: route.fallback,
    };
  });
  return {
    schemaVersion: "2.0",
    version,
    styleId: style.id,
    styleName: style.name,
    cutRhythm: style.cutRhythm,
    palette: style.palette,
    gsapEases: style.gsapEases || [],
    upstream: style.upstream || "brandflow",
    verification: {
      audioIsTimelineSource: true,
      semanticCutsOnly: true,
      stockIsContextOnly: true,
      stockProviderOrder: ["pexels", "pixabay"],
      returnToPresenterWhenAssetEnds: true,
      rotateTransitionFlavors: true,
      payoffHoldMinSec: 1,
      requireDraftFrameInspection: true,
      requireFinalSpotCheck: true,
    },
    targetDurationSec: duration,
    beats,
  };
}

export function sortResearchRows(rows = [], sort = "viral") {
  const key = sort === "views" ? "views" : sort === "engagement" ? "engagementPct" : "viralScore";
  return [...rows].sort((a, b) => Number(b[key] || 0) - Number(a[key] || 0));
}
