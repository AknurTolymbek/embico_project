import { useState } from 'react';
import { Table, Button, Input, Space, message, Modal } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, EyeOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { patientsApi } from '../../api/patients';
import dayjs from 'dayjs';
import type { Patient } from '../../types';

const { Search } = Input;

export const PatientsList = () => {
  const navigate = useNavigate();
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const pageSize = 10;

  const { data, isLoading } = useQuery({
    queryKey: ['patients', page, search],
    queryFn: () =>
      patientsApi.getPatients({
        skip: (page - 1) * pageSize,
        limit: pageSize,
        search: search || undefined,
      }),
  });

  const deleteMutation = useMutation({
    mutationFn: patientsApi.deletePatient,
    onSuccess: () => {
      message.success('Пациент удалён');
      queryClient.invalidateQueries({ queryKey: ['patients'] });
    },
    onError: () => {
      message.error('Ошибка при удалении');
    },
  });

  const handleDelete = (id: number) => {
    Modal.confirm({
      title: 'Удалить пациента?',
      content: 'Это действие нельзя отменить',
      onOk: () => deleteMutation.mutate(id),
    });
  };

  const calculateAge = (dob: string) => {
    return dayjs().diff(dayjs(dob), 'year');
  };

  const columns = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 80,
    },
    {
      title: t('patients.medicalRecordNumber'),
      dataIndex: 'medical_record_number',
      key: 'medical_record_number',
    },
    {
      title: t('patients.age'),
      dataIndex: 'date_of_birth',
      key: 'age',
      render: (dob: string) => calculateAge(dob),
      width: 100,
    },
    {
      title: t('patients.doctor'),
      dataIndex: 'attending_physician',
      key: 'doctor',
      render: (physician: Patient['attending_physician']) =>
        physician?.full_name || '—',
    },
    {
      title: t('common.actions'),
      key: 'actions',
      width: 200,
      render: (_: unknown, record: Patient) => (
        <Space>
          <Button
            icon={<EyeOutlined />}
            size="small"
            onClick={() => navigate(`/patients/${record.id}`)}
          >
            Открыть
          </Button>
          <Button
            icon={<EditOutlined />}
            size="small"
            onClick={() => navigate(`/patients/${record.id}/edit`)}
          />
          <Button
            icon={<DeleteOutlined />}
            size="small"
            danger
            onClick={() => handleDelete(record.id)}
          />
        </Space>
      ),
    },
  ];

  return (
    <div>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between' }}>
        <h1>{t('patients.title')}</h1>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => navigate('/patients/new')}
        >
          {t('patients.add')}
        </Button>
      </div>

      <div style={{ marginBottom: 16 }}>
        <Search
          placeholder={t('patients.search')}
          allowClear
          onSearch={setSearch}
          style={{ width: 400 }}
        />
      </div>

      <Table
        columns={columns}
        dataSource={data?.items || []}
        rowKey="id"
        loading={isLoading}
        pagination={{
          current: page,
          pageSize,
          total: data?.total || 0,
          onChange: setPage,
        }}
      />
    </div>
  );
};
