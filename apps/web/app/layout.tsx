import { Inter } from 'next/font/google';
import type { Metadata } from 'next';

// Import the font with custom subsets
const inter = Inter({
  subsets: ['latin'],
  display: 'swap',
});

// Define the site metadata
export const metadata: Metadata = {
  title: {
    default: 'QURAN AI - Intelligent Quran Study & Tafsir Platform',
    template: '%s | QURAN AI',
  },
  description: 'Thai-first intelligent Quran study platform with classical Tafsir agents and evidence-based scholarship.',
  keywords: ['Quran', 'Tafsir', 'Islamic Studies', 'Arabic', 'Thai', 'Scholarship'],
  authors: [{ name: 'QURAN AI Team' }],
  creator: 'QURAN AI Team',
  publisher: 'QURAN AI',
  formatDetection: {
    email: false,
    address: false,
    telephone: false,
  },
  metadataBase: new URL('http://localhost:3000'),
  openGraph: {
    title: 'QURAN AI - Intelligent Quran Study & Tafsir Platform',
    description: 'Thai-first intelligent Quran study platform with classical Tafsir agents and evidence-based scholarship.',
    url: 'https://quran-ai.org',
    siteName: 'QURAN AI',
    images: [
      {
        url: '/images/og-image.jpg',
        width: 1200,
        height: 630,
        alt: 'QURAN AI - Intelligent Quran Study & Tafsir Platform',
      },
    ],
    locale: 'th_TH',
    type: 'website',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'QURAN AI - Intelligent Quran Study & Tafsir Platform',
    description: 'Thai-first intelligent Quran study platform with classical Tafsir agents and evidence-based scholarship.',
    images: ['/images/twitter-image.jpg'],
    creator: '@quran_ai',
  },
};

// The root layout - this wraps every page
export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html
      lang="th"
      dir="ltr"
      className={inter.className}
    >
      <body className="min-h-screen bg-slate-50 text-slate-900 antialiased">
        {children}
      </body>
    </html>
  );
}