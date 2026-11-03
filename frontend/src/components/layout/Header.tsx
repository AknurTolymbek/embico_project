import { Avatar, Dropdown, Button } from "antd";
import {
  DownOutlined,
  UserOutlined,
  LogoutOutlined,
  TeamOutlined,
} from "@ant-design/icons";
import { Link } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";

export const Header = () => {
  const { user, logout } = useAuth();
  return (
    <header className="topbar">
      <Link to="/patients" className="topbar-location">
        <TeamOutlined />
        <span>Клиническое пространство</span>
      </Link>
      <div className="topbar-right">
        <span className="workspace-status">
          <i /> Рабочее пространство
        </span>
        <span className="header-divider" />
        <Dropdown
          menu={{
            items: [
              {
                key: "logout",
                label: "Выйти",
                icon: <LogoutOutlined />,
                onClick: logout,
              },
            ],
          }}
          trigger={["click"]}
        >
          <Button type="text" className="profile-button">
            <Avatar size={34} icon={<UserOutlined />} />
            <span>
              <strong>{user?.full_name || "Гость"}</strong>
              <small>
                {user?.id === 0 ? "Гостевой доступ" : "Специалист клиники"}
              </small>
            </span>
            <DownOutlined />
          </Button>
        </Dropdown>
      </div>
    </header>
  );
};
