# QURAN AI
## Intelligent Quran Study & Tafsir Platform
### Product Requirements Document (PRD) v1.1

**Document Status:** Product Foundation  
**Language:** Thai-first / Arabic-source-first  
**Architecture:** Next.js + FastAPI + PostgreSQL + pgvector  
**Primary Objective:** Evidence-based Quran study and multi-scholar Tafsir comparison.

---

# 1. PRODUCT LANGUAGE POLICY

กำหนดภาษาไทยเป็นภาษาหลักของระบบทั้งหมด

| Component | Primary Language | Supporting Language |
|---|---|---|
| Quran Reader UI | Thai | English |
| Quran Arabic Text | Arabic | — |
| Quran Translation | Thai | English |
| Word-by-Word | Thai | Arabic |
| Tafsir Chat | Thai | Arabic / English |
| AI Agent Response | Thai | Arabic source quotations |
| Scholarly Comparison | Thai | Arabic |
| References | Thai labels | Original book titles |

### Language Requirements

- UI และคำอธิบายทั้งหมดใช้ภาษาไทยเป็นค่าเริ่มต้น
- ข้อความอัลกุรอานต้องแสดงภาษาอาหรับจากแหล่งข้อมูลที่เชื่อถือได้
- คำแปลต้องระบุผู้แปลและแหล่งที่มา
- ห้าม AI แปลข้อความต้นฉบับโดยไม่แยกให้เห็นว่าเป็นคำแปลของ AI
- รองรับ RTL สำหรับข้อความภาษาอาหรับ
- รองรับการค้นหาภาษาไทยและภาษาอาหรับ
- ผู้ใช้สามารถเปลี่ยนภาษาได้ในอนาคต

---

# 2. CORE PRODUCT EXPERIENCE

ผู้ใช้สามารถ:

1. เลือกซูเราะฮ์และอายะฮ์
2. อ่านข้อความอัลกุรอานภาษาอาหรับ
3. อ่านคำแปลภาษาไทย
4. เลือกอายะฮ์ที่ต้องการศึกษา
5. เปิด Tafsir Chat
6. เลือกนักตัฟซีรที่ต้องการศึกษา
7. อ่านคำอธิบายจากแต่ละตำรา
8. เปรียบเทียบความเห็นของอุละมาอ์
9. ตรวจสอบหลักฐานและแหล่งอ้างอิงต้นฉบับ

**Core Principle:** ทุกคำอธิบายต้องสามารถตรวจสอบย้อนกลับไปยังแหล่งข้อมูลได้

---

# 3. TAFSIR AGENT SYSTEM

ระบบเริ่มต้นด้วย 6 Agents

| Agent | Scholar | Main Methodology |
|---|---|---|
| Ibn Kathir Agent | อิบนุกะษีร | Tafsir bil-Ma'thur |
| Al-Tabari Agent | อัฏเฏาะบะรี | Early Reports and Narrations |
| Al-Qurtubi Agent | อัลกุรฏุบี | Ahkam al-Quran |
| Ibn Ashur Agent | อิบนุอาชูร | Linguistic and Maqasid Analysis |
| Al-Sa'di Agent | อัสสะอ์ดี | Accessible Tafsir |
| Al-Zuhayli Agent | วะฮ์บะฮ์ อัซซุฮัยลีย์ | Contemporary Fiqh and Society |

### Agent Execution Rules

แต่ละ Agent ต้องทำงานตามลำดับ:

1. รับ Ayah ID และข้อความอัลกุรอาน
2. ตรวจสอบบริบทของอายะฮ์
3. ค้นหาตำราที่เกี่ยวข้อง
4. ดึงข้อความต้นฉบับภาษาอาหรับ
5. ตรวจสอบตำแหน่งและข้อมูลหนังสือ
6. วิเคราะห์ตามแนวทางของนักวิชาการ
7. สร้างคำอธิบายภาษาไทย
8. ส่งหลักฐานให้ Citation Validator
9. แสดงผลแก่ผู้ใช้

