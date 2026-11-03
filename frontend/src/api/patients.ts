import { apiClient } from "./client";
import type { Patient, PatientCreate, PatientUpdate } from "../types";

const path = "/api/v1/patients";
export const patientsApi = {
  getPatients: async (): Promise<Patient[]> => {
    const patients: Patient[] = [];
    const limit = 500;
    while (true) {
      const { data } = await apiClient.get<Patient[]>(`${path}/`, {
        params: { skip: patients.length, limit },
      });
      patients.push(...data);
      if (data.length < limit) return patients;
    }
  },
  getPatient: async (id: number): Promise<Patient> =>
    (await apiClient.get<Patient>(`${path}/${id}`)).data,
  createPatient: async (data: PatientCreate): Promise<Patient> =>
    (await apiClient.post<Patient>(`${path}/`, data)).data,
  updatePatient: async (id: number, data: PatientUpdate): Promise<Patient> =>
    (await apiClient.put<Patient>(`${path}/${id}`, data)).data,
  deletePatient: async (id: number): Promise<void> => {
    await apiClient.delete(`${path}/${id}`);
  },
};
