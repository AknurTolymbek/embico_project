import { Card, Empty, Typography } from 'antd';
import { useTranslation } from 'react-i18next';

const { Title } = Typography;

export const SettingsPage = () => {
  const { t } = useTranslation();

  return (
    <div>
      <Title level={2}>{t('menu.settings')}</Title>
      <Card>
        <Empty description="Раздел в разработке. Здесь будут настройки системы." />
      </Card>
    </div>
  );
};
