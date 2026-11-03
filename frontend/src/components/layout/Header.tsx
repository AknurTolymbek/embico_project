import { Avatar, Dropdown, Button, message } from "antd";
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
                onClick: async () => {
                  try {
                    await logout();
                  } catch {
                    message.error(
                      "Не удалось выйти. Проверьте соединение и попробуйте ещё раз.",
                    );
                  }
                },
              },
            ],
          }}
          trigger={["click"]}
        >
          <Button type="text" className="profile-button">
            <Avatar size={34} icon={<UserOutlined />} />
            <span>
              <strong>{user?.full_name || user?.username}</strong>
              <small>{user?.role === "admin" ? "Администратор" : "Врач"}</small>
            </span>
            <DownOutlined />
          </Button>
        </Dropdown>
      </div>
    </header>
  );
};
