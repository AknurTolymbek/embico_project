import { Card, Empty, Typography } from 'antd';
import { useTranslation } from 'react-i18next';

const { Title } = Typography;

export const TeamPage = () => {
  const { t } = useTranslation();

  return (
    <div>
      <Title level={2}>{t('menu.team')}</Title>
      <Card>
        <Empty description="Раздел в разработке. Здесь будет управление пользователями." />
      </Card>
    </div>
  );
};
