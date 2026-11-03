import { useEffect } from 'react';
import { Form, Input, DatePicker, Button, Card, Space, message, Spin } from 'antd';
import { LeftOutlined, SaveOutlined } from '@ant-design/icons';
import { useNavigate, useParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { patientsApi } from '../../api/patients';
import dayjs from 'dayjs';
import type { PatientCreate } from '../../types';

export const PatientForm = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const [form] = Form.useForm();

  const isEdit = id && id !== 'new';

  const { data: patient, isLoading } = useQuery({
    queryKey: ['patient', id],
    queryFn: () => patientsApi.getPatient(Number(id)),
    enabled: !!isEdit,
  });

  const createMutation = useMutation({
    mutationFn: patientsApi.createPatient,
    onSuccess: () => {
      message.success('Пациент создан');
      queryClient.invalidateQueries({ queryKey: ['patients'] });
      navigate('/patients');
    },
    onError: () => {
      message.error('Ошибка при создании');
    },
  });

  const updateMutation = useMutation({
    mutationFn: (data: { id: number; values: PatientCreate }) =>
      patientsApi.updatePatient(data.id, data.values),
    onSuccess: () => {
      message.success('Пациент обновлён');
      queryClient.invalidateQueries({ queryKey: ['patients'] });
      queryClient.invalidateQueries({ queryKey: ['patient', id] });
      navigate(`/patients/${id}`);
    },
    onError: () => {
      message.error('Ошибка при обновлении');
    },
  });

  useEffect(() => {
    if (patient) {
      form.setFieldsValue({
        ...patient,
        date_of_birth: dayjs(patient.date_of_birth),
      });
    }
  }, [patient, form]);

  const onFinish = (values: PatientCreate & { date_of_birth: dayjs.Dayjs }) => {
    const data = {
      ...values,
      date_of_birth: values.date_of_birth.format('YYYY-MM-DD'),
    };

    if (isEdit) {
      updateMutation.mutate({ id: Number(id), values: data });
    } else {
      createMutation.mutate(data);
    }
  };

  if (isEdit && isLoading) {
    return (
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <Spin size="large" />
      </div>
    );
  }

  return (
    <div>
      <div style={{ marginBottom: 16 }}>
        <Button icon={<LeftOutlined />} onClick={() => navigate(-1)}>
          {t('common.back')}
        </Button>
      </div>

      <Card title={isEdit ? t('patients.edit') : t('patients.add')}>
        <Form
          form={form}
          layout="vertical"
          onFinish={onFinish}
          style={{ maxWidth: 600 }}
        >
          <Form.Item
            name="medical_record_number"
            label={t('patients.medicalRecordNumber')}
            rules={[{ required: true, message: 'Обязательное поле' }]}
          >
            <Input placeholder="Например: PAT_001" />
          </Form.Item>

          <Form.Item
            name="date_of_birth"
            label={t('patients.dateOfBirth')}
            rules={[{ required: true, message: 'Обязательное поле' }]}
          >
            <DatePicker style={{ width: '100%' }} format="DD.MM.YYYY" />
          </Form.Item>

          <Form.Item name="phone" label={t('patients.phone')}>
            <Input placeholder="+7 (___) ___-__-__" />
          </Form.Item>

          <Form.Item name="diagnosis" label={t('patients.diagnosis')}>
            <Input.TextArea rows={3} placeholder="Диагноз" />
          </Form.Item>

          <Form.Item>
            <Space>
              <Button
                type="primary"
                htmlType="submit"
                icon={<SaveOutlined />}
                loading={createMutation.isPending || updateMutation.isPending}
              >
                {t('common.save')}
              </Button>
              <Button onClick={() => navigate(-1)}>{t('common.cancel')}</Button>
            </Space>
          </Form.Item>
        </Form>
      </Card>
    </div>
  );
};
