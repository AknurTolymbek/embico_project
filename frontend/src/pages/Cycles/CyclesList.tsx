import { Card, Empty, Typography } from 'antd';
import { useTranslation } from 'react-i18next';

const { Title } = Typography;

export const CyclesList = () => {
  const { t } = useTranslation();

  return (
    <div>
      <Title level={2}>{t('menu.cycles')}</Title>
      <Card>
        <Empty description="Раздел в разработке. Здесь будет список всех циклов ЭКО." />
      </Card>
    </div>
  );
};
