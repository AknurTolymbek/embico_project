import { useState } from "react";
import { Alert, Button, Empty, Skeleton, Tabs } from "antd";
import {
  ArrowLeftOutlined,
  ArrowRightOutlined,
  CheckCircleOutlined,
  EditOutlined,
  ExperimentOutlined,
  FileTextOutlined,
  HeartOutlined,
  SafetyCertificateOutlined,
  TeamOutlined,
} from "@ant-design/icons";
import { Link, useLocation, useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import axios from "axios";
import { patientsApi } from "../../api/patients";
import { PatientEditor } from "./PatientEditor";
import { ageLabel, formatDate, hasValue, isComplete } from "./patientUtils";
import "../Predictions/predictions.css";

export const PatientCard = () => {
  const { id } = useParams<{ id: string }>();
  const location = useLocation();
  const [editorOpen, setEditorOpen] = useState(
    location.pathname.endsWith("/edit"),
  );
  const [tab, setTab] = useState("overview");
  const validId =
    !!id &&
    /^\d+$/.test(id) &&
    Number.isSafeInteger(Number(id)) &&
    Number(id) > 0;
  const {
    data: patient,
    isLoading,
    isError,
    error,
    refetch,
  } = useQuery({
    queryKey: ["patient", id],
    queryFn: () => patientsApi.getPatient(Number(id)),
    enabled: validId,
  });
  const backLink = (
    <Link to="/patients" className="back-link">
      <ArrowLeftOutlined /> Все пациенты
    </Link>
  );
  if (isLoading)
    return (
      <div>
        {backLink}
        <div className="panel loading-panel">
          <Skeleton active avatar paragraph={{ rows: 8 }} />
        </div>
      </div>
    );
  if (!validId || (axios.isAxiosError(error) && error.response?.status === 404))
    return (
      <div>
        {backLink}
        <div className="panel loading-panel">
          <Empty description="Пациент не найден" />
        </div>
      </div>
    );
  if (isError || !patient)
    return (
      <div>
        {backLink}
        <Alert
          type="error"
          showIcon
          title="Не удалось загрузить медицинскую карту"
          description="Проверьте соединение с сервером."
          action={<Button onClick={() => refetch()}>Повторить</Button>}
        />
      </div>
    );
  const metrics = [
    {
      label: "Группа крови",
      value: patient.blood_type || "—",
      unit: "",
      icon: <HeartOutlined />,
      tone: "rose",
    },
    {
      label: "Антимюллеров гормон",
      value: hasValue(patient.amh_level)
        ? Number(patient.amh_level).toLocaleString("ru-RU")
        : "—",
      unit: "нг/мл",
      icon: <ExperimentOutlined />,
      tone: "blue",
    },
    {
      label: "Рост",
      value: hasValue(patient.height)
        ? Number(patient.height).toLocaleString("ru-RU")
        : "—",
      unit: "см",
      icon: <ArrowRightOutlined rotate={-90} />,
      tone: "mint",
    },
    {
      label: "Вес",
      value: hasValue(patient.weight)
        ? Number(patient.weight).toLocaleString("ru-RU")
        : "—",
      unit: "кг",
      icon: <HeartOutlined />,
      tone: "lavender",
    },
  ];
  const filledCount = [
    patient.blood_type,
    patient.height,
    patient.weight,
    patient.amh_level,
  ].filter(hasValue).length;
  const medicalData = (
    <section className="panel medical-panel">
      <div className="section-heading">
        <span className="section-icon">
          <ExperimentOutlined />
        </span>
        <div>
          <h2>Медицинские показатели</h2>
          <p>Основные данные пациента</p>
        </div>
        <Button
          type="text"
          icon={<EditOutlined />}
          aria-label="Редактировать медицинские показатели"
          onClick={() => setEditorOpen(true)}
        />
      </div>
      <div className="metrics-grid">
        {metrics.map((metric) => (
          <div className="metric-card" key={metric.label}>
            <span className={`metric-icon ${metric.tone}`}>{metric.icon}</span>
            <span>{metric.label}</span>
            <strong>
              {metric.value}
              <small>{metric.value !== "—" ? metric.unit : ""}</small>
            </strong>
          </div>
        ))}
      </div>
      <div className="panel-note">
        <SafetyCertificateOutlined /> Показатели из медицинской карты. Обновлено{" "}
        {formatDate(patient.updated_at)}.
      </div>
    </section>
  );
  const history = (
    <section className="panel history-panel">
      <div className="section-heading">
        <span className="section-icon">
          <FileTextOutlined />
        </span>
        <div>
          <h2>История карты</h2>
          <p>Даты регистрации и последнего изменения</p>
        </div>
      </div>
      <div className="timeline">
        <div>
          <i />
          <span>
            <strong>Последнее обновление карты</strong>
            <small>Актуальные данные пациента</small>
          </span>
          <time>{formatDate(patient.updated_at)}</time>
        </div>
        <div>
          <i />
          <span>
            <strong>Пациент добавлен в клинику</strong>
            <small>
              Создана медицинская карта {patient.medical_record_number}
            </small>
          </span>
          <time>{formatDate(patient.created_at)}</time>
        </div>
      </div>
    </section>
  );
  return (
    <div className="patient-detail">
      <div className="breadcrumb">
        <Link to="/patients">Пациенты</Link>
        <span>/</span>
        <strong>{patient.medical_record_number}</strong>
      </div>
      {backLink}
      <section className="patient-hero panel">
        <div className="patient-hero-main">
          <span className={`patient-avatar large tone-${patient.id % 4}`}>
            <TeamOutlined />
          </span>
          <div>
            <div className="eyebrow">МЕДИЦИНСКАЯ КАРТА</div>
            <h1>{patient.medical_record_number}</h1>
            <div className="patient-subline">
              <span>{ageLabel(patient.date_of_birth)}</span>
              <i />
              <span>Дата рождения: {formatDate(patient.date_of_birth)}</span>
            </div>
          </div>
        </div>
        <div className="patient-hero-actions">
          <span
            className={`status-pill ${isComplete(patient) ? "complete" : "pending"}`}
          >
            <i />
            {isComplete(patient) ? "Карта заполнена" : "Карта заполняется"}
          </span>
          <div className="patient-prediction-actions">
            <Button
              type="primary"
              icon={<ExperimentOutlined />}
              href={`/patients/${id}/predict`}
            >
              Предикт
            </Button>
            <Button icon={<EditOutlined />} onClick={() => setEditorOpen(true)}>
              Редактировать карту
            </Button>
          </div>
        </div>
      </section>
      <Tabs
        className="detail-tabs"
        activeKey={tab}
        onChange={setTab}
        items={[
          { key: "overview", label: "Обзор пациента" },
          { key: "medical", label: "Медицинские данные" },
          { key: "history", label: "История карты" },
        ]}
      />
      <div className="detail-grid">
        <div className="detail-main">
          {tab !== "history" && medicalData}
          {tab !== "medical" && history}
        </div>
        <aside className="detail-aside">
          <section className="panel info-panel">
            <h2>Информация о карте</h2>
            <dl>
              <div>
                <dt>Идентификатор</dt>
                <dd>#{String(patient.id).padStart(4, "0")}</dd>
              </div>
              <div>
                <dt>Дата регистрации</dt>
                <dd>{formatDate(patient.created_at)}</dd>
              </div>
              <div>
                <dt>Обновлена</dt>
                <dd>{formatDate(patient.updated_at)}</dd>
              </div>
              <div>
                <dt>Формат данных</dt>
                <dd>Обезличенные</dd>
              </div>
            </dl>
          </section>
          <section className="completion-card">
            <span className="stat-icon blue">
              <CheckCircleOutlined />
            </span>
            <h3>
              {filledCount === 4
                ? "Всё необходимое — под рукой"
                : "Полная карта — больше ясности"}
            </h3>
            <p>
              {filledCount === 4
                ? "Все основные медицинские показатели заполнены."
                : "Дополните медицинские показатели, чтобы важные данные всегда были рядом."}
            </p>
            <div className="completion-track">
              <i style={{ width: `${filledCount * 25}%` }} />
            </div>
            <span className="completion-caption">
              Заполнено {filledCount} из 4 показателей
            </span>
            {filledCount < 4 && (
              <Button type="link" onClick={() => setEditorOpen(true)}>
                Дополнить карту <ArrowRightOutlined />
              </Button>
            )}
          </section>
        </aside>
      </div>
      <PatientEditor
        open={editorOpen}
        patient={patient}
        onClose={() => setEditorOpen(false)}
      />
    </div>
  );
};
