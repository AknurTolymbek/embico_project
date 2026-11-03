import { FileTextOutlined } from "@ant-design/icons";
import { UnderDevelopment } from "../../components/UnderDevelopment";

export const DocumentsList = () => (
  <UnderDevelopment
    title="Документы"
    icon={<FileTextOutlined />}
    description="Здесь появятся протоколы циклов, медицинские документы и материалы пациентов."
  />
);
