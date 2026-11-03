import { Alert, Button, Empty, Progress, Table } from "antd";
import { DownloadOutlined, ExperimentOutlined } from "@ant-design/icons";
import type { PredictionResult as Result } from "../../types/ml";

const number = (value: number) =>
  value.toLocaleString("ru-RU", { maximumFractionDigits: 2 });
const percent = (value: number) => `${number(value * 100)}%`;
function ProbabilityGroup({
  title,
  values,
  labels,
  unavailable,
}: {
  title: string;
  values: number[] | null;
  labels: string[];
  unavailable: string;
}) {
  return (
    <section className="prediction-probability-group" aria-label={title}>
      <h3 className="prediction-subheading">
        {title}
        {!!values?.length && <span>{percent(Math.max(...values))}</span>}
      </h3>
      {values?.length ? (
        <div className="probabilities">
          {values.map((value, index) => (
            <div key={labels[index]}>
              <span>{labels[index]}</span>
              <Progress
                percent={value * 100}
                showInfo={false}
                size="small"
                strokeColor="#7195df"
              />
              <small>{percent(value)}</small>
            </div>
          ))}
        </div>
      ) : (
        <p className="prediction-explanation">{unavailable}</p>
      )}
    </section>
  );
}

export const PredictionResult = ({
  result,
  patientNumber,
}: {
  result: Result;
  patientNumber: string;
}) => {
  const data = result.data;
  const download = () => {
    const body = JSON.stringify(
      {
        medical_record_number: patientNumber,
        calculated_at: new Date().toISOString(),
        ...result,
      },
      null,
      2,
    );
    const url = URL.createObjectURL(
      new Blob([body], { type: "application/json" }),
    );
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `embico-${result.kind}-${Date.now()}.json`;
    anchor.click();
    URL.revokeObjectURL(url);
  };
  return (
    <section
      className="panel prediction-result"
      aria-label="Результат анализа"
      aria-live="polite"
    >
      <div className="section-heading">
        <span className="section-icon">
          <ExperimentOutlined />
        </span>
        <div>
          <h2>Результат анализа</h2>
          <p>Карта {patientNumber}</p>
        </div>
        <Button icon={<DownloadOutlined />} onClick={download}>
          JSON
        </Button>
      </div>
      <div className="prediction-result-body">
        <Alert
          type={data.status === "ok" ? "success" : "warning"}
          showIcon
          title={
            data.status === "ok"
              ? "Анализ завершён"
              : "Модель не даёт рекомендацию"
          }
          description={
            data.status === "no_recommendation"
              ? "Проверьте ограничения и предупреждения ниже. Результат требует оценки эмбриологом."
              : undefined
          }
        />
        {result.kind === "blastocyst" ? (
          <>
            <div className="prediction-score">
              <span>Оценка модели · EXP0–EXP4</span>
              <strong>{result.data.gardner}</strong>
              <div className="prediction-confidence">
                <span>Уверенность модели</span>
                <b>{percent(result.data.confidence)}</b>
              </div>
              <Progress
                percent={Math.round(result.data.confidence * 100)}
                showInfo={false}
                strokeColor="#7195df"
              />
            </div>
            <div className="prediction-values">
              {[
                ["Экспансия", `EXP${result.data.expansion_class}`],
                [
                  "Внутренняя клеточная масса",
                  result.data.icm ?? "Не определена",
                ],
                ["Трофэктодерма", result.data.te ?? "Не определена"],
              ].map(([label, value]) => (
                <div key={label}>
                  <span>{label}</span>
                  <strong>{value}</strong>
                </div>
              ))}
            </div>
            <p className="prediction-explanation">
              Итоговая уверенность — минимальная уверенность среди оценённых
              компонентов: экспансии, ВКМ (ICM) и трофэктодермы (TE). Классы
              экспансии отображаются как в модели: EXP0–EXP4.
            </p>
            <ProbabilityGroup
              title="Вероятности степени экспансии"
              values={result.data.probabilities.exp}
              labels={["EXP0", "EXP1", "EXP2", "EXP3", "EXP4"]}
              unavailable="Модель не вернула вероятности экспансии."
            />
            <ProbabilityGroup
              title="Вероятности ВКМ (ICM)"
              values={result.data.probabilities.icm}
              labels={["A", "B", "C"]}
              unavailable={
                result.data.expansion_class < 2
                  ? "ВКМ не оценивается для этой стадии."
                  : "Модель не вернула вероятности ВКМ."
              }
            />
            <ProbabilityGroup
              title="Вероятности трофэктодермы (TE)"
              values={result.data.probabilities.te}
              labels={["A", "B", "C"]}
              unavailable={
                result.data.expansion_class < 2
                  ? "Трофэктодерма не оценивается для этой стадии."
                  : "Модель не вернула вероятности трофэктодермы."
              }
            />
          </>
        ) : (
          <>
            <div className="prediction-score">
              <span>Последняя распознанная стадия</span>
              <strong>{result.data.last_stage}</strong>
              <div className="prediction-confidence">
                <span>Уверенность распознавания</span>
                <b>{percent(result.data.stage_confidence)}</b>
              </div>
              <Progress
                percent={Math.round(result.data.stage_confidence * 100)}
                showInfo={false}
                strokeColor="#7195df"
              />
            </div>
            <div className="prediction-values">
              <div>
                <span>Кадров</span>
                <strong>{result.data.n_frames}</strong>
              </div>
              <div>
                <span>Длительность наблюдения</span>
                <strong>{number(result.data.video_hours)} ч</strong>
              </div>
              <div>
                <span>Исследовательский ранг</span>
                <strong>
                  {result.data.blastocyst_rank_research === null
                    ? "Недоступен"
                    : number(result.data.blastocyst_rank_research)}
                </strong>
              </div>
            </div>
            <p className="prediction-explanation">
              {result.data.blastocyst_rank_meaning}. Ранг не является
              вероятностью успешного исхода лечения.
            </p>
            {result.data.blastocyst_probability_research !== null && (
              <p className="prediction-explanation">
                Исследовательская вероятность бластоцисты:{" "}
                {percent(result.data.blastocyst_probability_research)}.
              </p>
            )}
            <h3 className="prediction-subheading">События и морфокинетика</h3>
            <Table
              size="small"
              rowKey="name"
              pagination={false}
              locale={{
                emptyText: (
                  <Empty
                    image={Empty.PRESENTED_IMAGE_SIMPLE}
                    description="Показатели не определены"
                  />
                ),
              }}
              dataSource={Object.entries({
                ...result.data.events_hours,
                ...result.data.morphokinetics,
              }).map(([name, value]) => ({ name, value }))}
              columns={[
                { title: "Показатель", dataIndex: "name" },
                {
                  title: "Время, ч",
                  dataIndex: "value",
                  render: (value: number | null) =>
                    value === null ? "Не определено" : number(value),
                },
              ]}
            />
            {!!result.data.flags.length && (
              <Alert
                type="warning"
                showIcon
                title="Флаги отклонений"
                description={
                  <ul>
                    {result.data.flags.map((flag, index) => (
                      <li key={index}>{flag}</li>
                    ))}
                  </ul>
                }
              />
            )}
          </>
        )}
        {!!data.warnings.length && (
          <Alert
            type="warning"
            showIcon
            title="Предупреждения модели"
            description={
              <ul>
                {data.warnings.map((warning, index) => (
                  <li key={index}>{warning}</li>
                ))}
              </ul>
            }
          />
        )}
        <div className="prediction-disclaimer">{data.disclaimer}</div>
        <div className="prediction-version">
          Версия модели: {data.model_version}
        </div>
      </div>
    </section>
  );
};
