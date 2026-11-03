// User and Auth types
export interface User {
  id: number;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
}

export const UserRole = {
  REPRODUCTOLOGIST: "reproductologist",
  EMBRYOLOGIST: "embryologist",
} as const;
export type UserRole = (typeof UserRole)[keyof typeof UserRole];

export interface LoginRequest {
  email: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

// Patient fields match backend/app/schemas/patient.py.
export interface PatientCreate {
  medical_record_number: string;
  date_of_birth: string;
  blood_type?: string | null;
  height?: number | string | null;
  weight?: number | string | null;
  amh_level?: number | string | null;
}

export interface Patient extends PatientCreate {
  id: number;
  created_at: string;
  updated_at: string;
}

export type PatientUpdate = Partial<PatientCreate>;

// Cycle types
export const CycleType = {
  FRESH: "fresh",
  CRYO: "cryo",
} as const;
export type CycleType = (typeof CycleType)[keyof typeof CycleType];

export const CycleStatus = {
  ACTIVE: "active",
  COMPLETED: "completed",
  CANCELLED: "cancelled",
} as const;
export type CycleStatus = (typeof CycleStatus)[keyof typeof CycleStatus];

export const CycleStage = {
  PREPARATION: "preparation",
  STIMULATION: "stimulation",
  RETRIEVAL: "retrieval",
  EMBRYOLOGY: "embryology",
  TRANSFER: "transfer",
  OUTCOME: "outcome",
} as const;
export type CycleStage = (typeof CycleStage)[keyof typeof CycleStage];

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
