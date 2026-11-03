import { Menu } from 'antd';
import { useNavigate, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import {
  CalendarOutlined,
  TeamOutlined,
  SyncOutlined,
  ExperimentOutlined,
  BugOutlined,
  FileTextOutlined,
  UsergroupAddOutlined,
  SettingOutlined,
} from '@ant-design/icons';

export const Sidebar = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { t } = useTranslation();

  const menuItems = [
    {
      key: '/today',
      icon: <CalendarOutlined />,
      label: t('menu.today'),
    },
    {
      key: '/patients',
      icon: <TeamOutlined />,
      label: t('menu.patients'),
    },
    {
      key: '/cycles',
      icon: <SyncOutlined />,
      label: t('menu.cycles'),
    },
    {
      key: '/lab',
      icon: <ExperimentOutlined />,
      label: t('menu.lab'),
    },
    {
      key: '/embryos',
      icon: <BugOutlined />,
      label: t('menu.embryos'),
    },
    {
      key: '/documents',
      icon: <FileTextOutlined />,
      label: t('menu.documents'),
    },
    {
      type: 'divider',
    },
    {
      key: '/team',
      icon: <UsergroupAddOutlined />,
      label: t('menu.team'),
    },
    {
      key: '/settings',
      icon: <SettingOutlined />,
      label: t('menu.settings'),
    },
  ];

  const handleMenuClick = ({ key }: { key: string }) => {
    navigate(key);
  };

  return (
    <div style={{ height: '100%', background: '#001529' }}>
      <div
        style={{
          padding: '24px',
          color: '#fff',
          fontSize: '20px',
          fontWeight: 600,
        }}
      >
        EMBICO
      </div>
      <Menu
        theme="dark"
        mode="inline"
        selectedKeys={[location.pathname]}
        onClick={handleMenuClick}
        items={menuItems}
        style={{ borderRight: 0 }}
      />
    </div>
  );
};
