import React, { useEffect, useMemo, useState } from 'react';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

const TIMELINE_STEPS = [
  { value: 'received', label: 'Teslim Alındı' },
  { value: 'inspection', label: 'İnceleme Aşamasında' },
  { value: 'repair', label: 'Tamir Aşamasında' },
  { value: 'ready', label: 'Teslime Hazır' },
  { value: 'delivered', label: 'Teslim Edildi' },
];

const STATUS_LABELS = {
  received: 'Teslim Alındı',
  inspection: 'İnceleme Aşamasında',
  repair: 'Tamir Aşamasında',
  ready: 'Teslime Hazır',
  delivered: 'Teslim Edildi',
  cancelled: 'İptal Edildi',
};

const currencyFormatter = new Intl.NumberFormat('tr-TR', {
  style: 'currency',
  currency: 'TRY',
});

function formatCurrency(value) {
  if (value === null || value === undefined || value === '') {
    return 'Belirtilmemiş';
  }

  const numericValue = Number(value);
  if (Number.isNaN(numericValue)) {
    return 'Belirtilmemiş';
  }

  return currencyFormatter.format(numericValue);
}

function formatDate(value) {
  if (!value) {
    return 'Belirtilmemiş';
  }

  const parsedDate = new Date(value);
  if (Number.isNaN(parsedDate.getTime())) {
    return 'Belirtilmemiş';
  }

  return parsedDate.toLocaleString('tr-TR');
}

function normalizeText(value) {
  if (value === null || value === undefined || value === '') {
    return 'Belirtilmemiş';
  }

  return String(value);
}

function getStatusLabel(statusValue) {
  const normalizedStatus = (statusValue || '').toString().trim().toLowerCase();
  if (!normalizedStatus) {
    return 'Belirtilmemiş';
  }

  if (STATUS_LABELS[normalizedStatus]) {
    return STATUS_LABELS[normalizedStatus];
  }

  return `Bilinmeyen durum (${normalizedStatus})`;
}

function WorkOrderStatusTimeline({ status }) {
  const normalizedStatus = (status || '').toString().trim().toLowerCase();
  const currentStepIndex = TIMELINE_STEPS.findIndex((step) => step.value === normalizedStatus);
  const isCancelled = normalizedStatus === 'cancelled';
  const isUnknown = !isCancelled && currentStepIndex === -1;

  return (
    <div className="workorder-timeline-wrapper">
      {isCancelled && <p className="timeline-cancelled">Bu iş emri iptal edildi.</p>}
      {isUnknown && (
        <p className="timeline-unknown">
          Bu iş emri için tanımsız bir durum geldi: {normalizeText(status)}
        </p>
      )}

      <ol className="workorder-timeline" aria-label="İş emri durum zaman çizelgesi">
        {TIMELINE_STEPS.map((step, index) => {
          let stepClassName = 'pending';

          if (!isCancelled && !isUnknown) {
            if (index < currentStepIndex) {
              stepClassName = 'completed';
            } else if (index === currentStepIndex) {
              stepClassName = 'active';
            }
          }

          return (
            <li key={step.value} className={`timeline-step ${stepClassName}`}>
              <span className="timeline-dot" aria-hidden="true" />
              <span className="timeline-label">{step.label}</span>
            </li>
          );
        })}
      </ol>
    </div>
  );
}

function CustomerWorkOrders({ onBack }) {
  const [workOrders, setWorkOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState('');
  const [tokenMissing, setTokenMissing] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem('access_token');

    if (!token) {
      setTokenMissing(true);
      setLoading(false);
      setErrorMessage('');
      setWorkOrders([]);
      return;
    }

    const controller = new AbortController();

    const fetchWorkOrders = async () => {
      try {
        setLoading(true);
        setErrorMessage('');
        setTokenMissing(false);

        const response = await fetch(`${API_BASE_URL}/my/work-orders`, {
          method: 'GET',
          headers: {
            Authorization: `Bearer ${token}`,
          },
          signal: controller.signal,
        });

        if (response.status === 401) {
          setErrorMessage('Oturumunuz geçersiz veya süresi dolmuş. Lütfen tekrar giriş yapın.');
          setWorkOrders([]);
          return;
        }

        if (response.status === 403) {
          setErrorMessage('Bu alan yalnızca müşteri hesapları tarafından kullanılabilir.');
          setWorkOrders([]);
          return;
        }

        if (!response.ok) {
          setErrorMessage('İş emirleri yüklenirken bir hata oluştu. Lütfen daha sonra tekrar deneyin.');
          setWorkOrders([]);
          return;
        }

        const payload = await response.json();
        if (!Array.isArray(payload)) {
          setErrorMessage('API yanıtı beklenen formatta değil.');
          setWorkOrders([]);
          return;
        }

        setWorkOrders(payload);
      } catch (error) {
        if (error?.name === 'AbortError') {
          return;
        }

        setErrorMessage('Backend sunucusuna ulaşılamadı. Lütfen bağlantınızı ve backend servisini kontrol edin.');
        setWorkOrders([]);
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false);
        }
      }
    };

    fetchWorkOrders();

    return () => {
      controller.abort();
    };
  }, []);

  const content = useMemo(() => {
    if (loading) {
      return <p className="workorder-state-message">İş emirleriniz yükleniyor...</p>;
    }

    if (tokenMissing) {
      return <p className="workorder-state-message">İş emirlerinizi görüntülemek için müşteri hesabıyla giriş yapmalısınız.</p>;
    }

    if (errorMessage) {
      return <p className="workorder-state-message ui-error">{errorMessage}</p>;
    }

    if (workOrders.length === 0) {
      return <p className="workorder-state-message">Henüz kayıtlı bir iş emriniz bulunmuyor.</p>;
    }

    return (
      <ul className="workorder-list">
        {workOrders.map((workOrder) => (
          <li key={workOrder.id} className="workorder-card-wrapper">
            <article className="workorder-card">
              <div className="workorder-header">
                <h3>İş Emri #{normalizeText(workOrder.id)}</h3>
                <p className="workorder-status-badge">{getStatusLabel(workOrder.status)}</p>
              </div>
              
              <div className="workorder-meta-primary">
                <p><strong>İşletme:</strong> {normalizeText(workOrder.business_name)}</p>
                <p><strong>Araç:</strong> {normalizeText(workOrder.vehicle_plate)} - {normalizeText(workOrder.vehicle_model)}</p>
                <p><strong>Hizmet:</strong> {normalizeText(workOrder.service_type)}</p>
                <p><strong>Fiyat:</strong> {formatCurrency(workOrder.price)}</p>
              </div>
              
              <div className="workorder-timeline-wrap">
                <WorkOrderStatusTimeline status={workOrder.status} />
              </div>
              
              <div className="workorder-meta-secondary">
                <p className="workorder-meta-date"><strong>Oluşturulma:</strong> {formatDate(workOrder.created_at)}</p>
                {workOrder.updated_at && (
                  <p className="workorder-meta-date"><strong>Güncelleme:</strong> {formatDate(workOrder.updated_at)}</p>
                )}
              </div>
            </article>
          </li>
        ))}
      </ul>
    );
  }, [loading, tokenMissing, errorMessage, workOrders]);

  return (
    <section className="customer-workorders-page">
      <div className="customer-workorders-header">
        <div>
          <h2>İş Emirlerim</h2>
          <p>Oluşturduğunuz iş emirlerinin durum ve detaylarını takip edin.</p>
        </div>
        <button onClick={onBack} className="business-detail-back-button">İşletmelere Geri Dön</button>
      </div>
      {content}
    </section>
  );
}

export default CustomerWorkOrders;