import { apiClient } from './client';
import type { Patient, PatientCreate, PatientUpdate, PaginatedResponse } from '../types';

export const patientsApi = {
  getPatients: async (params?: {
    skip?: number;
    limit?: number;
    search?: string;
  }): Promise<PaginatedResponse<Patient>> => {
    const response = await apiClient.get<PaginatedResponse<Patient>>('/api/patients/', {
      params,
    });
    return response.data;
  },

  getPatient: async (id: number): Promise<Patient> => {
    const response = await apiClient.get<Patient>(`/api/patients/${id}`);
    return response.data;
  },

  createPatient: async (data: PatientCreate): Promise<Patient> => {
    const response = await apiClient.post<Patient>('/api/patients/', data);
    return response.data;
  },

  updatePatient: async (id: number, data: PatientUpdate): Promise<Patient> => {
    const response = await apiClient.put<Patient>(`/api/patients/${id}`, data);
    return response.data;
  },

  deletePatient: async (id: number): Promise<void> => {
    await apiClient.delete(`/api/patients/${id}`);
  },
};
