import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "QURAN AI — อ่านและศึกษาอัลกุรอาน",
  description:
    "พื้นที่อ่านอัลกุรอานและศึกษาตัฟซีรอย่างรอบคอบ พร้อมแสดงที่มาและสถานะหลักฐานอย่างโปร่งใส",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="th">
      <body>{children}</body>
    </html>
  );
}
