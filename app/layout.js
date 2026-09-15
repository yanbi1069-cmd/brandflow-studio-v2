import "./globals.css";

export const metadata = {
  title: "BrandFlow Executive Studio",
  description: "Nền tảng AI xây dựng video thương hiệu cá nhân cho chuyên gia và doanh nhân",
};

export default function RootLayout({ children }) {
  return (
    <html lang="vi">
      <body>{children}</body>
    </html>
  );
}
