export const DEMO_TRENDS = [
  {
    id: "trend-01",
    title: "Sai lầm khiến nội dung chuyên môn mãi không tạo ra khách hàng",
    channel: "The Expert Lab",
    views: 284000,
    subscribers: 18200,
    breakout: 15.6,
    duration: "00:47",
    hook: "Đừng đăng thêm một video nào nếu nội dung của bạn vẫn thiếu điều này.",
    angle: "Phá bỏ một thói quen phổ biến",
  },
  {
    id: "trend-02",
    title: "Công thức 3 tầng biến kiến thức khó thành video dễ hiểu",
    channel: "Creator Systems",
    views: 176000,
    subscribers: 12100,
    breakout: 14.5,
    duration: "00:54",
    hook: "Kiến thức càng khó, bạn càng không nên giải thích ngay.",
    angle: "Khung giải thích 3 tầng",
  },
  {
    id: "trend-03",
    title: "Một phút để khách hàng hiểu vì sao họ cần chuyên gia",
    channel: "Founder Notes",
    views: 94000,
    subscribers: 8300,
    breakout: 11.3,
    duration: "00:42",
    hook: "Khách hàng không mua kiến thức. Họ mua một quyết định dễ dàng hơn.",
    angle: "Insight ngược chiều",
  },
];

export function tailorTrends(niche = "thương hiệu cá nhân") {
  const label = niche.trim() || "thương hiệu cá nhân";
  return DEMO_TRENDS.map((trend, index) => ({
    ...trend,
    title: index === 0
      ? `3 sai lầm người làm ${label} thường bỏ qua`
      : index === 1
        ? `Cách giải thích ${label} để người xem hiểu trong 45 giây`
        : `Góc nhìn ít người nói về ${label}`,
    niche: label,
  }));
}

export function buildDemoScript({ niche, audience, brandName, trendTitle }) {
  const subject = niche || "lĩnh vực của bạn";
  const viewer = audience || "khách hàng mục tiêu";
  const brand = brandName || "thương hiệu của bạn";
  return {
    hook: `Nếu bạn đang làm ${subject} mà video đăng đều vẫn không có khách, vấn đề có thể không nằm ở lượt xem.`,
    body: `Phần lớn nội dung chỉ cố nói thật nhiều kiến thức. Nhưng ${viewer} không cần thêm thông tin; họ cần nhìn thấy một vấn đề của chính mình, hiểu vì sao cách cũ chưa hiệu quả và biết bước tiếp theo nên làm gì. Hãy giữ mỗi video ở một ý duy nhất: mở bằng tình huống thật, đưa một bằng chứng dễ hiểu, rồi chốt bằng một hành động nhỏ. Đây cũng là cấu trúc được rút ra từ chủ đề “${trendTitle || "nội dung đang tăng trưởng"}”, nhưng được viết lại theo góc nhìn riêng của ${brand}.`,
    cta: `Lưu video này và theo dõi ${brand} để nhận thêm những hướng dẫn có thể áp dụng ngay.`,
    sourceMode: "demo",
    model: "BrandFlow demo engine",
  };
}
