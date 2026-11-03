import dayjs from "dayjs";
import type { Patient } from "../../types";
export const hasValue = (value: unknown) =>
  value !== null && value !== undefined && value !== "";
export const isComplete = (patient: Patient) =>
  [patient.blood_type, patient.height, patient.weight, patient.amh_level].every(
    hasValue,
  );
export const ageLabel = (date: string) => {
  const age = dayjs().diff(dayjs(date), "year");
  const end =
    age % 100 >= 11 && age % 100 <= 14
      ? "лет"
      : age % 10 === 1
        ? "год"
        : age % 10 >= 2 && age % 10 <= 4
          ? "года"
          : "лет";
  return `${age} ${end}`;
};
export const formatDate = (date?: string) =>
  date && dayjs(date).isValid() ? dayjs(date).format("DD.MM.YYYY") : "—";
