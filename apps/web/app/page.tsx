"use client";

import { Inter } from 'next/font/google';
import { Arabic_OTS, Noto_Naskh_Arabic } from 'next/font/google';

const inter = Inter({ subsets: ['latin'] });
const arabicOTS = Arabic_OTS({ subsets: ['arabic'], weight: '400' });
const arabicNoto = Noto_Naskh_Arabic({ subsets: ['arabic'], weight: ['400', '700'] });

export default function Home() {
  return (
    <main className={`${inter.className} min-h-screen bg-slate-50`}>
      <div className="flex h-screen">
        {/* Left Panel - Navigation (260px) */}
        <aside className="w-[260px] bg-white border-r border-slate-200 flex flex-col h-full">
          <div className="p-4 border-b border-slate-200">
            <h2 className="text-xl font-bold text-emerald-800">QURAN AI</h2>
          </div>
          
          <nav className="flex-1 overflow-y-auto p-4">
            <ul className="space-y-2">
              <li>
                <a href="#surah-navigator" className="block p-3 rounded-lg hover:bg-emerald-50 text-slate-700">
                  📖 Surah Navigator
                </a>
              </li>
              <li>
                <a href="#study-courses" className="block p-3 rounded-lg hover:bg-emerald-50 text-slate-700">
                  📚 Study Courses
                </a>
              </li>
              <li>
                <a href="#flashcard-decks" className="block p-3 rounded-lg hover:bg-emerald-50 text-slate-700">
                  🔄 Flashcard Decks
                </a>
              </li>
              <li>
                <a href="#quiz-history" className="block p-3 rounded-lg hover:bg-emerald-50 text-slate-700">
                  📊 Quiz History
                </a>
              </li>
              <li>
                <a href="#document-pdf" className="block p-3 rounded-lg hover:bg-emerald-50 text-slate-700">
                  📄 Document PDF
                </a>
              </li>
            </ul>
            
            <div className="mt-6">
              <h3 className="text-sm font-semibold text-slate-500 uppercase tracking-wide mb-3">
                Study Tracks
              </h3>
              <ul className="space-y-1">
                <li>
                  <a href="#tafsir-juz-amman" className="block p-2 pl-4 text-sm rounded hover:bg-emerald-50 text-slate-600">
                    • Tafsir Juz Amma
                  </a>
                </li>
                <li>
                  <a href="#stories-prophets" className="block p-2 pl-4 text-sm rounded hover:bg-emerald-50 text-slate-600">
                    • Stories of the Prophets
                  </a>
                </li>
                <li>
                  <a href="#miracles-surah-al-kahf" className="block p-2 pl-4 text-sm rounded hover:bg-emerald-50 text-slate-600">
                    • The Miracles of Surah Al-Kahf
                  </a>
                </li>
              </ul>
            </div>
          </nav>
          
          <div className="p-4 border-t border-slate-200 mt-auto">
            <div className="bg-gradient-to-r from-emerald-50 to-teal-50 rounded-lg p-3">
              <h4 className="text-sm font-semibold text-emerald-800 mb-2">Daily Zap Streak</h4>
              <p className="text-2xl font-bold text-emerald-600">7d</p>
              <p className="text-xs text-slate-600 mt-1">Complete today's lesson</p>
            </div>
            
            <div className="mt-3 flex items-center justify-between">
              <span className="text-sm text-slate-600">Gems: 1,420</span>
              <span className="text-sm text-slate-600">Hearts: 5/5</span>
            </div>
          </div>
        </aside>

        {/* Center Panel - Quran Reader (Flex 1) */}
        <section className="flex-1 flex flex-col h-full bg-gradient-to-br from-slate-50 to-emerald-50/30">
          {/* Surah Header */}
          <header className="bg-white border-b border-slate-200 p-4 sticky top-0 z-10">
            <div className="flex items-center justify-between mb-3">
              <h1 className="text-2xl font-bold text-emerald-800">36. Ya-Sin</h1>
              <div className="flex items-center gap-3">
                <span className="px-3 py-1 bg-amber-100 text-amber-800 rounded-full text-sm font-medium">Makki</span>
                <span className="text-sm text-slate-600">25 verses</span>
              </div>
            </div>
            
            {/* Ayah Navigation */}
            <div className="flex gap-2 overflow-x-auto pb-2">
              {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25].map((ayah) => (
                <button
                  key={ayah}
                  className={`min-w-[40px] h-8 rounded-lg text-sm font-medium transition-colors ${ayah === 13 ? 'bg-emerald-600 text-white' : 'bg-white text-slate-700 hover:bg-emerald-50 border border-slate-200'}`}
                >
                  {ayah}
                </button>
              ))}
            </div>
          </header>

          {/* Quran Reader Canvas */}
          <article className="flex-1 overflow-y-auto p-8">
            <div className="max-w-4xl mx-auto">
              {/* Ayah 13 - Selected */}
              <div id="ayah-13" className="text-center mb-12 animate-fade-in">
                <div className="mb-4">
                  <span className="inline-block px-2 py-1 bg-emerald-100 text-emerald-700 rounded text-xs font-medium mb-3">
                    Ayah 13
                  </span>
                </div>
                
                {/* Arabic Uthmani Text */}
                <h1 
                  className="text-5xl md:text-6xl font-arabic leading-[2.2] mb-6 text-slate-900"
                  style={{ fontFamily: 'Amiri Quran, Noto Naskh Arabic, serif' }}
                  dir="rtl"
                  lang="ar"
                >
                  وَاضْرِبْ لَهُم مَّثَلًا أَصْحَابَ الْقَرْيَةِ
                </h1>
                
                {/* Word-by-Word under Arabic */}
                <div className="flex justify-center gap-2 mb-6 text-xs text-slate-500 font-mono">
                  <span>و</span>
                  <span>اضرب</span>
                  <span>لهم</span>
                  <span>مثلاً</span>
                  <span>أصحاب</span>
                  <span>القرية</span>
                </div>
                
                {/* Thai Translation */}
                <p className="text-xl text-slate-700 mb-2 leading-relaxed">
                  “และจงยกอุทาหรณ์แก่พวกเขาถึงชาวเมือง…”
                </p>
                
                {/* English Translation */}
                <p className="text-lg text-slate-600 mb-6 italic">
                  And set for them a similitude: the inhabitants of the city
                </p>
                
                {/* Audio Player */}
                <div className="flex items-center justify-center gap-4 mb-8">
                  <button className="w-12 h-12 bg-emerald-600 hover:bg-emerald-700 rounded-full flex items-center justify-center text-white transition-colors">
                    🔊
                  </button>
                  <span className="text-sm text-slate-600">Mishary Rashid Al-Afasy</span>
                </div>
                
                {/* Quick Action Bar */}
                <div className="flex items-center justify-center gap-3 flex-wrap">
                  <button className="px-4 py-2 bg-white border border-emerald-200 rounded-lg hover:bg-emerald-50 text-emerald-700 text-sm font-medium transition-colors">
                    📖 Open Tafsir
                  </button>
                  <button className="px-4 py-2 bg-white border border-emerald-200 rounded-lg hover:bg-emerald-50 text-emerald-700 text-sm font-medium transition-colors">
                    ➕ Add Flashcard
                  </button>
                  <button className="px-4 py-2 bg-white border border-emerald-200 rounded-lg hover:bg-emerald-50 text-emerald-700 text-sm font-medium transition-colors">
                    ⭐ Bookmark
                  </button>
                </div>
              </div>
              
              {/* Other Ayahs Preview */}
              <div className="space-y-4 mt-12">
                {[1, 2, 3, 4, 5].map((ayah) => (
                  <div key={ayah} className="p-4 bg-white rounded-lg border border-slate-200 hover:border-emerald-200 transition-colors cursor-pointer">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <span className="w-8 h-8 bg-slate-100 rounded text-sm font-medium flex items-center justify-center">
                          {ayah}
                        </span>
                        <div>
                          <p className="text-sm font-arabic text-right" dir="rtl" lang="ar">
                            {ayah === 1 ? 'إِذْ أَرْسَلْنَا إِلَيْهِمُ اثْنَيْنِ' : 
                             ayah === 2 ? 'فَكَذَّبُوهُمَا' : 
                             ayah === 3 ? 'فَعَزَّزْنَا بِهِمْ' : 
                             ayah === 4 ? 'فَجَعَلْنَاهُمْ حَبۡطًا' : 
                             'فَلَمۡ یَزِدۡهُمۡ إِلَّا نُفُورًا'}
                          </p>
                          <p className="text-xs text-slate-600 mt-1">
                            {ayah === 1 ? 'When We sent to them two men' : 
                             ayah === 2 ? 'But they denied them both' : 
                             ayah === 3 ? 'Then We reinforced them' : 
                             ayah === 4 ? 'So We made them become silent ruins' : 
                             'But they did not believe'}
                          </p>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="text-xs text-slate-500">Verse {ayah}</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </article>
        </section>

        {/* Right Panel - Tafsir & AI Tools (420px) */}
        <aside className="w-[420px] bg-white border-l border-slate-200 flex flex-col h-full">
          {/* Tab Navigation */}
          <div className="flex border-b border-slate-200">
            <button className="flex-1 px-4 py-3 text-sm font-medium text-emerald-600 border-b-2 border-emerald-600 bg-emerald-50/50">
              Tafsir
            </button>
            <button className="flex-1 px-4 py-3 text-sm font-medium text-slate-600 hover:text-slate-900">
              Quiz
            </button>
            <button className="flex-1 px-4 py-3 text-sm font-medium text-slate-600 hover:text-slate-900">
              Cards
            </button>
          </div>
          
          {/* Agent Selector */}
          <div className="p-4 border-b border-slate-200 bg-slate-50">
            <h3 className="text-sm font-semibold text-slate-700 mb-2">Agent Selector</h3>
            <div className="grid grid-cols-2 gap-2">
              <button className="p-2 rounded-lg border border-slate-200 hover:border-emerald-300 bg-white transition-colors">
                <div className="text-xs font-medium text-slate-700">Ibn Kathir</div>
                <div className="text-xs text-slate-500 mt-1">Classical narration</div>
              </button>
              <button className="p-2 rounded-lg border border-slate-200 hover:border-emerald-300 bg-white transition-colors">
                <div className="text-xs font-medium text-slate-700">Al-Tabari</div>
                <div className="text-xs text-slate-500 mt-1">Historical reports</div>
              </button>
              <button className="p-2 rounded-lg border border-slate-200 hover:border-emerald-300 bg-white transition-colors">
                <div className="text-xs font-medium text-slate-700">Al-Qurtubi</div>
                <div className="text-xs text-slate-500 mt-1">Legal rulings</div>
              </button>
              <button className="p-2 rounded-lg border border-slate-200 hover:border-emerald-300 bg-white transition-colors">
                <div className="text-xs font-medium text-slate-700">Ibn Ashur</div>
                <div className="text-xs text-slate-500 mt-1">Linguistic analysis</div>
              </button>
            </div>
          </div>
          
          {/* Chat Stream */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {/* Agent Response */}
            <div className="bg-emerald-50 rounded-lg p-4 border-l-4 border-emerald-500">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-semibold text-emerald-800">Ibn Kathir Tafsir Agent</span>
                <span className="text-xs text-slate-500">[VERIFIED]</span>
              </div>
              <p className="text-sm text-slate-700 leading-relaxed">
                According to <strong>Tafsir al-Qur'an al-Azim (Vol 6, p. 565)</strong>, this ayah refers to Antioch (Antakiya) as mentioned by the scholars.
              </p>
              <div className="mt-3 flex items-center gap-2">
                <button className="text-xs text-emerald-600 hover:text-emerald-800">👁️ View Classical Arabic</button>
                <button className="text-xs text-emerald-600 hover:text-emerald-800">📊 Compare Matrix</button>
              </div>
            </div>
            
            {/* User Query */}
            <div className="bg-slate-50 rounded-lg p-4 border-l-4 border-slate-400 ml-auto max-w-xs">
              <p className="text-sm text-slate-700">Can you explain the meaning of this ayah in simple Thai language?</p>
              <div className="text-xs text-slate-500 mt-1 text-right">You</div>
            </div>
            
            {/* AI Synthesis */}
            <div className="bg-indigo-50 rounded-lg p-4 border-l-4 border-indigo-500">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-semibold text-indigo-800">AI Assistant</span>
                <span className="text-xs text-slate-500">[AI-SYNTHESIS]</span>
              </div>
              <p className="text-sm text-slate-700 leading-relaxed">
                The story illustrates how people who reject messengers eventually become spiritually corrupt and face divine punishment. It's a warning about arrogance and disobedience.
              </p>
              <div className="mt-3 flex items-center gap-2">
                <button className="text-xs text-indigo-600 hover:text-indigo-800">📚 Add to Flashcards</button>
                <button className="text-xs text-indigo-600 hover:text-indigo-800">❓ Generate Quiz</button>
              </div>
            </div>
          </div>
          
          {/* Input Area */}
          <div className="p-4 border-t border-slate-200">
            <div className="flex gap-2">
              <input
                type="text"
                placeholder="Ask about this ayah or request explanation..."
                className="flex-1 px-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
              />
              <button className="px-6 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg font-medium transition-colors">
                Send
              </button>
            </div>
          </div>
        </aside>
      </div>
    </main>
  );
}