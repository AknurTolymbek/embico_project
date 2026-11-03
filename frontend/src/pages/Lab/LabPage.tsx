import { Card, Empty, Typography } from 'antd';
import { useTranslation } from 'react-i18next';

const { Title } = Typography;

export const LabPage = () => {
  const { t } = useTranslation();

  return (
    <div>
      <Title level={2}>{t('menu.lab')}</Title>
      <Card>
        <Empty description="Раздел в разработке. Здесь будут эмбриологические данные." />
      </Card>
    </div>
  );
};
