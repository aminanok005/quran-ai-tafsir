"use client";

import { Inter, Noto_Sans_Thai, Amiri_Quran } from 'next/font/google';

export const inter = Inter({
  subsets: ['latin'],
  variable: '--font-inter',
  display: 'swap',
});

export const notoSansThai = Noto_Sans_Thai({
  subsets: ['thai'],
  variable: '--font-thai',
  display: 'swap',
});

export const amiriQuran = Amiri_Quran({
  subsets: ['arabic'],
  weight: '400',
  variable: '--font-arabic',
  display: 'swap',
});

export const notoNaskhArabic = new (class {
  constructor() {
    // Noto Naskh Arabic will be imported via CSS
  }
})();
