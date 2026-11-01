from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field, validator
from fastapi import UploadFile
import uuid

# Enums
class SurahType(str, Enum):
    MECCAN = "meccan"
    MEDINAN = "medinan"

class Language(str, Enum):
    ARABIC = "ar"
    THAI = "th"
    ENGLISH = "en"
    URDU = "ur"

class EvidenceLevel(str, Enum):
    VERIFIED = "VERIFIED"
    SOURCE_ATTRIBUTED = "SOURCE-ATTRIBUTED"
    SCHOLARLY_DISAGREEMENT = "SCHOLARLY DIFFERENCE"
    UNVERIFIED = "UNVERIFIED"
    AI_SYNTHESIS = "AI SYNTHESIS"

class AgentType(str, Enum):
    IBN_KATHIR = "ibn-kathir"
    AL_TABARI = "al-tabari"
    AL_QURTUBI = "al-qurtubi"
    IBN_ASHUR = "ibn-ashur"
    AL_SAADI = "al-saadi"
    AL_ZUHALYI = "al-zuhayli"

class Methodology(str, Enum):
    MA_THUR = "ma'thur"
    RA_Y = "ra'y"
    LINGUISTIC = "linguistic"
    LEGAL = "legal"
    CONTEMPORARY = "contemporary"

class HadithGrade(str, Enum):
    SAHIH = "sahih"
    HASAN = "hasan"
    DAIF = "daif"
    MAUDU = "maudu"

class UserRole(str, Enum):
    READER = "reader"
    STUDENT = "student"
    RESEARCHER = "researcher"
    SCHOLAR = "scholar"
    CONTENT_ADMIN = "content_admin"
    PLATFORM_ADMIN = "platform_admin"

