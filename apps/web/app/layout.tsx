import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "QURAN AI — Quran Reader",
  description: "อ่านอัลกุรอานและศึกษาความหมายจากแหล่งข้อมูลที่ตรวจสอบได้",
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
