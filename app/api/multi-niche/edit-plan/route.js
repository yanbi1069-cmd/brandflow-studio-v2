import editStyles from "@/config/edit-styles-v2.json";
import { getDomainPack } from "@/lib/domain-engine";
import { buildEditPlan } from "@/lib/finance-core-compat";

export async function POST(request) {
  const input = await request.json();
  if (!input.scriptApproved) return Response.json({ error: "Cần duyệt kịch bản trước khi tạo edit plan." }, { status: 409 });
  const style = editStyles.find((item) => item.id === input.styleId) || editStyles[0];
  const domain = getDomainPack(input.domainId);
  const plan = buildEditPlan({ script: input.script, style, domain, version: Number(input.version || 1), videoMode: input.videoMode || "avatar" });
  return Response.json({ plan, mode: "production-plan", paidAction: false });
}
