import { useEffect, useRef, useState } from "react";
import { Alert, Button, Empty, Input, Skeleton, Tabs } from "antd";
import {
  ArrowDownOutlined,
  ArrowLeftOutlined,
  ArrowUpOutlined,
  CloseOutlined,
  ExperimentOutlined,
  FileImageOutlined,
  PlayCircleOutlined,
  ReloadOutlined,
  UploadOutlined,
} from "@ant-design/icons";
import { Link, useParams } from "react-router-dom";
import { useMutation, useQuery } from "@tanstack/react-query";
import axios from "axios";
import { patientsApi } from "../../api/patients";
import { mlApi } from "../../api/ml";
import type { PredictionResult as Result } from "../../types/ml";
import { PredictionResult } from "./PredictionResult";
import "./predictions.css";

type Mode = "blastocyst" | "timelapse";
const naturalOrder = new Intl.Collator("ru", { numeric: true });
const isImage = (file: File) => /\.(jpe?g|png|tiff?)$/i.test(file.name);

function ImageFiles({
  label,
  files,
  multiple = false,
  disabled,
  onChange,
}: {
  label: string;
  files: File[];
  multiple?: boolean;
  disabled: boolean;
  onChange: (files: File[]) => void;
}) {
  const move = (index: number, step: number) => {
    const next = [...files];
    [next[index], next[index + step]] = [next[index + step], next[index]];
    onChange(next);
  };
  return (
    <div className="prediction-file-group">
      <label className={`prediction-upload ${disabled ? "disabled" : ""}`}>
        <UploadOutlined />
        <strong>{label}</strong>
        <span>
          {multiple
            ? "Выберите изображения JPG, PNG или TIFF"
            : "Выберите одно изображение JPG, PNG или TIFF"}
        </span>
        <input
          type="file"
          aria-label={label}
          accept=".jpg,.jpeg,.png,.tif,.tiff"
          multiple={multiple}
          disabled={disabled}
          onChange={(event) => {
            const selected = Array.from(event.target.files || []).sort((a, b) =>
              naturalOrder.compare(a.name, b.name),
            );
            if (selected.length) onChange(selected);
            event.target.value = "";
          }}
        />
      </label>
      {!!files.length && (
        <div className="prediction-file-list">
          {files.map((file, index) => (
            <div className="prediction-file" key={`${file.name}-${index}`}>
              <FileImageOutlined />
              <span>
                <strong>
                  {multiple ? `${index + 1}. ` : ""}
                  {file.name}
                </strong>
                <small>
                  {(file.size / 1024 / 1024).toLocaleString("ru-RU", {
                    maximumFractionDigits: 2,
                  })}{" "}
                  МБ
                </small>
              </span>
              {multiple && (
                <>
                  <Button
                    type="text"
                    size="small"
                    icon={<ArrowUpOutlined />}
                    aria-label={`Выше: ${file.name}`}
                    disabled={disabled || index === 0}
                    onClick={() => move(index, -1)}
                  />
                  <Button
                    type="text"
                    size="small"
                    icon={<ArrowDownOutlined />}
                    aria-label={`Ниже: ${file.name}`}
                    disabled={disabled || index === files.length - 1}
                    onClick={() => move(index, 1)}
                  />
                </>
              )}
              <Button
                type="text"
                size="small"
                icon={<CloseOutlined />}
                aria-label={`Убрать: ${file.name}`}
                disabled={disabled}
                onClick={() =>
                  onChange(files.filter((_, item) => item !== index))
                }
              />
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function apiError(error: unknown): string {
  if (axios.isCancel(error))
    return "Ожидание ответа остановлено. Уже запущенный расчёт на сервере может продолжаться.";
  if (axios.isAxiosError(error)) {
    const detail: unknown = error.response?.data?.detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail))
      return detail
        .map(
          (item) =>
            `${Array.isArray(item.loc) ? item.loc.slice(1).join(".") : "Данные"}: ${item.msg}`,
        )
        .join("; ");
    if (error.code === "ECONNABORTED")
      return "Сервер не ответил за 10 минут. Проверьте состояние модели перед повторным запуском.";
    if (!error.response)
      return "Нет соединения с сервером. Проверьте подключение и попробуйте ещё раз.";
    if (error.response.status === 413)
      return "Объём загруженных изображений превышает допустимый размер.";
  }
  return "Не удалось выполнить анализ. Попробуйте ещё раз.";
}

export const PatientPrediction = () => {
  const { id } = useParams<{ id: string }>();
  const validId =
    !!id &&
    /^\d+$/.test(id) &&
    Number.isSafeInteger(Number(id)) &&
    Number(id) > 0;
  const [mode, setMode] = useState<Mode>("blastocyst");
  const [image, setImage] = useState<File[]>([]);
  const [frames, setFrames] = useState<File[]>([]);
  const [framesFm, setFramesFm] = useState<File[]>([]);
  const [framesFp, setFramesFp] = useState<File[]>([]);
  const [hoursText, setHoursText] = useState("");
  const [validationError, setValidationError] = useState("");
  const controller = useRef<AbortController | null>(null);
  useEffect(() => () => controller.current?.abort(), []);
  const patientQuery = useQuery({
    queryKey: ["patient", id],
    queryFn: () => patientsApi.getPatient(Number(id)),
    enabled: validId,
  });
  const statusQuery = useQuery({
    queryKey: ["ml-status"],
    queryFn: mlApi.status,
    staleTime: 5000,
    refetchInterval: 15000,
    refetchOnWindowFocus: true,
  });
  const status = statusQuery.data;
  const unavailable =
    !!status &&
    (!status.enabled ||
      !!status.missing_dependencies.length ||
      !status[mode].weights_found);
  const mutation = useMutation({
    mutationFn: async (hours: number[]): Promise<Result> => {
      controller.current = new AbortController();
      if (mode === "blastocyst")
        return {
          kind: mode,
          data: await mlApi.blastocyst(image[0], controller.current.signal),
        };
      return {
        kind: mode,
        data: await mlApi.timelapse(
          { frames, hours, framesFm, framesFp },
          controller.current.signal,
        ),
      };
    },
    onSettled: () => {
      statusQuery.refetch();
    },
  });
  const changed = () => {
    setValidationError("");
    mutation.reset();
  };
  const submit = () => {
    let hours: number[] = [];
    const fail = (message: string) => setValidationError(message);
    const selected =
      mode === "blastocyst" ? image : [...frames, ...framesFm, ...framesFp];
    if (mode === "blastocyst" && image.length !== 1)
      return fail("Выберите одно фото бластоцисты.");
    if (mode === "timelapse" && !frames.length)
      return fail("Добавьте кадры центральной плоскости F0.");
    if (selected.some((file) => !isImage(file)))
      return fail("Поддерживаются изображения JPG, PNG и TIFF.");
    if (selected.some((file) => file.size === 0))
      return fail(
        "Среди выбранных файлов есть пустой. Удалите его и загрузите изображение.",
      );
    if (mode === "timelapse") {
      try {
        const text = hoursText.trim();
        const values: unknown = text.startsWith("[")
          ? JSON.parse(text)
          : text.split(",").map((value) => value.trim());
        if (
          !Array.isArray(values) ||
          values.some(
            (value) =>
              !["number", "string"].includes(typeof value) ||
              String(value).trim() === "",
          )
        )
          throw new Error();
        hours = values.map(Number);
        if (
          !hours.length ||
          hours.some((value) => !Number.isFinite(value) || value < 0)
        )
          throw new Error();
      } catch {
        return fail(
          "Укажите время кадров неотрицательными числами через запятую, например: 0, 0.5, 1.",
        );
      }
      if (hours.length !== frames.length)
        return fail(
          `Временных отметок: ${hours.length}, кадров F0: ${frames.length}. Для каждого кадра нужно одно значение.`,
        );
      if (hours.some((value, index) => index > 0 && value <= hours[index - 1]))
        return fail(
          "Время кадров должно строго возрастать. Проверьте порядок и значения.",
        );
      if (
        (framesFm.length && framesFm.length !== frames.length) ||
        (framesFp.length && framesFp.length !== frames.length)
      )
        return fail(
          "Дополнительные плоскости должны содержать столько же кадров, сколько F0.",
        );
    }
    setValidationError("");
    mutation.mutate(hours);
  };
  const pending = mutation.isPending;
  const back = (
    <Link to={validId ? `/patients/${id}` : "/patients"} className="back-link">
      <ArrowLeftOutlined />
      {validId ? "В карточку пациента" : "Все пациенты"}
    </Link>
  );
  if (patientQuery.isLoading)
    return (
      <>
        {back}
        <div className="panel loading-panel">
          <Skeleton active paragraph={{ rows: 6 }} />
        </div>
      </>
    );
  if (
    !validId ||
    (axios.isAxiosError(patientQuery.error) &&
      patientQuery.error.response?.status === 404)
  )
    return (
      <>
        {back}
        <Empty description="Пациент не найден" />
      </>
    );
  if (!patientQuery.data)
    return (
      <>
        {back}
        <Alert
          type="error"
          showIcon
          title="Не удалось загрузить пациента"
          action={
            <Button onClick={() => patientQuery.refetch()}>Повторить</Button>
          }
        />
      </>
    );
  const patient = patientQuery.data;
  return (
    <div className="prediction-page">
      <div className="breadcrumb">
        <Link to="/patients">Пациенты</Link>
        <span>/</span>
        <Link to={`/patients/${id}`}>{patient.medical_record_number}</Link>
        <span>/</span>
        <strong>Предикт</strong>
      </div>
      {back}
      <div className="page-heading">
        <div>
          <div className="eyebrow">ML · АНАЛИЗ ЭМБРИОНОВ</div>
          <h1>
            Предикт<span className="heading-dot">.</span>
          </h1>
          <p>
            Загрузите изображения, заполните параметры и получите ответ модели.
          </p>
        </div>
        <span className="prediction-patient">
          <ExperimentOutlined />
          Карта {patient.medical_record_number}
        </span>
      </div>
      <div className="prediction-layout">
        <div className="prediction-inputs">
          <section className="panel prediction-form">
            <div className="section-heading">
              <span className="section-icon">
                <ExperimentOutlined />
              </span>
              <div>
                <h2>Новый анализ</h2>
                <p>Выберите модель и подготовьте данные</p>
              </div>
            </div>
            <Tabs
              activeKey={mode}
              onChange={(key) => {
                setMode(key as Mode);
                changed();
              }}
              items={[
                {
                  key: "blastocyst",
                  label: "По фото · Гарднер",
                  disabled: pending,
                },
                {
                  key: "timelapse",
                  label: "Time-lapse · Кадры",
                  disabled: pending,
                },
              ]}
            />
            <div className="prediction-form-body">
              {statusQuery.isError && (
                <Alert
                  type="error"
                  showIcon
                  title="Не удалось проверить состояние моделей"
                  description="Проверьте подключение к серверу."
                  action={
                    <Button size="small" onClick={() => statusQuery.refetch()}>
                      Повторить
                    </Button>
                  }
                />
              )}
              {unavailable && (
                <Alert
                  type="warning"
                  showIcon
                  title="Модель пока недоступна"
                  description={
                    <>
                      <p>
                        {!status?.enabled
                          ? "ML-модуль отключён на сервере."
                          : "Для расчёта на сервере должны быть установлены ML-зависимости и загружены веса выбранной модели."}
                      </p>
                      <details>
                        <summary>Чего не хватает</summary>
                        {!!status?.missing_dependencies.length && (
                          <p>
                            Зависимости:{" "}
                            {status.missing_dependencies.join(", ")}.
                          </p>
                        )}
                        {!!status?.[mode].missing_files.length && (
                          <p>Веса: {status[mode].missing_files.join(", ")}.</p>
                        )}
                      </details>
                    </>
                  }
                />
              )}
              <div className="prediction-instructions">
                <strong>
                  {mode === "blastocyst"
                    ? "Оценка бластоцисты по шкале Гарднера"
                    : "Морфокинетика по последовательности кадров"}
                </strong>
                <p>
                  {mode === "blastocyst"
                    ? "Нужно одно фото эмбриона. Модель вернёт степень экспансии, оценку ВКМ, трофэктодермы и уверенность."
                    : "Загрузите кадры F0 и укажите время каждого кадра в часах после оплодотворения. Дополнительные фокальные плоскости необязательны."}
                </p>
              </div>
              {mode === "blastocyst" ? (
                <ImageFiles
                  label="Загрузить фото бластоцисты"
                  files={image}
                  disabled={pending}
                  onChange={(files) => {
                    setImage(files);
                    changed();
                  }}
                />
              ) : (
                <>
                  <ImageFiles
                    label="Загрузить кадры F0"
                    files={frames}
                    multiple
                    disabled={pending}
                    onChange={(files) => {
                      setFrames(files);
                      changed();
                    }}
                  />
                  <p className="prediction-hint">
                    Кадры сортируются по имени файла. Проверьте хронологию и при
                    необходимости измените порядок стрелками. Новый выбор файлов
                    заменяет текущий набор.
                  </p>
                  <label
                    className="prediction-field-label"
                    htmlFor="frame-hours"
                  >
                    Время каждого кадра, ч после оплодотворения
                  </label>
                  <Input.TextArea
                    id="frame-hours"
                    value={hoursText}
                    onChange={(event) => {
                      setHoursText(event.target.value);
                      changed();
                    }}
                    placeholder="Например: 0, 0.5, 1, 1.5"
                    rows={3}
                    disabled={pending}
                  />
                  <p className="prediction-hint">
                    Значения через запятую в том же порядке, что и кадры F0.
                    Десятичный разделитель — точка. Кадров F0: {frames.length}.
                  </p>
                  <details className="prediction-extra">
                    <summary>Дополнительные плоскости F−15 и F+15</summary>
                    <p className="prediction-hint">
                      Количество и порядок кадров в каждой плоскости должны
                      совпадать с F0.
                    </p>
                    <ImageFiles
                      label="Загрузить кадры F−15"
                      files={framesFm}
                      multiple
                      disabled={pending}
                      onChange={(files) => {
                        setFramesFm(files);
                        changed();
                      }}
                    />
                    <ImageFiles
                      label="Загрузить кадры F+15"
                      files={framesFp}
                      multiple
                      disabled={pending}
                      onChange={(files) => {
                        setFramesFp(files);
                        changed();
                      }}
                    />
                  </details>
                </>
              )}
              {validationError && (
                <Alert
                  type="error"
                  showIcon
                  title="Проверьте данные"
                  description={validationError}
                />
              )}
              {mutation.isError && (
                <Alert
                  type="error"
                  showIcon
                  title="Анализ не выполнен"
                  description={apiError(mutation.error)}
                />
              )}
              <div className="prediction-submit">
                <Button
                  type="primary"
                  icon={<PlayCircleOutlined />}
                  loading={pending}
                  disabled={unavailable || statusQuery.isPending}
                  onClick={submit}
                >
                  Запустить предикт
                </Button>
                {pending && (
                  <Button onClick={() => controller.current?.abort()}>
                    Остановить ожидание
                  </Button>
                )}
              </div>
              {pending && (
                <p className="prediction-hint" role="status">
                  Анализ выполняется. Первый запуск может занять больше времени:
                  сервер загружает модель.
                </p>
              )}
            </div>
          </section>
          <p className="prediction-storage-note">
            Результат доступен на этой странице до её закрытия или изменения
            входных данных. В медицинскую карту автоматически не сохраняется.
          </p>
        </div>
        <aside className="prediction-output">
          {pending ? (
            <section className="panel loading-panel">
              <h2>Модель анализирует данные</h2>
              <Skeleton active paragraph={{ rows: 5 }} />
            </section>
          ) : mutation.data ? (
            <PredictionResult
              result={mutation.data}
              patientNumber={patient.medical_record_number}
            />
          ) : (
            <section className="panel prediction-placeholder">
              <span className="stat-icon blue">
                <ExperimentOutlined />
              </span>
              <h2>Здесь появится результат</h2>
              <p>
                Загрузите данные и запустите анализ. Ответ модели будет показан
                рядом с формой.
              </p>
              <div className="prediction-readiness">
                <i className={`online-dot ${unavailable ? "not-ready" : ""}`} />
                {statusQuery.isPending
                  ? "Проверяем модели…"
                  : statusQuery.isError
                    ? "Статус моделей неизвестен"
                    : unavailable
                      ? "Требуется настройка модели"
                      : "Модель готова к запуску"}
              </div>
              <Button
                type="text"
                icon={<ReloadOutlined />}
                loading={statusQuery.isFetching}
                onClick={() => statusQuery.refetch()}
              >
                Проверить готовность
              </Button>
            </section>
          )}
          <div className="prediction-disclaimer">
            Только для исследования и проверки эмбриологом. Не является
            клиническим решением.
          </div>
        </aside>
      </div>
    </div>
  );
};
