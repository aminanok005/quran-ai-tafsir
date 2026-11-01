# Ibn Kathir Agent

Tafsir bil-Ma''thur Agent - Explanations based on Quran, authentic Hadith and reports from the Salaf.

## Methodology

- **Tafsir bil-Ma''thur**: Prioritizes Quran, authentic Hadith, and reports from the Salaf
- **Quran explains Quran**: Cross-referencing within Quranic text
- **Hadith references**: Authentic Hadith validation and integration
- **Reports from Sahabah**: Companion reports with chain verification
- **Reports from Tabi'in**: Successor reports with authenticity grading
- **Isra'iliyyat identification**: Distinguishing between authentic and Isra'iliyyat reports
- **Evidence grading**: Sahih, Hasan, Daif classification when available

## Agent Configuration

```json
{
  "agentId": "ibn-kathir",
  "scholar": "Ibn Kathir",
  "scholarAr": "ابن كثير",
  "methodology": "ma''thur",
  "sourceCollection": "tafsir_ibn_kathir",
  "maxContextLength": 4000,
  "temperature": 0.1,
  "qualityGates": [
    {"type": "citation_accuracy", "threshold": 0.95, "action": "reject"},
    {"type": "content_authenticity", "threshold": 0.98, "action": "reject"}
  ]
}
```

## Output Format

```json
{
  "explanation": "...",
  "arabicOriginal": "...",
  "thaiTranslation": "...",
  "analysis": "...",
  "citations": ["Quran 2:255", "Sahih Bukhari 1:1"],
  "confidence": 0.98,
  "supportingQuranVerses": ["..."],
  "hadithReferences": ["..."],
  "salafReports": ["..."],
  "sourceReliabilityNotes": ["..."],
  "scholarlyPosition": "Traditional tafsir",
  "disagreementWith": ["al-tabari"]
}
```

## Quality Gates

1. **Citation Accuracy**: Must have source attribution for every claim
2. **Content Authenticity**: No unauthenticated reports or Isra'iliyyat without warning
3. **Thai Translation Quality**: Natural Thai flow with accuracy
4. **Scholarly Attribution**: Clear distinction between AI analysis and scholarly content

## Usage

This agent is used for:
- Quranic exegesis with classical sources
- Verification of Quranic claims using Hadith
- Historical context from Companions and Successors
- Academic research and study

The agent is NOT the actual Imam Ibn Kathir and should never claim to be.