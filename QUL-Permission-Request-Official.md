# OFFICIAL PERMISSION REQUEST & LICENSING CLARIFICATION

**Document Reference:** `QURAN-AI/LEGAL-REQ/2026-11/QUL-01`  
**Date:** November 3, 2026  
**Subject:** Formal Request for Permission & Licensing Clarification for Quranic & Classical Tafsir Datasets Integration  
**Project:** Quran AI — Intelligent Tafsir & Quran Study Platform  
**Repository:** https://github.com/aminanok005/quran-ai-tafsir  
**Contact:** Lead Project Coordinator & Data Governance Team  

---

## 1. Executive Summary & Purpose

I am writing on behalf of the **Quran AI Project**—an intelligent, evidence-based digital Quran and classical Tafsir study platform. Our mission is to facilitate in-depth, responsible study of the Holy Quran by combining authentic texts, classical scholarly commentaries, and modern retrieval-augmented intelligence.

A foundational architectural requirement of our platform is **Strict Source Integrity & Ethical Data Governance**. We recognize that public download links, automated user registration, and unverified web resources do **not** constitute legal authorization. Therefore, we formally submit this inquiry to obtain clear, written authorization from **QUL (Quranic Universal Library / Resource Licensor)** regarding the exact scope, terms, and technical boundaries for utilizing your digitized Quranic texts, translations, and classical Tafsir corpora.

---

## 2. Specific Authorization & Permission Scope

We kindly request confirmation and explicit authorization for each of the following eight technical and legal operational areas:

### 2.1 Rights Ownership & Governing Licenses
* Identification of the legal entity or scholar estate that controls the intellectual property rights for each provided text, translation, specific scholarly print edition, and the digitized database format.
* Specification of the exact license terms (e.g., CC-BY-NC, custom non-commercial agreement, or specific scholarly distribution license) that apply to each corpus.

### 2.2 Application Display & Passage Presentation
* Permission to display the authentic Arabic text, translations, and scholarly commentary within our web and mobile applications.
* Authorization for:
  1. **Ayah-Linked Passages:** Displaying concise, relevant commentary directly mapped to a user-selected Ayah.
  2. **Extended Contextual Passages:** Enabling an in-app scholarly reader view to examine full chapters/passages when pedagogically necessary, subject to any length thresholds you specify.

### 2.3 Server Storage, Ingestion, Normalization & Vector Indexing
* Permission to store authorized datasets on secure, encrypted project infrastructure and maintain automated backups.
* Permission to extract, normalize, and segment Arabic text and metadata (Surah, Ayah, volume, page, editor, and edition).
* Permission to generate full-text search indexes and **dense semantic vector embeddings** (e.g., PostgreSQL `pgvector`) strictly to support accurate passage lookup.

### 2.4 Transmission to Third-Party LLM Providers (RAG Pipeline Only)
* Authorization to pass retrieved, relevant textual excerpts via secure API calls to third-party Large Language Model providers (e.g., Google Gemini, Anthropic Claude, OpenAI) **solely** to synthesize Ayah-level explanations.
* All AI outputs must enforce strict citation standards, displaying exact source attribution, book name, author, volume, and page number.

### 2.5 Presentation of Generated Syntheses & Citation Formatting
* Permission to display AI-synthesized summaries alongside original Arabic quotations.
* Guidance on required typographic distinctions, verbatim quote thresholds, and clear visual disclaimers distinguishing divine scripture, scholarly quotes, and AI synthesis.

### 2.6 Attribution, Credit Notices & Usage Restrictions
* Specification of exact attribution statements, institutional credit lines, links, and copyright notices required on the platform.
* Explicit confirmation of any geographical, commercial, temporal, or redistribution restrictions.

### 2.7 Termination, Revocation & Data Deletion Protocol
* Written confirmation of the data lifecycle upon revocation: The Quran AI Project guarantees that should authorization expire or a resource be withdrawn, all local copies, database tables, search indexes, vector embeddings, and temporary caches associated with that resource will be completely purged within 30 calendar days.

### 2.8 Explicit Prohibition of Machine Learning Training
* **Binding Commitment:** The project undertakes **never** to utilize QUL datasets, scholarly commentaries, or translations for training, pre-training, fine-tuning, or distilling foundation AI models, unless explicit written consent is separately granted. Data is processed exclusively at inference time for real-time Retrieval-Augmented Generation (RAG).

---

## 3. Targeted Resource Authorization Matrix

Please confirm authorization for each specific resource below:

| Resource ID | Work Title / Dataset | Author / Compiler / Translator | Print Edition / Publisher | Display (Passage) | Ingestion & Vector Index | RAG Synthesis | Approved? (Yes / No) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: |
| **CORP-01** | *Tafsir al-Qur'an al-'Azim* | Imam Ibn Kathir (d. 774H) | Verified Classical Edition | Yes | Yes | Yes | [ &nbsp; ] |
| **CORP-02** | *Jami' al-Bayan 'an Ta'wil Ay al-Qur'an* | Imam Al-Tabari (d. 310H) | Verified Classical Edition | Yes | Yes | Yes | [ &nbsp; ] |
| **CORP-03** | *Al-Jami' li-Ahkam al-Qur'an* | Imam Al-Qurtubi (d. 671H) | Verified Classical Edition | Yes | Yes | Yes | [ &nbsp; ] |
| **CORP-04** | *Al-Tahrir wa al-Tanwir* | Sheikh Muhammad al-Tahir ibn 'Ashur | Dar Suhnun / Verified Edition | Yes | Yes | Yes | [ &nbsp; ] |
| **CORP-05** | *Taysir al-Karim al-Rahman* | Sheikh Abd al-Rahman al-Sa'di | Verified Edition | Yes | Yes | Yes | [ &nbsp; ] |
| **CORP-06** | *Al-Tafsir al-Munir* | Dr. Wahbah al-Zuhayli | Dar al-Fikr / Verified Edition | Yes | Yes | Yes | [ &nbsp; ] |
| **CORP-07** | Thai Quran Translation | Verified Royal Thai / Approved Translators | Official Translation Body | Yes | Yes | Yes | [ &nbsp; ] |
| **CORP-08** | English Quran Translation | Sahih International / Verified Translation | Official Translation Body | Yes | Yes | Yes | [ &nbsp; ] |

---

## 4. Formal Sign-Off & Acknowledgment

### Authorized QUL Representative:

* **Full Name:** _________________________________________________
* **Title / Department:** ________________________________________
* **Signature & Seal:** __________________________________________
* **Date of Approval:** __________________________________________
* **Scope Granted:** &nbsp; [ &nbsp; ] Full Approval &nbsp;&nbsp;&nbsp; [ &nbsp; ] Conditional (See Addendum) &nbsp;&nbsp;&nbsp; [ &nbsp; ] Rejected

---

### Requesting Project Lead:

* **Project Lead:** Lead Coordinator, Quran AI Platform
* **Repository:** [https://github.com/aminanok005/quran-ai-tafsir](https://github.com/aminanok005/quran-ai-tafsir)
* **Status:** Verified Source Integration & Governance Protocol