# Base Models
class BaseModel(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    class Config:
        from_attributes = True

class BaseEntity(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    class Config:
        from_attributes = True

# Quran Models
class SurahModel(BaseEntity):
    number: int = Field(..., gt=0, le=114)
    name: str
    name_simple: str
    name_complex: str
    english_name: Optional[str] = None
    english_name_translation: Optional[str] = None
    revelation_type: SurahType
    revelation_order: int
    verses_count: int = Field(..., ge=0)
    pages: List[int]
    audio: Optional[List[str]] = None

class AyahModel(BaseEntity):
    surah_id: uuid.UUID
    surah_number: int = Field(..., gt=0, le=114)
    ayah_number: int = Field(..., ge=1, le=200)
    text_uthmani: str
    text_simple: Optional[str] = None
    text_complex: Optional[str] = None
    text_indopak: Optional[str] = None
    juz_number: Optional[int] = None
    hizb_number: Optional[int] = None
    rub_el_hizb_number: Optional[int] = None
    page_number: Optional[int] = None
    sajdah: bool = False
    sajdah_number: Optional[int] = None

    @validator('surah_number')
    def validate_surah_number(cls, v):
        if not (1 <= v <= 114):
            raise ValueError('Surah number must be between 1 and 114')
        return v

    @validator('ayah_number')
    def validate_ayah_number(cls, v):
        if not (1 <= v <= 200):
            raise ValueError('Ayah number must be between 1 and 200')
        return v

class TranslationModel(BaseEntity):
    ayah_id: uuid.UUID
    language: Language
    translation_id: int
    author_name: Optional[str] = None
    author_name_ar: Optional[str] = None
    text: str
    footnotes: Dict[str, Any] = Field(default_factory=dict)

    @validator('language')
    def validate_language(cls, v):
        if v not in [lang.value for lang in Language]:
            raise ValueError(f'Language must be one of: {[lang.value for lang in Language]}')
        return v

class WordTranslationModel(BaseEntity):
    ayah_id: uuid.UUID
    word_index: int = Field(..., ge=1)
    word_arabic: str
    word_translation: Optional[str] = None
    word_transliteration: Optional[str] = None
    root_arabic: Optional[str] = None
    lemma_arabic: Optional[str] = None
    part_of_speech: Optional[str] = None

# Scholar Models
class ScholarModel(BaseEntity):
    name: str
    name_ar: Optional[str] = None
    death_year_hijri: Optional[int] = None
    death_year_gregorian: Optional[int] = None
    birth_year_hijri: Optional[int] = None
    birth_year_gregorian: Optional[int] = None
    birth_place: Optional[str] = None
    death_place: Optional[str] = None
    madhhab: Optional[str] = None
    specialization: List[str] = Field(default_factory=list)
    biography: Optional[str] = None
    biography_ar: Optional[str] = None
    is_active: bool = True
    source_urls: List[str] = Field(default_factory=list)

class TafsirBookModel(BaseEntity):
    scholar_id: uuid.UUID
    title: str
    title_ar: Optional[str] = None
    title_transliteration: Optional[str] = None
    short_name: Optional[str] = None
    methodology: Methodology
    description: Optional[str] = None
    description_ar: Optional[str] = None
    volumes_count: int = Field(default=1, gt=0)
    total_pages: Optional[int] = None
    language: Language = Language.ARABIC
    original_language: Language = Language.ARABIC
    publisher: Optional[str] = None
    publication_year: Optional[int] = None
    publication_place: Optional[str] = None
    edition: Optional[str] = None
    isbn: Optional[str] = None
    source_url: Optional[str] = None
    shamela_id: Optional[int] = None
    shamela_book_id: Optional[int] = None
    is_active: bool = True
    metadata: Dict[str, Any] = Field(default_factory=dict)

# Source and Citation Models
class SourcePermissionModel(BaseEntity):
    source_id: uuid.UUID
    book_id: uuid.UUID
    license: str
    allowed_uses: List[str] = Field(default_factory=list)
    restrictions: List[str] = Field(default_factory=list)
    expires_at: Optional[datetime] = None
    reviewer_id: Optional[uuid.UUID] = None
    review_date: Optional[datetime] = None
    status: str = "pending"
    metadata: Dict[str, Any] = Field(default_factory=dict)

class SourceReferenceModel(BaseEntity):
    passage_id: uuid.UUID
    reference_type: str
    source_id: Optional[uuid.UUID] = None
    source_table: Optional[str] = None
    reference_text: Optional[str] = None
    reference_text_ar: Optional[str] = None
    grading: Optional[HadithGrade] = None
    chain: List[str] = Field(default_factory=list)
    reliability_score: float = Field(default=0.5, ge=0.0, le=1.0)
    verified_by: Optional[uuid.UUID] = None
    verified_at: Optional[datetime] = None
    notes: Optional[str] = None

class CitationModel(BaseEntity):
    source_id: uuid.UUID
    passage_id: Optional[uuid.UUID] = None
    ayah_id: Optional[uuid.UUID] = None
    reference: str
    original_text: str
    excerpt: str
    grading: Optional[HadithGrade] = None
    verified: bool = False
    validation_status: str = "pending"
    validation_issues: List[Dict[str, Any]] = Field(default_factory=list)

# Agent Models
class AgentConfigModel(BaseEntity):
    agent_type: AgentType
    scholar: str
    scholar_ar: Optional[str] = None
    methodology: Methodology
    source_collection: str
    max_context_length: int = Field(default=4000, gt=0)
    temperature: float = Field(default=0.1, ge=0.0, le=2.0)
    top_p: float = Field(default=0.95, ge=0.0, le=1.0)
    default_max_tokens: int = Field(default=1000, gt=0)
    quality_gates: List[Dict[str, Any]] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class RetrievedSourceModel(BaseEntity):
    source_id: str
    title: str
    author: str
    relevance: float = Field(default=1.0, ge=0.0, le=1.0)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    excerpt: str
    full_text: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class AgentExecutionModel(BaseEntity):
    agent_id: uuid.UUID
    ayah_id: uuid.UUID
    context: Dict[str, Any]
    sources: List[Dict[str, Any]] = Field(default_factory=list)
    output: Dict[str, Any]
    citations: List[Dict[str, Any]] = Field(default_factory=list)
    quality_score: float = Field(default=0.0, ge=0.0, le=1.0)
    llm_provider: str
    llm_model: str
    token_usage: Dict[str, int] = Field(default_factory=dict)
    execution_time: float = Field(default=0.0, ge=0.0)
    error_message: Optional[str] = None

class UserModel(BaseEntity):
    username: str
    email: str
    role: UserRole = UserRole.READER
    is_active: bool = True
    preferences: Dict[str, Any] = Field(default_factory=dict)
    profile: Dict[str, Any] = Field(default_factory=dict)

class BookmarkModel(BaseEntity):
    user_id: uuid.UUID
    ayah_id: uuid.UUID
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)

class ReadingProgressModel(BaseEntity):
    user_id: uuid.UUID
    ayah_id: uuid.UUID
    last_read: datetime = Field(default_factory=datetime.now)
    progress_percentage: float = Field(default=0.0, ge=0.0, le=100.0)
    notes: Optional[str] = None

# Search and Retrieval Models
class SearchRequestModel(BaseModel):
    query: str
    filters: Optional[Dict[str, Any]] = None
    page: int = Field(default=1, gt=0)
    per_page: int = Field(default=20, gt=0, le=100)
    search_type: str = "hybrid"

class SearchResultModel(BaseModel):
    ayah_id: str
    surah: int
    ayah: int
    text: str
    score: float
    match_type: str
    source: Optional[str] = None

class SearchResponseModel(BaseModel):
    results: List[SearchResultModel]
    total: int
    page: int
    per_page: int
    execution_time: float

# API Request/Response Models
class CreateTafsirRequest(BaseModel):
    book_id: uuid.UUID
    surah_number: int
    ayah_number: int
    arabic_text: str
    thai_translation: str
    source_reference: Optional[str] = None

class CreateTafsirResponse(BaseModel):
    id: uuid.UUID
    status: str
    message: str

class ExecuteAgentRequest(BaseModel):
    ayah_id: str
    agent_types: List[AgentType]
    context: Optional[Dict[str, Any]] = None
    max_agents: int = Field(default=3, gt=0)

class ExecuteAgentResponse(BaseModel):
    execution_id: str
    outputs: List[Dict[str, Any]]
    citations: List[Dict[str, Any]]
    processing_time: float

# Enum helper for documentation
__all__ = [
    'SurahType', 'Language', 'EvidenceLevel', 'AgentType', 'Methodology',
    'HadithGrade', 'UserRole',
    'BaseModel', 'BaseEntity',
    'SurahModel', 'AyahModel', 'TranslationModel', 'WordTranslationModel',
    'ScholarModel', 'TafsirBookModel',
    'SourcePermissionModel', 'SourceReferenceModel', 'CitationModel',
    'AgentConfigModel', 'RetrievedSourceModel', 'AgentExecutionModel',
    'UserModel', 'BookmarkModel', 'ReadingProgressModel',
    'SearchRequestModel', 'SearchResultModel', 'SearchResponseModel',
    'CreateTafsirRequest', 'CreateTafsirResponse',
    'ExecuteAgentRequest', 'ExecuteAgentResponse'
]