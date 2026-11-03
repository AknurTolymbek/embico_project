import { Card, Descriptions, Button, Space, Spin, Tag, Empty, List } from 'antd';
import { EditOutlined, LeftOutlined, PlusOutlined } from '@ant-design/icons';
import { useNavigate, useParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useQuery } from '@tanstack/react-query';
import { patientsApi } from '../../api/patients';
import dayjs from 'dayjs';

export const PatientCard = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { t } = useTranslation();

  const { data: patient, isLoading } = useQuery({
    queryKey: ['patient', id],
    queryFn: () => patientsApi.getPatient(Number(id)),
    enabled: !!id,
  });

  if (isLoading) {
    return (
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <Spin size="large" />
      </div>
    );
  }

  if (!patient) {
    return <Empty description="Пациент не найден" />;
  }

  const calculateAge = (dob: string) => {
    return dayjs().diff(dayjs(dob), 'year');
  };

  return (
    <div>
      <div style={{ marginBottom: 16 }}>
        <Space>
          <Button icon={<LeftOutlined />} onClick={() => navigate('/patients')}>
            {t('common.back')}
          </Button>
          <Button
            type="primary"
            icon={<EditOutlined />}
            onClick={() => navigate(`/patients/${id}/edit`)}
          >
            {t('common.edit')}
          </Button>
        </Space>
      </div>

      <Card title={t('patients.card')} style={{ marginBottom: 16 }}>
        <Descriptions column={2} bordered>
          <Descriptions.Item label={t('patients.medicalRecordNumber')}>
            {patient.medical_record_number}
          </Descriptions.Item>
          <Descriptions.Item label={t('patients.age')}>
            {calculateAge(patient.date_of_birth)} лет
          </Descriptions.Item>
          <Descriptions.Item label={t('patients.dateOfBirth')}>
            {dayjs(patient.date_of_birth).format('DD.MM.YYYY')}
          </Descriptions.Item>
          <Descriptions.Item label={t('patients.phone')}>
            {patient.phone || '—'}
          </Descriptions.Item>
          <Descriptions.Item label={t('patients.doctor')} span={2}>
            {patient.attending_physician?.full_name || '—'}
          </Descriptions.Item>
          <Descriptions.Item label={t('patients.diagnosis')} span={2}>
            {patient.diagnosis || '—'}
          </Descriptions.Item>
        </Descriptions>
      </Card>

      <Card
        title={t('patients.activeCycles')}
        extra={
          <Button type="primary" icon={<PlusOutlined />}>
            Начать новый цикл
          </Button>
        }
      >
        <Empty description="Нет активных циклов" />
      </Card>

      <Card title="История циклов" style={{ marginTop: 16 }}>
        <Empty description="Циклов пока нет" />
      </Card>
    </div>
  );
};
