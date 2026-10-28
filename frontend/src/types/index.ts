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
