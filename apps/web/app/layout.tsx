import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "อัลกุรอานและตัฟซีร | Quran AI",
  description:
    "อ่านอัลกุรอาน เลือกอายะฮ์ และศึกษาคำอธิบายตัฟซีรโดยมีแหล่งอ้างอิง",
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