**ข้อห้าม:** Agent ไม่ใช่ตัวนักวิชาการจริง และห้ามสร้างคำพูดหรือทัศนะแล้วอ้างว่าเป็นของนักวิชาการ

---

# 4. EVIDENCE & CITATION SYSTEM

กำหนดสถานะหลักฐาน 5 ประเภท:

| Label | Meaning |
|---|---|
| VERIFIED | ตรวจสอบข้อความต้นฉบับแล้ว |
| SOURCE-ATTRIBUTED | ระบุแหล่งที่มาได้ แต่ยังมีข้อจำกัดในการตรวจสอบ |
| SCHOLARLY DIFFERENCE | เป็นประเด็นที่มีความเห็นแตกต่าง |
| UNVERIFIED | ยังไม่สามารถยืนยันหลักฐาน |
| AI SYNTHESIS | เป็นการสังเคราะห์ของ AI ไม่ใช่ข้อความจากตำรา |

### Citation Format

ข้อมูลอ้างอิงควรประกอบด้วย:

- ชื่อผู้แต่ง
- ชื่อตำรา
- ชื่อบทหรือหัวข้อ
- เล่ม
- หน้า
- สำนักพิมพ์หรือฉบับพิมพ์
- URL หรือแหล่งข้อมูลต้นฉบับ
- ข้อความภาษาอาหรับที่เกี่ยวข้อง

หากไม่มีข้อมูลเล่มหรือหน้า ต้องไม่แต่งขึ้นเอง

---

# 5. SCHOLARLY DISAGREEMENT ENGINE

สร้างระบบเปรียบเทียบความเห็นของอุละมาอ์

เมื่อผู้ใช้เลือกอายะฮ์ ระบบสามารถแสดง:

- จุดที่นักวิชาการเห็นตรงกัน
- จุดที่มีความเห็นแตกต่าง
- หลักฐานที่แต่ละฝ่ายใช้
- ความแตกต่างด้านภาษา
- ความแตกต่างด้านหะดีษและรายงาน
- ความแตกต่างด้านฟิกฮ์
- ข้อสรุปที่มีหลักฐานรองรับ

ห้ามรวมความเห็นที่แตกต่างให้กลายเป็นข้อสรุปเดียวโดยไม่อธิบายความแตกต่าง

---

# 6. DATA SOURCE ARCHITECTURE

## 6.1 Primary ingestion source: Quranic Universal Library (QUL)

ใช้ QUL Resource Catalog เป็นแหล่งแรกสำหรับการนำเข้าข้อมูลอัลกุรอานและ
ทรัพยากรที่เกี่ยวข้อง โดยดาวน์โหลด JSON เพื่อสำรวจข้อมูล และใช้ SQLite
สำหรับชุดข้อมูลขนาดใหญ่หรือการ query ซ้ำ จากนั้นนำเข้าข้อมูลที่ผ่านการตรวจสอบ
เข้า PostgreSQL ของระบบ

เอกสารอ้างอิง:
- Datasets: https://qul.tarteel.ai/docs/datasets
- API status: https://qul.tarteel.ai/docs/api
- Data model: https://qul.tarteel.ai/docs/data-model
- Downloading data: https://qul.tarteel.ai/docs/downloading-data
- Resources: https://qul.tarteel.ai/resources
- Repository: https://github.com/TarteelAI/quranic-universal-library

**ข้อจำกัด:** QUL Public REST API ยังอยู่ระหว่างออกแบบ เอกสารแนะนำให้ดาวน์โหลด
Resource ใน JSON หรือ SQLite จึงห้ามออกแบบระบบ production โดยพึ่ง endpoint
`/api/v1` ที่ยังไม่เปิดให้บริการ แต่ละ Resource มีต้นทางและคุณภาพต่างกัน
และต้องตรวจสอบสิทธิ์การจัดเก็บ แสดงผล อ้างอิง ทำดัชนี และใช้กับ AI แยกกัน

