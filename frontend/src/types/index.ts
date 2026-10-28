export type CaseType = "criminal" | "civil" | "contract" | "other";

export interface User {
  id: string;
  name: string;
  email: string;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface Case {
  id: string;
  title: string;
  description: string;
  case_type: CaseType;
  owner_id: string;
  document_count: number;
  created_at: string;
  updated_at: string;
}

export interface CaseCreatePayload {
  title: string;
  description?: string;
  case_type: CaseType;
}

export interface CaseUpdatePayload {
  title?: string;
  description?: string;
  case_type?: CaseType;
}

export interface CaseDocument {
  id: string;
  case_id: string;
  filename: string;
  original_name: string;
  file_type: "pdf" | "docx" | "jpg" | "jpeg" | "png" | string;
  file_size: number;
  sha256: string;
  uploaded_at: string;
  extracted: boolean;
}

export interface Parties {
  petitioner: string[];
  respondent: string[];
  counsel: string[];
}

export interface DateMention {
  date: string;
  event: string;
}

export interface CitedProvision {
  act: string;
  section: string;
  description: string;
}

export interface SpacyEntity {
  label: string;
  text: string;
}

export interface ExtractedEvent {
  date?: string | null;
  description: string;
  type: "filing" | "hearing" | "judgment" | "incident" | "other" | string;
  page_number?: number | null;
}

export interface ExtractionResult {
  id: string;
  document_id: string;
  case_id: string;
  source_document: string;
  parties: Parties;
  dates: DateMention[];
  events: ExtractedEvent[];
  claims: string[];
  cited_provisions: CitedProvision[];
  spacy_entities: SpacyEntity[];
  extracted_at: string;
  ocr_used: boolean;
  extraction_method: string;
  text_preview: string;
}

export interface ExtractResponse {
  case_id: string;
  processed: number;
  skipped: number;
  extractions: ExtractionResult[];
}

export interface TimelineEvent {
  date?: string | null;
  description: string;
  type: string;
  source_document: string;
  document_id: string;
  document_type: string;
  page_number?: number | null;
}

export interface Timeline {
  case_id: string;
  events: TimelineEvent[];
  last_updated?: string | null;
}

export interface CaseEntities {
  case_id: string;
  parties: Parties;
  dates: DateMention[];
  claims: string[];
  cited_provisions: CitedProvision[];
  spacy_entities: SpacyEntity[];
  document_count_extracted: number;
  extraction_methods?: string[];
}

export interface GraphNode {
  id: string;
  label: string;
  group: string;
}

export interface GraphLink {
  source: string;
  target: string;
  label: string;
}

export interface KnowledgeGraph {
  case_id: string;
  nodes: GraphNode[];
  links: GraphLink[];
}
