// User and Auth types
export interface User {
  id: number;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
}

export enum UserRole {
  REPRODUCTOLOGIST = 'reproductologist',
  EMBRYOLOGIST = 'embryologist',
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

// Patient types
export interface Patient {
  id: number;
  medical_record_number: string;
  date_of_birth: string;
  phone?: string;
  diagnosis?: string;
  attending_physician_id?: number;
  attending_physician?: User;
  created_at: string;
  updated_at: string;
}

export interface PatientCreate {
  medical_record_number: string;
  date_of_birth: string;
  phone?: string;
  diagnosis?: string;
  attending_physician_id?: number;
}

export interface PatientUpdate {
  phone?: string;
  diagnosis?: string;
  attending_physician_id?: number;
}

// Cycle types
export enum CycleType {
  FRESH = 'fresh',
  CRYO = 'cryo',
}

export enum CycleStatus {
  ACTIVE = 'active',
  COMPLETED = 'completed',
  CANCELLED = 'cancelled',
}

export enum CycleStage {
  PREPARATION = 'preparation',
  STIMULATION = 'stimulation',
  RETRIEVAL = 'retrieval',
  EMBRYOLOGY = 'embryology',
  TRANSFER = 'transfer',
  OUTCOME = 'outcome',
}

export interface Cycle {
  id: number;
  patient_id: number;
  patient?: Patient;
  cycle_type: CycleType;
  status: CycleStatus;
  current_stage: CycleStage;
  start_date: string;
  end_date?: string;
  attending_physician_id?: number;
  attending_physician?: User;
  assigned_embryologist_id?: number;
  assigned_embryologist?: User;
  created_at: string;
  updated_at: string;
}

// API Response types
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export interface ApiError {
  detail: string;
}