เริ่ม MVP ด้วย Quran script ที่เลือก คำแปลภาษาไทยที่ตรวจสอบผู้แปลและสิทธิ์แล้ว
หากมี และตำราตัฟซีรหนึ่งฉบับที่มีข้อมูลบรรณานุกรม/สิทธิ์ชัดเจน อย่าสมมติว่า
Resource ครอบคลุมตำราตัฟซีรทั้ง 6 รายชื่อ หรือว่ามี mapping เล่ม/หน้าให้ครบ

QUL tafsir candidates ที่ระบุแล้ว ได้แก่ As-Saadi (ภาษาอินโดนีเซีย), al-Tabari,
Ibn Kathir และ Al Qurtubi ดู resource/download IDs และสถานะ review ที่
`docs/sources/README.md` ห้ามเปิดใช้เป็น Agent corpus ก่อนตรวจภาษา ฉบับพิมพ์
schema, mapping และสิทธิ์ของแต่ละไฟล์ โดยเฉพาะ As-Saadi resource ที่หน้าเว็บ
แจ้งว่าไม่มีข้อมูล copyright ไม่เหมาะใช้ตอบภาษาไทยโดยไม่ติดป้ายภาษาและที่มา

ปัจจุบันมีไฟล์ SQLite ของ corpus เหล่านี้อยู่ใน `data-tafsir/`; Ibn Kathir
retrieval ใช้ไฟล์ local โดยตรงและอ้างอิง ayah/group range จากฐานข้อมูล แต่ต้อง
คงสถานะ `UNVERIFIED` และ rights pending จนกว่าจะ review edition และการใช้งาน

## 6.2 Optional live Quran API: Quran Foundation

Quran Foundation API เป็นตัวเลือกเสริมเมื่อมีความต้องการข้อมูล runtime
หรือ API สดโดยเฉพาะ ไม่ใช่ dependency สำหรับการนำเข้าชุดข้อมูล QUL

เอกสาร: https://api-docs.quran.com/docs/api-reference/

- เรียก API ผ่าน Backend และเก็บ credential เฉพาะฝั่ง Server
- ตรวจสอบการเข้าถึง API, ข้อกำหนดการใช้งาน, Translation ID ภาษาไทย และเงื่อนไข
  cache ก่อนเปิดใช้จริง
- อย่ารวมข้อมูลจาก API กับ QUL โดยไม่มีการระบุ resource/version และกฎการเลือก
  source of truth

## 6.3 Optional tafsir providers and hadith sources

Shamela หรือผู้ให้บริการอื่นใช้เป็น ingestion adapter เพิ่มเติมได้เมื่อยืนยัน
การเข้าถึง หนังสือ/ฉบับพิมพ์ และสิทธิ์การประมวลผลแล้วเท่านั้น ไม่ให้ Agents
เรียกแหล่งภายนอกโดยตรงระหว่างตอบคำถาม ให้ import เข้าฐานข้อมูลภายในพร้อม
metadata และ audit record

Hadith corpus, chain, และ grading ต้องมาจากแหล่งที่ตรวจสอบได้แยกต่างหาก
หมวดข้อมูลของ QUL ที่ระบุในเอกสารไม่ได้ยืนยันว่ามีบริการ hadith verification
ครบถ้วน ห้ามอนุมาน grade หรือ isnad จากข้อความตัฟซีรเพียงอย่างเดียว

## 6.4 Ingestion and source-of-truth rules

ดูขั้นตอนและ acceptance checks ที่ [Data Integration Guide](docs/sources/README.md).

ทุก resource ต้องมี registry record สำหรับผู้แต่ง/ผู้แปล ชื่อหนังสือ ฉบับพิมพ์
สิทธิ์ URL/รหัส resource วันที่นำเข้า checksum/version และสถานะการตรวจสอบ
เชื่อมข้อมูลระดับอายะฮ์ด้วย `surah_id + ayah_number` และระดับคำด้วย
`surah_id + ayah_number + word_position`; เก็บ identifiers เดิมไว้และห้ามเติม
เลขหน้า/เล่มที่ไม่มีใน resource

