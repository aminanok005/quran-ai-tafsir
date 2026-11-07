# apps/web

QURAN AI workspace component.

## Strapi-backed study tracks

The server-rendered `/courses` and `/courses/[slug]` routes read published
content from Strapi. Set `STRAPI_API_BASE_URL` and, when the API is private,
`STRAPI_API_TOKEN` in the Next.js server environment. The token is read only by
the server-side module `src/lib/strapi.ts`; do not prefix it with `NEXT_PUBLIC_`.
Use a Strapi read-only token with `find`/`findOne` permissions for `courses` and
`chapters`.

Expected Strapi content model:

- `Course` collection: `title`, `slug`, optional `description` and `level`, and
  a to-many `chapters` relation.
- `Chapter` collection: `title`, optional `chapter_number`, `surah_id`,
  `ayah_range`, and a `content_blocks` Dynamic Zone.
- `learning.theory-block`: `title`, `arabic_text`, `translation_th`,
  `explanation_markdown` (or `content_markdown`), and `citation_reference`.
- `learning.quiz-block`: `question`, `options` (each with `label`, `value`,
  `is_correct`, optional `feedback`), optional `explanation_on_complete` and
  `points`.
- `learning.vocabulary-matching`: `title` and `pairs` (each with
  `arabic_word`, optional `root_word`, and `meaning_th`).

Course and chapter reads are cached for up to one hour. Quiz answers and
learning progress are not saved to an account; course quiz blocks are rendered
as practice only. Strapi/MCP server setup and schema creation are not automated
by this repository.
