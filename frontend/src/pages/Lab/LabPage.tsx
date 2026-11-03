import { ExperimentOutlined } from "@ant-design/icons";
import { UnderDevelopment } from "../../components/UnderDevelopment";

export const LabPage = () => (
  <UnderDevelopment
    title="Лаборатория"
    icon={<ExperimentOutlined />}
    description="Здесь появятся эмбриологические данные и результаты лабораторных исследований."
  />
);
