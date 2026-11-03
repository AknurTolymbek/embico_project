import { useMemo, useState } from "react";
import { Alert, Button, Empty, Input, Select, Table, Tooltip } from "antd";
import {
  ArrowDownOutlined,
  ArrowRightOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  ExportOutlined,
  PlusOutlined,
  SearchOutlined,
  TeamOutlined,
} from "@ant-design/icons";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import dayjs from "dayjs";
import { patientsApi } from "../../api/patients";
import { PatientEditor } from "./PatientEditor";
import { ageLabel, formatDate, hasValue, isComplete } from "./patientUtils";
import type { Patient } from "../../types";

export const PatientsList = () => {
  const navigate = useNavigate();
  const [params, setParams] = useSearchParams();
  const search = params.get("search") || "";
  const filter = params.get("filter") || "all";
  const sort = params.get("sort") || "newest";
  const page = Math.max(1, Number(params.get("page")) || 1);
  const [editorOpen, setEditorOpen] = useState(false);
  const {
    data = [],
    isLoading,
    isError,
    refetch,
  } = useQuery({ queryKey: ["patients"], queryFn: patientsApi.getPatients });
  const update = (key: string, value: string) =>
    setParams(
      (current) => {
        const next = new URLSearchParams(current);
        if (value) next.set(key, value);
        else next.delete(key);
        if (key !== "page") next.delete("page");
        return next;
      },
      { replace: true },
    );
  const closeEditor = () => {
    setEditorOpen(false);
    if (params.has("create")) update("create", "");
  };
  const completeCount = data.filter(isComplete).length;
  const recentCount = data.filter((patient) =>
    dayjs(patient.created_at).isAfter(dayjs().subtract(30, "day")),
  ).length;
  const filtered = useMemo(
    () =>
      data
        .filter((patient) => {
          const matchesSearch = `${patient.medical_record_number} ${patient.id}`
            .toLowerCase()
            .includes(search.trim().toLowerCase());
          return (
            matchesSearch &&
            (filter === "all" ||
              (filter === "complete"
                ? isComplete(patient)
                : !isComplete(patient)))
          );
        })
        .sort((a, b) =>
          sort === "number"
            ? a.medical_record_number.localeCompare(
                b.medical_record_number,
                "ru",
                { numeric: true },
              )
            : sort === "oldest"
              ? dayjs(a.created_at).valueOf() - dayjs(b.created_at).valueOf()
              : dayjs(b.created_at).valueOf() - dayjs(a.created_at).valueOf(),
        ),
    [data, search, filter, sort],
  );
  const currentPage = Math.min(
    page,
    Math.max(1, Math.ceil(filtered.length / 8)),
  );
  const exportPatients = () => {
    const rows = [
      [
        "Номер карты",
        "Дата рождения",
        "Группа крови",
        "Рост, см",
        "Вес, кг",
        "АМГ, нг/мл",
      ],
      ...filtered.map((p) => [
        p.medical_record_number,
        formatDate(p.date_of_birth),
        p.blood_type ?? "",
        p.height ?? "",
        p.weight ?? "",
        p.amh_level ?? "",
      ]),
    ];
    const csv =
      "\uFEFF" +
      rows
        .map((row) =>
          row
            .map(
              (cell) =>
                `"${String(cell)
                  .replace(/^[=+@\-\t\r]/, "'$&")
                  .replaceAll('"', '""')}"`,
            )
            .join(";"),
        )
        .join("\r\n");
    const url = URL.createObjectURL(
      new Blob([csv], { type: "text/csv;charset=utf-8;" }),
    );
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `embico-patients-${dayjs().format("YYYY-MM-DD")}.csv`;
    anchor.click();
    URL.revokeObjectURL(url);
  };
  return (
    <div className="patients-page">
      <div className="breadcrumb">
        Клиника <span>/</span> <strong>Пациенты</strong>
      </div>
      <div className="page-heading">
        <div>
          <div className="eyebrow">ВАШИ ПАЦИЕНТЫ. ИХ ИСТОРИИ.</div>
          <h1>
            Пациенты<span className="heading-dot">.</span>
          </h1>
          <p>Единое пространство для заботы о каждом пациенте.</p>
        </div>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => setEditorOpen(true)}
        >
          Добавить пациента
        </Button>
      </div>
      <div className="stats-grid">
        <div className="stat-card">
          <span className="stat-icon blue">
            <TeamOutlined />
          </span>
          <div>
            <span className="stat-label">Всего пациентов</span>
            <div className="stat-value">
              {isError ? "—" : isLoading ? "…" : data.length}
              <span>в вашей клинике</span>
            </div>
          </div>
          <span className="stat-decoration">↗</span>
        </div>
        <div className="stat-card">
          <span className="stat-icon mint">
            <ClockCircleOutlined />
          </span>
          <div>
            <span className="stat-label">Новые пациенты</span>
            <div className="stat-value">
              {isError ? "—" : isLoading ? "…" : recentCount}
              <span>за последние 30 дней</span>
            </div>
          </div>
        </div>
        <div className="stat-card">
          <span className="stat-icon lavender">
            <CheckCircleOutlined />
          </span>
          <div>
            <span className="stat-label">Карты заполнены</span>
            <div className="stat-value">
              {isError ? "—" : isLoading ? "…" : completeCount}
              <span>все медицинские показатели</span>
            </div>
          </div>
        </div>
      </div>
      <section className="panel registry-panel" aria-label="Реестр пациентов">
        <div className="registry-title">
          <div>
            <h2>
              Реестр пациентов{" "}
              <span className="count-badge">{isError ? "—" : data.length}</span>
            </h2>
            <p>Медицинские карты и основная информация</p>
          </div>
          <Button
            icon={<ExportOutlined />}
            onClick={exportPatients}
            disabled={!filtered.length || isError}
          >
            Экспорт
          </Button>
        </div>
        <div className="registry-tabs" role="group" aria-label="Фильтр карт">
          {[
            { key: "all", label: "Все пациенты", count: data.length },
            {
              key: "complete",
              label: "Заполненные карты",
              count: completeCount,
            },
            {
              key: "incomplete",
              label: "Требуют заполнения",
              count: data.length - completeCount,
            },
          ].map((item) => (
            <button
              key={item.key}
              className={filter === item.key ? "active" : ""}
              aria-pressed={filter === item.key}
              onClick={() => update("filter", item.key)}
            >
              {item.label}
              <span>{isError ? "—" : item.count}</span>
            </button>
          ))}
        </div>
        <div className="table-toolbar">
          <Input
            prefix={<SearchOutlined />}
            placeholder="Поиск по номеру карты или ID…"
            value={search}
            onChange={(event) => update("search", event.target.value)}
            allowClear
            aria-label="Поиск пациентов"
          />
          <Select
            aria-label="Сортировка пациентов"
            value={sort}
            onChange={(value) => update("sort", value)}
            suffixIcon={<ArrowDownOutlined />}
            options={[
              { value: "newest", label: "Сначала новые" },
              { value: "oldest", label: "Сначала старые" },
              { value: "number", label: "По номеру карты" },
            ]}
          />
        </div>
        {isError ? (
          <div className="error-container">
            <Alert
              type="error"
              showIcon
              title="Не удалось загрузить пациентов"
              description="Проверьте соединение с сервером и попробуйте ещё раз."
              action={<Button onClick={() => refetch()}>Повторить</Button>}
            />
          </div>
        ) : (
          <Table<Patient>
            className="patient-table"
            rowKey="id"
            loading={isLoading}
            dataSource={filtered}
            scroll={{ x: 790 }}
            onRow={(record) => ({
              onClick: (event) => {
                if (!(event.target as HTMLElement).closest("a, button"))
                  navigate(`/patients/${record.id}`);
              },
              className: "patient-row",
            })}
            locale={{
              emptyText: (
                <Empty
                  image={Empty.PRESENTED_IMAGE_SIMPLE}
                  description={
                    search || filter !== "all"
                      ? "По вашему запросу пациенты не найдены"
                      : "Добавьте первого пациента, чтобы начать работу"
                  }
                />
              ),
            }}
            columns={[
              {
                title: "ПАЦИЕНТ / МЕД. КАРТА",
                key: "patient",
                render: (_, patient) => (
                  <Link
                    to={`/patients/${patient.id}`}
                    className="patient-identity"
                  >
                    <span className={`patient-avatar tone-${patient.id % 4}`}>
                      <TeamOutlined />
                    </span>
                    <span>
                      <strong>{patient.medical_record_number}</strong>
                      <small>
                        Медицинская карта · ID{" "}
                        {String(patient.id).padStart(4, "0")}
                      </small>
                    </span>
                  </Link>
                ),
              },
              {
                title: "ВОЗРАСТ",
                dataIndex: "date_of_birth",
                render: (value: string) => (
                  <div className="cell-stack">
                    <strong>{ageLabel(value)}</strong>
                    <small>{formatDate(value)}</small>
                  </div>
                ),
              },
              {
                title: "ГРУППА КРОВИ",
                dataIndex: "blood_type",
                render: (value) =>
                  value ? (
                    <span className="blood-label">{value}</span>
                  ) : (
                    <span className="muted">Не указана</span>
                  ),
              },
              {
                title: "АМГ, нг/мл",
                dataIndex: "amh_level",
                render: (value) =>
                  hasValue(value) ? (
                    <span className="numeric-value">
                      {Number(value).toLocaleString("ru-RU")}
                    </span>
                  ) : (
                    <span className="muted">—</span>
                  ),
              },
              {
                title: "ЗАПОЛНЕНИЕ КАРТЫ",
                key: "status",
                render: (_, patient) => (
                  <Tooltip title="Группа крови, рост, вес и АМГ">
                    <span
                      className={`status-pill ${isComplete(patient) ? "complete" : "pending"}`}
                    >
                      <i />
                      {isComplete(patient) ? "Заполнена" : "Не все данные"}
                    </span>
                  </Tooltip>
                ),
              },
              {
                title: "",
                key: "open",
                width: 55,
                render: (_, patient) => (
                  <Link
                    className="open-patient"
                    to={`/patients/${patient.id}`}
                    aria-label={`Открыть карту ${patient.medical_record_number}`}
                  >
                    <ArrowRightOutlined />
                  </Link>
                ),
              },
            ]}
            pagination={{
              current: currentPage,
              pageSize: 8,
              total: filtered.length,
              onChange: (value) => update("page", String(value)),
              showSizeChanger: false,
              showTotal: (total, range) =>
                total
                  ? `${range[0]}–${range[1]} из ${total} пациентов`
                  : "0 пациентов",
            }}
          />
        )}
      </section>
      <div className="registry-footnote">
        <span className="online-dot" /> Обезличенные данные · Внимание к каждому
        пациенту
      </div>
      <PatientEditor
        open={editorOpen || params.get("create") === "1"}
        onClose={closeEditor}
        onCreated={(patient) => navigate(`/patients/${patient.id}`)}
      />
    </div>
  );
};
