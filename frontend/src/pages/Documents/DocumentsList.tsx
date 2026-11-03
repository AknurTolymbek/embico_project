import { Card, Empty, Typography } from 'antd';
import { useTranslation } from 'react-i18next';

const { Title } = Typography;

export const DocumentsList = () => {
  const { t } = useTranslation();

  return (
    <div>
      <Title level={2}>{t('menu.documents')}</Title>
      <Card>
        <Empty description="Раздел в разработке. Здесь будут протоколы циклов." />
      </Card>
    </div>
  );
};
