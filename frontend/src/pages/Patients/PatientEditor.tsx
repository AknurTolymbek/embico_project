import { useEffect } from "react";
import {
  Modal,
  Form,
  Input,
  DatePicker,
  InputNumber,
  Select,
  message,
} from "antd";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import dayjs from "dayjs";
import axios from "axios";
import { patientsApi } from "../../api/patients";
import type { Patient, PatientCreate } from "../../types";

type Values = Omit<PatientCreate, "date_of_birth"> & {
  date_of_birth: dayjs.Dayjs;
};
export const PatientEditor = ({
  open,
  patient,
  onClose,
  onCreated,
}: {
  open: boolean;
  patient?: Patient;
  onClose: () => void;
  onCreated?: (patient: Patient) => void;
}) => {
  const [form] = Form.useForm<Values>();
  const queryClient = useQueryClient();
  useEffect(() => {
    if (open) {
      form.resetFields();
      if (patient)
        form.setFieldsValue({
          ...patient,
          date_of_birth: dayjs(patient.date_of_birth),
          height: patient.height == null ? undefined : Number(patient.height),
          weight: patient.weight == null ? undefined : Number(patient.weight),
          amh_level:
            patient.amh_level == null ? undefined : Number(patient.amh_level),
        });
    }
  }, [open, patient, form]);
  const mutation = useMutation({
    mutationFn: (values: Values) => {
      const data = {
        ...values,
        blood_type: values.blood_type ?? null,
        height: values.height ?? null,
        weight: values.weight ?? null,
        amh_level: values.amh_level ?? null,
        medical_record_number: values.medical_record_number.trim(),
        date_of_birth: values.date_of_birth.format("YYYY-MM-DD"),
      };
      return patient
        ? patientsApi.updatePatient(patient.id, data)
        : patientsApi.createPatient(data);
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["patients"] });
      queryClient.invalidateQueries({ queryKey: ["patient", String(data.id)] });
      message.success(
        patient ? "Данные пациента обновлены" : "Пациент добавлен",
      );
      onClose();
      if (!patient) onCreated?.(data);
    },
    onError: (error) => {
      const detail = axios.isAxiosError(error)
        ? error.response?.data?.detail
        : undefined;
      message.error(
        typeof detail === "string"
          ? detail
          : "Не удалось сохранить данные. Попробуйте ещё раз.",
      );
    },
  });
  return (
    <Modal
      title={patient ? "Редактировать пациента" : "Новый пациент"}
      open={open}
      onCancel={() => {
        if (!mutation.isPending) onClose();
      }}
      cancelButtonProps={{ disabled: mutation.isPending }}
      closable={!mutation.isPending}
      keyboard={!mutation.isPending}
      onOk={() => form.submit()}
      okText={patient ? "Сохранить изменения" : "Добавить пациента"}
      cancelText="Отмена"
      confirmLoading={mutation.isPending}
      maskClosable={!mutation.isPending}
      width={560}
    >
      <p className="editor-description">
        Обезличенная медицинская карта. Обязательные поля отмечены звёздочкой.
      </p>
      <Form
        form={form}
        layout="vertical"
        onFinish={(values) => mutation.mutate(values)}
      >
        <Form.Item
          name="medical_record_number"
          label="Номер медицинской карты"
          rules={[
            {
              required: true,
              whitespace: true,
              message: "Укажите номер карты",
            },
            { max: 50, message: "Не более 50 символов" },
          ]}
        >
          <Input placeholder="Например, EMB-2026-001" />
        </Form.Item>
        <Form.Item
          name="date_of_birth"
          label="Дата рождения"
          rules={[{ required: true, message: "Укажите дату рождения" }]}
        >
          <DatePicker
            format="DD.MM.YYYY"
            placeholder="Выберите дату"
            style={{ width: "100%" }}
            disabledDate={(date) => date.isAfter(dayjs(), "day")}
          />
        </Form.Item>
        <div className="form-grid">
          <Form.Item name="blood_type" label="Группа крови">
            <Select
              allowClear
              placeholder="Не указана"
              options={[
                "O(I) Rh+",
                "O(I) Rh−",
                "A(II) Rh+",
                "A(II) Rh−",
                "B(III) Rh+",
                "B(III) Rh−",
                "AB(IV) Rh+",
                "AB(IV) Rh−",
              ].map((value) => ({ value, label: value }))}
            />
          </Form.Item>
          <Form.Item name="amh_level" label="АМГ, нг/мл">
            <InputNumber min={0} step={0.1} placeholder="Не указан" />
          </Form.Item>
          <Form.Item name="height" label="Рост, см">
            <InputNumber min={0} max={300} placeholder="Не указан" />
          </Form.Item>
          <Form.Item name="weight" label="Вес, кг">
            <InputNumber min={0} max={500} step={0.1} placeholder="Не указан" />
          </Form.Item>
        </div>
      </Form>
    </Modal>
  );
};
