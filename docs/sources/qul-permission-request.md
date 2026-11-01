# QUL Resource Permission Request

Use this draft to request resource-specific permission from the Quranic
Universal Library (QUL). Replace bracketed details before sending. This is a
request, not evidence that permission has been granted.

## Permission goals

Ask QUL to confirm, separately for each exact resource:

- Who owns or controls the rights in the text, translation, edition, and
  digitized dataset, and which license or terms apply.
- Whether the project may display the text in a Quran study application,
  including short passages linked to a selected ayah and longer passages only
  if explicitly permitted.
- Whether it may store the downloaded dataset on its server, make backups,
  normalize it, and create a searchable or vector index for retrieval.
- Whether retrieved passages may be sent to a third-party LLM provider to
  generate an ayah-level explanation, with source attribution and citations.
- Whether generated summaries may be shown to users, and whether quotations
  must be limited or formatted in a particular way.
- Required attribution, links, notices, and any restrictions on redistribution,
  access, commercial use, geography, or duration.
- Whether embeddings, indexes, caches, and generated outputs must be deleted
  when permission ends or a resource is withdrawn.
- Whether model training or fine-tuning is permitted. The project will not use
  the resources for training unless QUL expressly grants that use.

An account registration, welcome email, public download link, or a page stating
that copyright information is unavailable does not answer these questions.
Permission should identify the exact resource and allowed uses.

## English email draft

**Subject:** Permission request for specific QUL tafsir resources in Quran AI Tafsir

Assalamu alaikum,

I am developing **Quran AI Tafsir**, a Quran reading and study application.
Users can select an ayah, read the Arabic Quran text and translations, and
study tafsir with clearly identified sources and citations. I would like to
request written guidance and, where needed, permission to use specific QUL
resources in this application.

The resources I am asking about are:

1. Tafsir Ibn Kathir — Arabic (`qul:ar-tafsir-ibn-kathir`), local file
   `ar-tafsir-ibn-kathir.db`. QUL resource page:
   https://qul.tarteel.ai/resources/tafsir/22
   Candidate downloads:
   https://qul.tarteel.ai/resources/tafsir/c269d0d1f6414d664e0428544cfd9e9d/download
   and https://qul.tarteel.ai/resources/tafsir/2a6f7b2dc3e2a10ff540d49647f91767/download
2. Tafsir al-Tabari — Arabic (`qul:ar-tafsir-al-tabari`), local file
   `ar-tafsir-al-tabari.db`. QUL resource page:
   https://qul.tarteel.ai/resources/tafsir/37
   Candidate downloads:
   https://qul.tarteel.ai/resources/tafsir/2de427d35ee3cd4662db60ae725c6c05/download
   and https://qul.tarteel.ai/resources/tafsir/7cd206df05d7ca99eea76a9aab041c72/download
3. Tafseer al-Qurtubi — local file `ar-tafseer-al-qurtubi.db`. Candidate
   downloads (please confirm exact title, language, and edition):
   https://qul.tarteel.ai/resources/tafsir/9fe5997c5c380a104aa77606a41531af/download
   and https://qul.tarteel.ai/resources/tafsir/f0d31d805524430f2e172a3f18b1d76c/download
4. Tafsir As-Saadi — local files `tafsir-as-saadi.db` and
   `id-tafsir-as-saadi.db`. Candidate QUL resource page and downloads:
   https://qul.tarteel.ai/resources/tafsir/503
   https://qul.tarteel.ai/resources/tafsir/7108e1242d0baba9c195ae89fa36fc7a/download
   https://qul.tarteel.ai/resources/tafsir/3403ba2978aa005fd4e94c8d0b3e359f/download
   Project notes identify resource 503 as Indonesian. Please confirm which
   download corresponds to each local file, and whether the other file is a
   separate Arabic edition/resource.

Please correct any title, language, resource-page, edition, or local-file
identification above. The download IDs are included so that permission can be
confirmed for each exact file rather than assumed for a whole book title.

For each resource, could you please confirm:

1. The applicable license or terms, and the rights holder/licensor for the
   underlying text, translation/edition, and QUL digitization.
2. Whether the following uses are permitted:
   - displaying the text, or limited excerpts, alongside the selected Quran
     ayah in a web study application;
   - storing and backing up the dataset on the application's server;
   - cleaning/normalizing the data and creating a search/vector index for
     retrieval (RAG);
   - sending only the relevant retrieved passage and ayah context to an
     external LLM provider to produce a cited explanation for the user;
   - displaying the generated explanation and source citation to users.
3. Any required attribution wording, linking, quotation limits, notices,
   restrictions, or deletion requirements.
4. Whether use in a free public application is allowed and whether separate
   permission would be required if the project later accepts donations,
   sponsorship, or charges for any service.
5. Whether model training or fine-tuning is allowed. I will treat training as
   **not permitted** unless you expressly authorize it.

If QUL does not control the relevant rights or cannot grant permission, I would
be grateful for the appropriate rights holder, license, or contact to consult.
I will keep each resource unavailable in the application until its applicable
terms and permissions are clear.

Project details:

- Project: Quran AI Tafsir
- Website or repository: [insert public URL, if available]
- Developer/contact: [name and email]
- Intended audience and availability: [describe audience, countries, and access]
- LLM provider/model and hosting region, if applicable: [insert details, or
  state that this is still being selected]

Thank you for your guidance.

Jazakum Allahu khairan,

[Name]

## Thai summary for the request

ขอให้ QUL ยืนยันสิทธิ์แยกตามชุดข้อมูลและภาษาอย่างชัดเจน ได้แก่ ผู้ถือสิทธิ์
license/เงื่อนไขการใช้ การแสดงข้อความหรือข้อความคัดบางส่วน การจัดเก็บและสำรอง
ข้อมูล การปรับรูปแบบ/สร้างดัชนีค้นหาและ RAG การส่งเฉพาะข้อความที่ค้นคืนได้ให้
ผู้ให้บริการ LLM ภายนอกเพื่อสร้างคำอธิบายพร้อมอ้างอิง และการแสดงผลลัพธ์แก่ผู้ใช้
รวมถึงรูปแบบเครดิต ข้อจำกัดการคัดลอก/เผยแพร่ ข้อกำหนดการลบข้อมูล การใช้งานฟรี
หรือเชิงพาณิชย์ และสิทธิ์สำหรับการฝึกหรือ fine-tune โมเดล ซึ่งจะไม่ทำจนกว่าจะ
ได้รับอนุญาตเป็นลายลักษณ์อักษรโดยเฉพาะ

ก่อนส่ง โปรดยืนยันชื่อ/ภาษาของแต่ละไฟล์จากหน้า QUL หรือ download metadata
ให้ตรงกับ dataset จริง รวมทั้งเติมข้อมูลผู้ติดต่อ รายละเอียดเว็บ และผู้ให้บริการ
LLM ที่วางแผนใช้