QUL ระบุว่าข้อมูลจากแหล่งภายนอกอาจมีข้อผิดพลาดและคำแปลมีข้อจำกัด การ import
จึงไม่ทำให้ข้อมูลเป็น `VERIFIED` โดยอัตโนมัติ ต้องผ่าน validation และ human
review ก่อนให้ Agent ใช้ตอบ

---

# 7. KNOWLEDGE BASE

ใช้ PostgreSQL + pgvector

รองรับ:
- Arabic Full-text Search
- Thai Full-text Search
- Semantic Search
- Exact Text Retrieval
- Ayah Mapping
- Book and Author Filtering
- Volume and Page Metadata

ห้ามใช้ Vector Search เพียงอย่างเดียวในการยืนยันคำพูดจากตำรา

ต้องให้ความสำคัญกับ Exact Text และแหล่งอ้างอิงต้นฉบับก่อน

---

# 8. MVP SCOPE

MVP ต้องประกอบด้วย:

1. Quran Reader
2. Arabic Quran Text
3. Thai Translation
4. Surah Navigation
5. Ayah Selection
6. Tafsir Chat
7. Ibn Kathir Agent
8. Al-Tabari Agent
9. Al-Sa'di Agent
10. Source Citation
11. Scholarly Comparison เบื้องต้น
12. Bookmarks และ Reading History

Agents อีก 3 ตัวสามารถทยอยเปิดใช้งานเมื่อแหล่งข้อมูลผ่านการตรวจสอบ

---

# 9. QUALITY GATES

ก่อนเปิดใช้งานแต่ละ Agent ต้องผ่าน:

- Source Availability Test
- Arabic Text Integrity Test
- Ayah Mapping Test
- Citation Accuracy Test
- Unsupported Claim Test
- Thai Translation Quality Test
- Scholarly Attribution Test

หากไม่ผ่าน ให้ Agent แสดงข้อความว่าไม่สามารถยืนยันหลักฐานได้ แทนการสร้างคำตอบขึ้นเอง

---

# 10. NEXT DEVELOPMENT PHASES

| Phase | Scope | Deliverable |
|---|---|---|
| 0 | Research & Foundation | Source and Architecture Validation |
| 1 | Quran Reader | Working Quran Reader |
| 2 | Tafsir Knowledge Base | Verified Source Repository |
| 3 | First Tafsir Agents | Ibn Kathir / Tabari / Sa'di |
| 4 | Multi-Agent System | Independent Tafsir Analysis |
| 5 | Comparison Engine | Scholarly Disagreement |
| 6 | Research Mode | Advanced Quran Study |
| 7 | Production Readiness | Security, Monitoring, Testing |

**Development Rule:** ห้ามเริ่มสร้าง Agent จำนวนมากก่อนที่ Knowledge Base และ Citation System จะผ่านการตรวจสอบ

---

# 11. DEFINITION OF DONE

ระบบจะถือว่าผ่าน MVP เมื่อ:

- ผู้ใช้เปิดอ่านอัลกุรอานได้
- เลือกอายะฮ์แล้วเปิด Tafsir Chat ได้
- Agent สามารถค้นหาตำราที่เกี่ยวข้องได้
- คำอธิบายมีแหล่งอ้างอิงตรวจสอบได้
- แยกคำพูดต้นฉบับกับการสังเคราะห์ของ AI ได้
- ไม่สร้างข้อมูลอ้างอิงที่ไม่มีอยู่จริง
- รองรับภาษาไทยและภาษาอาหรับได้อย่างถูกต้อง
- ผ่าน Automated Tests และ Security Review

---

**FINAL PRODUCT PRINCIPLE**

QURAN AI ไม่ได้ถูกสร้างขึ้นเพื่อแทนที่อุละมาอ์ แต่เพื่อช่วยให้ผู้คนเข้าถึงอัลกุรอาน ตำราตัฟซีร และหลักฐานทางวิชาการได้สะดวกขึ้น โดยรักษาความถูกต้อง ความโปร่งใส และความแตกต่างทางวิชาการ