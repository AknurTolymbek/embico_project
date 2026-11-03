import { NavLink } from "react-router-dom";
import {
  TeamOutlined,
  ExperimentOutlined,
  SyncOutlined,
  FileTextOutlined,
  SafetyCertificateOutlined,
  ArrowUpOutlined,
} from "@ant-design/icons";

export const Sidebar = () => (
  <aside className="sidebar">
    <a className="brand" href="/patients" aria-label="EMBICO — пациенты">
      <span className="brand-symbol">
        <i />
        <i />
        <i />
      </span>
      <span>
        embico
        <small>ПЛАТФОРМА ДЛЯ ЭКО-КЛИНИК</small>
      </span>
    </a>
    <div className="clinic-switch">
      <span className="clinic-icon">
        <ExperimentOutlined />
      </span>
      <div>
        <strong>Рабочее пространство</strong>
        <small>Центр репродукции</small>
      </div>
      <span className="online-dot" />
    </div>
    <div className="nav-caption">КЛИНИКА</div>
    <nav className="main-nav" aria-label="Основная навигация">
      <NavLink to="/patients" aria-label="Пациенты">
        <TeamOutlined />
        <span>Пациенты</span>
        <span className="nav-indicator" />
      </NavLink>
      <NavLink to="/cycles" aria-label="Циклы лечения">
        <SyncOutlined />
        <span>Циклы лечения</span>
        <span className="nav-indicator" />
      </NavLink>
      <NavLink to="/lab" aria-label="Лаборатория">
        <ExperimentOutlined />
        <span>Лаборатория</span>
        <span className="nav-indicator" />
      </NavLink>
      <NavLink to="/documents" aria-label="Документы">
        <FileTextOutlined />
        <span>Документы</span>
        <span className="nav-indicator" />
      </NavLink>
    </nav>
    <div className="sidebar-bottom">
      <div className="care-note">
        <span className="care-orbit">✳</span>
        <strong>Каждая история важна</strong>
        <p>Всё необходимое для заботы о пациентах — в одном месте.</p>
        <span className="care-caption">
          EMBICO CARE <ArrowUpOutlined />
        </span>
      </div>
      <div className="secure-label">
        <SafetyCertificateOutlined /> Медицинские данные
      </div>
    </div>
  </aside>
);
