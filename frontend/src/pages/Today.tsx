import { Card, Empty, Typography } from 'antd';
import { useTranslation } from 'react-i18next';

const { Title } = Typography;

export const Today = () => {
  const { t } = useTranslation();

  return (
    <div>
      <Title level={2}>{t('menu.today')}</Title>
      <Card>
        <Empty description="Раздел в разработке. Здесь будет очередь задач и активные циклы." />
      </Card>
    </div>
  );
};
