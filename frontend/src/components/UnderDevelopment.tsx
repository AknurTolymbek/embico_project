import type { ReactNode } from "react";
import { Link } from "react-router-dom";
import { ArrowLeftOutlined, ToolOutlined } from "@ant-design/icons";
import "./under-development.css";

export const UnderDevelopment = ({
  title,
  description,
  icon,
}: {
  title: string;
  description: string;
  icon: ReactNode;
}) => (
  <div className="development-page">
    <div className="breadcrumb">
      Клиника <span>/</span>
      <strong>{title}</strong>
    </div>
    <div className="page-heading">
      <div>
        <div className="eyebrow">КЛИНИЧЕСКОЕ ПРОСТРАНСТВО</div>
        <h1>
          {title}
        </h1>
      </div>
    </div>
    <section
      className="panel development-panel"
      aria-labelledby="development-title"
    >
      <div className="development-icon">
        {icon}
        <span>
          <ToolOutlined />
        </span>
      </div>
      <span className="development-status">Раздел в разработке</span>
      <h2 id="development-title">В стадии разработки</h2>
      <p>{description}</p>
      <Link className="development-return" to="/patients">
        <ArrowLeftOutlined /> К пациентам
      </Link>
    </section>
  </div>
);
