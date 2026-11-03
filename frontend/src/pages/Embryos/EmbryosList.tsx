import { Card, Empty, Typography } from 'antd';
import { useTranslation } from 'react-i18next';

const { Title } = Typography;

export const EmbryosList = () => {
  const { t } = useTranslation();

  return (
    <div>
      <Title level={2}>{t('menu.embryos')}</Title>
      <Card>
        <Empty description="Раздел в разработке. Здесь будет реестр эмбрионов с time-lapse." />
      </Card>
    </div>
  );
};
