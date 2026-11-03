import { SyncOutlined } from "@ant-design/icons";
import { UnderDevelopment } from "../../components/UnderDevelopment";

export const CyclesList = () => (
  <UnderDevelopment
    title="Циклы лечения"
    icon={<SyncOutlined />}
    description="Здесь появятся циклы ЭКО, этапы лечения и история протоколов пациентов."
  />
);
