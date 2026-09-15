import domainPacks from "@/config/domain-packs.json";
import contentFormats from "@/config/content-formats.json";
import editStyles from "@/config/edit-styles.json";

export function getDomainPack(id = "custom") {
  return domainPacks.find((item) => item.id === id) || domainPacks[0];
}

export function getContentFormat(id = "evidence-explainer") {
  return contentFormats.find((item) => item.id === id) || contentFormats[0];
}

export function getEditStyle(id = "clean-expert") {
  return editStyles.find((item) => item.id === id) || editStyles[0];
}

export function buildDomainContext(input = {}) {
  const domain = getDomainPack(input.domainId);
  const format = getContentFormat(input.formatId);
  return {domain, format, niche: String(input.niche || domain.niche).trim(), audience: String(input.audience || domain.audience).trim(), voice: String(input.voice || domain.voice).trim()};
}

export function buildScriptBrief(input = {}) {
  const context = buildDomainContext(input);
  return [
    `Ngành: ${context.domain.name}`,
    `Ngách cụ thể: ${context.niche}`,
    `Khán giả: ${context.audience}`,
    `Giọng thương hiệu: ${context.voice}`,
    `Format: ${context.format.name}`,
    `Cấu trúc: ${context.format.structure.join(" → ")}`,
    `Bằng chứng ưu tiên: ${context.domain.proofTypes.join(", ")}`,
    `Ràng buộc: ${context.domain.compliance.join("; ")}`,
    context.domain.disclaimer ? `Disclaimer: ${context.domain.disclaimer}` : ""
  ].filter(Boolean).join("\n");
}

export function recommendedStyleIds(domainId = "custom", formatId = "evidence-explainer") {
  const domain = getDomainPack(domainId);
  const formatMap = {"visual-metaphor":["visual-metaphor","warm-story"],"untold-story":["documentary-reveal","editorial-proof"],"jenga-tension":["data-kinetic","bold-social"],"product-demo":["screen-demo","tiktok-creator"],"case-study":["clean-expert","warm-story"]};
  return [...new Set([domain.defaultStyle, ...(formatMap[formatId] || [])])];
}
