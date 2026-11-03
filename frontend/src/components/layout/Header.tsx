import { Layout, Input, Select, Button, Dropdown, Space, Tag } from 'antd';
import { SearchOutlined, UserOutlined, LogoutOutlined, GlobalOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../../context/AuthContext';
import { UserRole } from '../../types';

const { Header: AntHeader } = Layout;

export const Header = () => {
  const { t, i18n } = useTranslation();
  const { user, logout } = useAuth();

  const handleLanguageChange = (lang: string) => {
    i18n.changeLanguage(lang);
    localStorage.setItem('language', lang);
  };

  const userMenuItems = [
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: t('auth.logout'),
      onClick: logout,
    },
  ];

  const getRoleLabel = (role: UserRole) => {
    return role === UserRole.REPRODUCTOLOGIST
      ? t('roles.reproductologist')
      : t('roles.embryologist');
  };

  const getRoleColor = (role: UserRole) => {
    return role === UserRole.REPRODUCTOLOGIST ? 'cyan' : 'blue';
  };

  return (
    <AntHeader
      style={{
        background: '#fff',
        padding: '0 24px',
        borderBottom: '1px solid #f0f0f0',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
      }}
    >
      <div style={{ flex: 1, maxWidth: 500 }}>
        <Input
          prefix={<SearchOutlined />}
          placeholder={t('patients.search')}
          size="middle"
        />
      </div>

      <Space size="middle">
        <Select
          value={i18n.language}
          onChange={handleLanguageChange}
          style={{ width: 120 }}
          suffixIcon={<GlobalOutlined />}
          options={[
            { value: 'ru', label: 'Русский' },
            { value: 'kk', label: 'Қазақша' },
          ]}
        />

        {user && (
          <>
            <Tag color={getRoleColor(user.role)}>{getRoleLabel(user.role)}</Tag>
            <Dropdown menu={{ items: userMenuItems }} placement="bottomRight">
              <Button icon={<UserOutlined />}>
                {user.full_name}
              </Button>
            </Dropdown>
          </>
        )}
      </Space>
    </AntHeader>
  );
};
