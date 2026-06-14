import React, { useEffect, useMemo, useRef, useState } from 'react';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

const STATUS_OPTIONS = [
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
};

const currencyFormatter = new Intl.NumberFormat('tr-TR', {
  style: 'currency',
  currency: 'TRY',
});

function normalizeText(value) {
  if (value === null || value === undefined || value === '') {
    return 'Belirtilmemiş';
  }
  return String(value);
}

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

  return parsedDate.toLocaleString('tr-TR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

function getStatusLabel(statusValue) {
  const normalized = (statusValue || '').toString().trim().toLowerCase();
  if (!normalized) {
    return 'Belirtilmemiş';
  }
  return STATUS_LABELS[normalized] || `Bilinmeyen durum (${normalized})`;
}

function getErrorMessage(responseStatus, payload, fallbackMessage) {
  if (responseStatus === 401) {
    return 'Oturumunuz geçersiz veya süresi dolmuş. Lütfen tekrar giriş yapın.';
  }

  if (responseStatus === 403) {
    return 'Bu alan yalnızca işletme sahibi hesapları tarafından kullanılabilir.';
  }

  if (payload && payload.detail) {
    if (typeof payload.detail === 'string') {
      return payload.detail;
    }
    return JSON.stringify(payload.detail);
  }

  return fallbackMessage;
}

function parseCustomerLabel(customer) {
  const fullName = (customer?.full_name || '').trim();
  const email = normalizeText(customer?.email);
  if (fullName) {
    return `${fullName} - ${email}`;
  }
  return email;
}

function parseVehicleLabel(vehicle) {
  const plate = normalizeText(vehicle?.plate);
  const make = normalizeText(vehicle?.make);
  const model = normalizeText(vehicle?.model);
  const year = normalizeText(vehicle?.year);
  return `${plate} - ${make} ${model} (${year})`;
}

function OwnerWorkOrdersPanel({ onBack }) {
  const [initialLoading, setInitialLoading] = useState(true);
  const [authErrorMessage, setAuthErrorMessage] = useState('');
  const [tokenMissing, setTokenMissing] = useState(false);
  const [isBusinessOwner, setIsBusinessOwner] = useState(true);

  const [ownerBusinesses, setOwnerBusinesses] = useState([]);
  const [selectedBusinessId, setSelectedBusinessId] = useState('');

  const [customers, setCustomers] = useState([]);
  const [customersLoading, setCustomersLoading] = useState(false);

  const [workOrders, setWorkOrders] = useState([]);
  const [workOrdersLoading, setWorkOrdersLoading] = useState(false);
  const [workOrdersError, setWorkOrdersError] = useState('');

  const [selectedCustomerId, setSelectedCustomerId] = useState('');
  const [vehicles, setVehicles] = useState([]);
  const [vehiclesLoading, setVehiclesLoading] = useState(false);
  const [vehiclesError, setVehiclesError] = useState('');
  const [selectedVehicleId, setSelectedVehicleId] = useState('');

  const [serviceType, setServiceType] = useState('');
  const [price, setPrice] = useState('');
  const [formError, setFormError] = useState('');
  const [formSuccess, setFormSuccess] = useState('');
  const [formSubmitting, setFormSubmitting] = useState(false);

  const [statusSelections, setStatusSelections] = useState({});
  const [statusUpdatingMap, setStatusUpdatingMap] = useState({});
  const [statusError, setStatusError] = useState('');
  const [statusSuccess, setStatusSuccess] = useState('');

  const [serviceCatalog, setServiceCatalog] = useState([]);
  const [businessServices, setBusinessServices] = useState([]);
  const [selectedServiceId, setSelectedServiceId] = useState('');
  const [newMinimumPrice, setNewMinimumPrice] = useState('');
  const [servicesLoading, setServicesLoading] = useState(false);
  const [servicesError, setServicesError] = useState('');
  const [servicesSuccess, setServicesSuccess] = useState('');
  const [serviceSubmitting, setServiceSubmitting] = useState(false);
  const [priceEditMap, setPriceEditMap] = useState({});
  const [updatingServiceId, setUpdatingServiceId] = useState(null);
  const [deletingServiceId, setDeletingServiceId] = useState(null);

  const tokenRef = useRef('');
  const vehicleRequestIdRef = useRef(0);

  const hasOwnerBusinesses = ownerBusinesses.length > 0;
  const hasCustomers = customers.length > 0;
  const hasVehicles = vehicles.length > 0;
  const hasWorkOrders = workOrders.length > 0;

  async function safeJson(response) {
    try {
      return await response.json();
    } catch {
      return null;
    }
  }

  async function fetchWorkOrders({ signal } = {}) {
    const token = tokenRef.current;
    if (!token) {
      return;
    }

    try {
      setWorkOrdersLoading(true);
      setWorkOrdersError('');

      const response = await fetch(`${API_BASE_URL}/work-orders/my-business`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
        signal,
      });

      const payload = await safeJson(response);

      if (!response.ok) {
        setWorkOrdersError(
          getErrorMessage(
            response.status,
            payload,
            'İş emirleri yüklenirken bir hata oluştu. Lütfen daha sonra tekrar deneyin.'
          )
        );
        setWorkOrders([]);
        return;
      }

      if (!Array.isArray(payload)) {
        setWorkOrdersError('API yanıtı beklenen formatta değil.');
        setWorkOrders([]);
        return;
      }

      setWorkOrders(payload);
      setStatusSelections((prev) => {
        const next = { ...prev };
        for (const item of payload) {
          const currentStatus = (item?.status || '').toString().trim().toLowerCase();
          if (STATUS_LABELS[currentStatus]) {
            next[item.id] = currentStatus;
          } else {
            next[item.id] = 'received';
          }
        }
        return next;
      });
    } catch (error) {
      if (error?.name === 'AbortError') {
        return;
      }
      setWorkOrdersError('Backend bağlantısı kurulamadı. Lütfen sunucunun çalıştığından emin olun.');
      setWorkOrders([]);
    } finally {
      if (!signal || !signal.aborted) {
        setWorkOrdersLoading(false);
      }
    }
  }

  async function fetchBusinessServices(businessId, { signal } = {}) {
    if (!businessId) {
      setBusinessServices([]);
      setPriceEditMap({});
      return;
    }

    try {
      setServicesLoading(true);
      setServicesError('');

      const response = await fetch(`${API_BASE_URL}/businesses/${businessId}/services`, {
        signal,
      });

      const payload = await safeJson(response);

      if (!response.ok) {
        setServicesError(
          getErrorMessage(
            response.status,
            payload,
            'İşletme hizmetleri yüklenirken bir hata oluştu.'
          )
        );
        setBusinessServices([]);
        setPriceEditMap({});
        return;
      }

      if (!Array.isArray(payload)) {
        setServicesError('API yanıtı beklenen formatta değil.');
        setBusinessServices([]);
        setPriceEditMap({});
        return;
      }

      setBusinessServices(payload);
      const nextMap = {};
      payload.forEach((item) => {
        nextMap[item.service_id] = String(item.minimum_price);
      });
      setPriceEditMap(nextMap);
    } catch (error) {
      if (error?.name === 'AbortError') {
        return;
      }
      setServicesError('Backend bağlantısı kurulamadı. Lütfen sunucunun çalıştığından emin olun.');
      setBusinessServices([]);
      setPriceEditMap({});
    } finally {
      if (!signal || !signal.aborted) {
        setServicesLoading(false);
      }
    }
  }

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    tokenRef.current = token || '';

    if (!token) {
      setTokenMissing(true);
      setInitialLoading(false);
      return;
    }

    const controller = new AbortController();

    const fetchInitialData = async () => {
      try {
        setInitialLoading(true);
        setAuthErrorMessage('');

        const [meResponse, businessesResponse, customersResponse] = await Promise.all([
          fetch(`${API_BASE_URL}/auth/me`, {
            headers: {
              Authorization: `Bearer ${token}`,
            },
            signal: controller.signal,
          }),
          fetch(`${API_BASE_URL}/businesses`, {
            signal: controller.signal,
          }),
          fetch(`${API_BASE_URL}/work-orders/my-business/customers`, {
            headers: {
              Authorization: `Bearer ${token}`,
            },
            signal: controller.signal,
          }),
        ]);

        const [mePayload, businessesPayload, customersPayload] = await Promise.all([
          safeJson(meResponse),
          safeJson(businessesResponse),
          safeJson(customersResponse),
        ]);

        if (!meResponse.ok) {
          setAuthErrorMessage(
            getErrorMessage(
              meResponse.status,
              mePayload,
              'Kullanıcı bilgisi alınırken bir hata oluştu.'
            )
          );
          return;
        }

        const role = (mePayload?.role || '').toString().trim().toLowerCase();
        if (role !== 'business_owner') {
          setIsBusinessOwner(false);
          return;
        }

        if (!businessesResponse.ok) {
          setAuthErrorMessage(
            getErrorMessage(
              businessesResponse.status,
              businessesPayload,
              'İşletmeler yüklenirken bir hata oluştu.'
            )
          );
          return;
        }

        if (!Array.isArray(businessesPayload)) {
          setAuthErrorMessage('İşletmeler için API yanıtı beklenen formatta değil.');
          return;
        }

        if (!customersResponse.ok) {
          setAuthErrorMessage(
            getErrorMessage(
              customersResponse.status,
              customersPayload,
              'Müşteri seçenekleri yüklenirken bir hata oluştu.'
            )
          );
          return;
        }

        if (!Array.isArray(customersPayload)) {
          setAuthErrorMessage('Müşteri seçenekleri için API yanıtı beklenen formatta değil.');
          return;
        }

        const ownerId = mePayload?.id;
        const filteredBusinesses = businessesPayload.filter(
          (business) => business?.owner_id === ownerId
        );

        setOwnerBusinesses(filteredBusinesses);
        setCustomers(customersPayload);
        setCustomersLoading(false);

        if (filteredBusinesses.length === 1) {
          setSelectedBusinessId(String(filteredBusinesses[0].id));
        }

        await fetchWorkOrders({ signal: controller.signal });

        const catalogResponse = await fetch(`${API_BASE_URL}/services`, {
          signal: controller.signal,
        });
        const catalogPayload = await safeJson(catalogResponse);
        if (catalogResponse.ok && Array.isArray(catalogPayload)) {
          setServiceCatalog(catalogPayload);
        }
      } catch (error) {
        if (error?.name === 'AbortError') {
          return;
        }
        setAuthErrorMessage('Backend bağlantısı kurulamadı. Lütfen sunucunun çalıştığından emin olun.');
      } finally {
        if (!controller.signal.aborted) {
          setInitialLoading(false);
          setCustomersLoading(false);
        }
      }
    };

    setCustomersLoading(true);
    fetchInitialData();

    return () => {
      controller.abort();
    };
  }, []);

  useEffect(() => {
    const token = tokenRef.current;

    if (!token || !selectedCustomerId) {
      setVehicles([]);
      setSelectedVehicleId('');
      setVehiclesLoading(false);
      setVehiclesError('');
      return;
    }

    const requestId = ++vehicleRequestIdRef.current;
    const controller = new AbortController();

    const loadVehicles = async () => {
      try {
        setVehiclesLoading(true);
        setVehiclesError('');
        setVehicles([]);
        setSelectedVehicleId('');

        const response = await fetch(
          `${API_BASE_URL}/work-orders/my-business/customers/${selectedCustomerId}/vehicles`,
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
            signal: controller.signal,
          }
        );

        const payload = await safeJson(response);

        if (requestId !== vehicleRequestIdRef.current) {
          return;
        }

        if (!response.ok) {
          setVehiclesError(
            getErrorMessage(
              response.status,
              payload,
              'Araç seçenekleri yüklenirken bir hata oluştu.'
            )
          );
          return;
        }

        if (!Array.isArray(payload)) {
          setVehiclesError('Araç seçenekleri için API yanıtı beklenen formatta değil.');
          return;
        }

        setVehicles(payload);
      } catch (error) {
        if (error?.name === 'AbortError') {
          return;
        }
        if (requestId !== vehicleRequestIdRef.current) {
          return;
        }
        setVehiclesError('Backend bağlantısı kurulamadı. Lütfen sunucunun çalıştığından emin olun.');
      } finally {
        if (!controller.signal.aborted && requestId === vehicleRequestIdRef.current) {
          setVehiclesLoading(false);
        }
      }
    };

    loadVehicles();

    return () => {
      controller.abort();
    };
  }, [selectedCustomerId]);

  useEffect(() => {
    setSelectedServiceId('');
    setNewMinimumPrice('');
    setServicesError('');
    setServicesSuccess('');

    if (!selectedBusinessId) {
      setBusinessServices([]);
      setPriceEditMap({});
      return;
    }

    const controller = new AbortController();

    fetchBusinessServices(selectedBusinessId, { signal: controller.signal });

    return () => {
      controller.abort();
    };
  }, [selectedBusinessId]);

  const isFormDisabled =
    !hasOwnerBusinesses ||
    !hasCustomers ||
    !selectedCustomerId ||
    !selectedVehicleId ||
    formSubmitting ||
    vehiclesLoading ||
    !hasVehicles;

  const ownerBusinessSelection = useMemo(() => {
    if (!hasOwnerBusinesses) {
      return null;
    }

    if (ownerBusinesses.length === 1) {
      return (
        <p className="owner-helper-text">
          İşletme: {normalizeText(ownerBusinesses[0].name)}
        </p>
      );
    }

    return (
      <label>
        İşletme
        <select
          value={selectedBusinessId}
          onChange={(event) => setSelectedBusinessId(event.target.value)}
        >
          <option value="">İşletme seçin</option>
          {ownerBusinesses.map((business) => (
            <option key={business.id} value={business.id}>
              {normalizeText(business.name)}
            </option>
          ))}
        </select>
      </label>
    );
  }, [hasOwnerBusinesses, ownerBusinesses, selectedBusinessId]);

  const activeServiceIds = useMemo(
    () => new Set(businessServices.map((item) => item.service_id)),
    [businessServices]
  );

  const availableServices = useMemo(
    () => serviceCatalog.filter((svc) => !activeServiceIds.has(svc.id)),
    [serviceCatalog, activeServiceIds]
  );

  async function handleCreateWorkOrder(event) {
    event.preventDefault();

    setFormError('');
    setFormSuccess('');
    setStatusError('');
    setStatusSuccess('');

    const token = tokenRef.current;
    if (!token) {
      setFormError('İşletme sahibi panelini görüntülemek için giriş yapmalısınız.');
      return;
    }

    const trimmedServiceType = serviceType.trim();
    const customerId = Number(selectedCustomerId);
    const vehicleId = Number(selectedVehicleId);
    const businessId = Number(selectedBusinessId);
    const numericPrice = Number(price);

    if (!hasOwnerBusinesses) {
      setFormError('Hesabınıza bağlı bir işletme bulunmuyor.');
      return;
    }

    if (!customerId || Number.isNaN(customerId) || customerId <= 0) {
      setFormError('Lütfen geçerli bir müşteri seçin.');
      return;
    }

    if (!vehicleId || Number.isNaN(vehicleId) || vehicleId <= 0) {
      setFormError('Lütfen geçerli bir araç seçin.');
      return;
    }

    if (!businessId || Number.isNaN(businessId) || businessId <= 0) {
      setFormError('Lütfen geçerli bir işletme seçin.');
      return;
    }

    if (!trimmedServiceType) {
      setFormError('Hizmet türü boş bırakılamaz.');
      return;
    }

    if (Number.isNaN(numericPrice) || numericPrice <= 0) {
      setFormError('Fiyat sıfırdan büyük olmalıdır.');
      return;
    }

    if (!hasVehicles) {
      setFormError('Bu müşteriye kayıtlı araç bulunmuyor.');
      return;
    }

    try {
      setFormSubmitting(true);

      const response = await fetch(`${API_BASE_URL}/work-orders`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          customer_id: customerId,
          vehicle_id: vehicleId,
          business_id: businessId,
          service_type: trimmedServiceType,
          price: numericPrice,
        }),
      });

      const payload = await safeJson(response);

      if (!response.ok) {
        setFormError(
          getErrorMessage(
            response.status,
            payload,
            'İş emri oluşturulurken bir hata oluştu.'
          )
        );
        return;
      }

      setFormSuccess('İş emri başarıyla oluşturuldu.');
      setServiceType('');
      setPrice('');
      await fetchWorkOrders();
    } catch (error) {
      if (error?.name === 'AbortError') {
        return;
      }
      setFormError('Backend bağlantısı kurulamadı. Lütfen sunucunun çalıştığından emin olun.');
    } finally {
      setFormSubmitting(false);
    }
  }

  async function handleUpdateStatus(workOrderId) {
    setStatusError('');
    setStatusSuccess('');
    setFormSuccess('');

    const token = tokenRef.current;
    if (!token) {
      setStatusError('İşletme sahibi panelini görüntülemek için giriş yapmalısınız.');
      return;
    }

    const nextStatus = statusSelections[workOrderId];
    if (!STATUS_LABELS[nextStatus]) {
      setStatusError('Geçerli bir durum seçin.');
      return;
    }

    const currentWorkOrder = workOrders.find((item) => item.id === workOrderId);
    const currentStatus = (currentWorkOrder?.status || '').toString().trim().toLowerCase();
    const normalizedNextStatus = (nextStatus || '').toString().trim().toLowerCase();

    if (currentStatus && currentStatus === normalizedNextStatus) {
      setStatusSuccess('');
      setStatusError('Yeni durum, mevcut durumdan farklı olmalıdır.');
      return;
    }

    try {
      setStatusUpdatingMap((prev) => ({
        ...prev,
        [workOrderId]: true,
      }));

      const response = await fetch(`${API_BASE_URL}/work-orders/${workOrderId}/status`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          status: nextStatus,
        }),
      });

      const payload = await safeJson(response);

      if (!response.ok) {
        setStatusError(
          getErrorMessage(
            response.status,
            payload,
            'İş emri durumu güncellenirken bir hata oluştu.'
          )
        );
        return;
      }

      setStatusSuccess('İş emri durumu başarıyla güncellendi.');
      await fetchWorkOrders();
    } catch (error) {
      if (error?.name === 'AbortError') {
        return;
      }
      setStatusError('Backend bağlantısı kurulamadı. Lütfen sunucunun çalıştığından emin olun.');
    } finally {
      setStatusUpdatingMap((prev) => ({
        ...prev,
        [workOrderId]: false,
      }));
    }
  }

  async function handleAddService(event) {
    event.preventDefault();

    setServicesError('');
    setServicesSuccess('');

    const token = tokenRef.current;
    if (!token) {
      setServicesError('İşlem yapmak için giriş yapmalısınız.');
      return;
    }

    const businessId = Number(selectedBusinessId);
    if (!businessId) {
      setServicesError('Lütfen bir işletme seçin.');
      return;
    }

    const serviceId = Number(selectedServiceId);
    if (!serviceId) {
      setServicesError('Lütfen bir hizmet seçin.');
      return;
    }

    const numericPrice = Number(newMinimumPrice);
    if (Number.isNaN(numericPrice) || numericPrice <= 0) {
      setServicesError('Minimum fiyat sıfırdan büyük olmalıdır.');
      return;
    }

    try {
      setServiceSubmitting(true);

      const response = await fetch(`${API_BASE_URL}/businesses/${businessId}/services`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          service_id: serviceId,
          minimum_price: numericPrice,
        }),
      });

      const payload = await safeJson(response);

      if (!response.ok) {
        if (response.status === 409) {
          setServicesError('Bu hizmet işletmeye zaten eklenmiş.');
        } else if (response.status === 422) {
          setServicesError('Lütfen hizmet ve minimum fiyat bilgilerini kontrol edin.');
        } else {
          setServicesError(
            getErrorMessage(
              response.status,
              payload,
              'Hizmet eklenirken bir hata oluştu.'
            )
          );
        }
        return;
      }

      setServicesSuccess('Hizmet başarıyla eklendi.');
      setSelectedServiceId('');
      setNewMinimumPrice('');
      await fetchBusinessServices(businessId);
    } catch (error) {
      if (error?.name === 'AbortError') {
        return;
      }
      setServicesError('Backend bağlantısı kurulamadı. Lütfen sunucunun çalıştığından emin olun.');
    } finally {
      setServiceSubmitting(false);
    }
  }

  async function handleUpdateServicePrice(serviceId) {
    setServicesError('');
    setServicesSuccess('');

    const token = tokenRef.current;
    if (!token) {
      setServicesError('İşlem yapmak için giriş yapmalısınız.');
      return;
    }

    const businessId = Number(selectedBusinessId);
    if (!businessId) {
      return;
    }

    const rawPrice = priceEditMap[serviceId];
    const numericPrice = Number(rawPrice);
    if (Number.isNaN(numericPrice) || numericPrice <= 0) {
      setServicesError('Yeni fiyat sıfırdan büyük olmalıdır.');
      return;
    }

    const targetService = businessServices.find((item) => item.service_id === serviceId);
    const currentMinimumPrice = Number(targetService?.minimum_price);

    if (!Number.isNaN(currentMinimumPrice)) {
      const nextPriceInCents = Math.round(numericPrice * 100);
      const currentPriceInCents = Math.round(currentMinimumPrice * 100);

      if (nextPriceInCents === currentPriceInCents) {
        setServicesSuccess('');
        setServicesError('Yeni minimum fiyat, mevcut fiyattan farklı olmalıdır.');
        return;
      }
    }

    try {
      setUpdatingServiceId(serviceId);

      const response = await fetch(
        `${API_BASE_URL}/businesses/${businessId}/services/${serviceId}`,
        {
          method: 'PATCH',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({ minimum_price: numericPrice }),
        }
      );

      const payload = await safeJson(response);

      if (!response.ok) {
        if (response.status === 422) {
          setServicesError('Lütfen hizmet ve minimum fiyat bilgilerini kontrol edin.');
        } else {
          setServicesError(
            getErrorMessage(
              response.status,
              payload,
              'Fiyat güncellenirken bir hata oluştu.'
            )
          );
        }
        return;
      }

      setServicesSuccess('Minimum başlangıç fiyatı güncellendi.');
      await fetchBusinessServices(businessId);
    } catch (error) {
      if (error?.name === 'AbortError') {
        return;
      }
      setServicesError('Backend bağlantısı kurulamadı. Lütfen sunucunun çalıştığından emin olun.');
    } finally {
      setUpdatingServiceId(null);
    }
  }

  async function handleDeactivateService(serviceId) {
    setServicesError('');
    setServicesSuccess('');

    const token = tokenRef.current;
    if (!token) {
      setServicesError('İşlem yapmak için giriş yapmalısınız.');
      return;
    }

    const businessId = Number(selectedBusinessId);
    if (!businessId) {
      return;
    }

    try {
      setDeletingServiceId(serviceId);

      const response = await fetch(
        `${API_BASE_URL}/businesses/${businessId}/services/${serviceId}`,
        {
          method: 'DELETE',
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      const payload = await safeJson(response);

      if (!response.ok) {
        setServicesError(
          getErrorMessage(
            response.status,
            payload,
            'Hizmet pasifleştirilirken bir hata oluştu.'
          )
        );
        return;
      }

      setServicesSuccess('Hizmet pasifleştirildi.');
      await fetchBusinessServices(businessId);
    } catch (error) {
      if (error?.name === 'AbortError') {
        return;
      }
      setServicesError('Backend bağlantısı kurulamadı. Lütfen sunucunun çalıştığından emin olun.');
    } finally {
      setDeletingServiceId(null);
    }
  }

  if (tokenMissing) {
    return (
      <section className="owner-panel-page owner-workorders-page">
        <div className="owner-panel-header">
          <h2>İşletme Sahibi Paneli</h2>
          <button onClick={onBack}>İşletmelere Geri Dön</button>
        </div>
        <p className="owner-inline-status">İşletme sahibi panelini görüntülemek için giriş yapmalısınız.</p>
      </section>
    );
  }

  if (initialLoading) {
    return (
      <section className="owner-panel-page owner-workorders-page">
        <div className="owner-panel-header">
          <h2>İşletme Sahibi Paneli</h2>
          <button onClick={onBack}>İşletmelere Geri Dön</button>
        </div>
        <p className="owner-inline-status">Panel verileri yükleniyor...</p>
      </section>
    );
  }

  if (authErrorMessage) {
    return (
      <section className="owner-panel-page owner-workorders-page">
        <div className="owner-panel-header">
          <h2>İşletme Sahibi Paneli</h2>
          <button onClick={onBack}>İşletmelere Geri Dön</button>
        </div>
        <p className="ui-error owner-inline-status">{authErrorMessage}</p>
      </section>
    );
  }

  if (!isBusinessOwner) {
    return (
      <section className="owner-panel-page owner-workorders-page">
        <div className="owner-panel-header">
          <h2>İşletme Sahibi Paneli</h2>
          <button onClick={onBack}>İşletmelere Geri Dön</button>
        </div>
        <p className="owner-inline-status">Bu alan yalnızca işletme sahibi hesapları tarafından kullanılabilir.</p>
      </section>
    );
  }

  return (
    <section className="owner-panel-page owner-workorders-page">
      <div className="owner-panel-header">
        <div className="owner-panel-header-content">
          <h2>İşletme Sahibi Paneli</h2>
          <p>İş emri oluşturma, durum güncelleme ve hizmet fiyat yönetimini tek ekrandan yapabilirsiniz.</p>
        </div>
        <button onClick={onBack}>İşletmelere Geri Dön</button>
      </div>

      <div className="owner-panel-section owner-section">
        <h3 className="owner-section-title">Yeni İş Emri Oluştur</h3>

        {!hasOwnerBusinesses && (
          <p className="ui-error owner-inline-status">Hesabınıza bağlı bir işletme bulunmuyor.</p>
        )}

        {customersLoading && <p className="owner-inline-status">Müşteri seçenekleri yükleniyor...</p>}
        {!customersLoading && hasOwnerBusinesses && !hasCustomers && (
          <p className="owner-inline-status">İş emri oluşturulabilecek aktif müşteri bulunmuyor.</p>
        )}

        <form className="owner-form owner-form-grid" onSubmit={handleCreateWorkOrder}>
          <label>
            Müşteri
            <select
              value={selectedCustomerId}
              onChange={(event) => {
                setSelectedCustomerId(event.target.value);
                setFormError('');
                setFormSuccess('');
              }}
              disabled={!hasOwnerBusinesses || !hasCustomers || formSubmitting}
            >
              <option value="">Müşteri seçin</option>
              {customers.map((customer) => (
                <option key={customer.id} value={customer.id}>
                  {parseCustomerLabel(customer)}
                </option>
              ))}
            </select>
          </label>

          <label>
            Araç
            <select
              value={selectedVehicleId}
              onChange={(event) => setSelectedVehicleId(event.target.value)}
              disabled={!selectedCustomerId || vehiclesLoading || !hasVehicles || formSubmitting}
            >
              <option value="">Araç seçin</option>
              {vehicles.map((vehicle) => (
                <option key={vehicle.id} value={vehicle.id}>
                  {parseVehicleLabel(vehicle)}
                </option>
              ))}
            </select>
          </label>

          {vehiclesLoading && <p className="owner-inline-status">Araç seçenekleri yükleniyor...</p>}
          {vehiclesError && <p className="ui-error owner-inline-status">{vehiclesError}</p>}
          {!vehiclesLoading && selectedCustomerId && !vehiclesError && !hasVehicles && (
            <p className="owner-inline-status">Bu müşteriye kayıtlı araç bulunmuyor.</p>
          )}

          {ownerBusinessSelection}

          <label>
            Hizmet Türü
            <input
              type="text"
              value={serviceType}
              onChange={(event) => setServiceType(event.target.value)}
              placeholder="Periyodik Bakım"
              disabled={!hasOwnerBusinesses || formSubmitting}
            />
          </label>

          <label>
            Fiyat
            <input
              type="number"
              min="0"
              step="0.01"
              value={price}
              onChange={(event) => setPrice(event.target.value)}
              disabled={!hasOwnerBusinesses || formSubmitting}
            />
          </label>

          {formError && <p className="ui-error owner-inline-status">{formError}</p>}
          {formSuccess && <p className="ui-success owner-inline-status">{formSuccess}</p>}

          <button type="submit" disabled={isFormDisabled}>
            {formSubmitting ? 'Oluşturuluyor...' : 'İş Emri Oluştur'}
          </button>
        </form>
      </div>

      <div className="owner-panel-section owner-section">
        <h3 className="owner-section-title">İş Emirleri</h3>

        {workOrdersLoading && <p className="owner-inline-status">İş emirleri yükleniyor...</p>}
        {workOrdersError && <p className="ui-error owner-inline-status">{workOrdersError}</p>}
        {statusError && <p className="ui-error owner-inline-status">{statusError}</p>}
        {statusSuccess && <p className="ui-success owner-inline-status">{statusSuccess}</p>}

        {!workOrdersLoading && !workOrdersError && !hasWorkOrders && (
          <p className="owner-inline-status">İşletmenize ait henüz bir iş emri bulunmuyor.</p>
        )}

        {!workOrdersLoading && !workOrdersError && hasWorkOrders && (
          <div className="owner-workorder-list">
            {workOrders.map((workOrder) => {
              const selectedStatus = statusSelections[workOrder.id] || 'received';
              const isUpdating = Boolean(statusUpdatingMap[workOrder.id]);

              return (
                <article key={workOrder.id} className="owner-workorder-card">
                  <h4>İş Emri #{normalizeText(workOrder.id)}</h4>
                  <p><strong>Müşteri:</strong> {normalizeText(workOrder.customer_name)}</p>
                  <p><strong>Müşteri E-posta:</strong> {normalizeText(workOrder.customer_email)}</p>
                  <p><strong>Araç Plakası:</strong> {normalizeText(workOrder.vehicle_plate)}</p>
                  <p>
                    <strong>Araç:</strong>{' '}
                    {`${normalizeText(workOrder.vehicle_make)} ${normalizeText(workOrder.vehicle_model)}`}
                  </p>
                  <p><strong>İşletme:</strong> {normalizeText(workOrder.business_name)}</p>
                  <p><strong>Hizmet Türü:</strong> {normalizeText(workOrder.service_type)}</p>
                  <p><strong>Fiyat:</strong> {formatCurrency(workOrder.price)}</p>
                  <p><strong>Durum:</strong> {getStatusLabel(workOrder.status)}</p>
                  <p><strong>Oluşturulma Tarihi:</strong> {formatDate(workOrder.created_at)}</p>

                  <div className="owner-status-row owner-action-row">
                    <select
                      value={selectedStatus}
                      onChange={(event) => {
                        const value = event.target.value;
                        setStatusSelections((prev) => ({
                          ...prev,
                          [workOrder.id]: value,
                        }));
                      }}
                      disabled={isUpdating}
                    >
                      {STATUS_OPTIONS.map((statusOption) => (
                        <option key={statusOption.value} value={statusOption.value}>
                          {statusOption.label}
                        </option>
                      ))}
                    </select>

                    <button
                      type="button"
                      onClick={() => handleUpdateStatus(workOrder.id)}
                      disabled={isUpdating}
                    >
                      {isUpdating ? 'Güncelleniyor...' : 'Durumu Güncelle'}
                    </button>
                  </div>
                </article>
              );
            })}
          </div>
        )}
      </div>

      <div className="owner-panel-section owner-section service-management-section">
        <h3 className="owner-section-title">Hizmet ve Başlangıç Fiyatları</h3>
        <p className="owner-helper-text owner-inline-status">
          İşletmenizin sunduğu hizmetleri ve araç durumuna göre artabilecek minimum başlangıç fiyatlarını yönetin.
        </p>

        {!hasOwnerBusinesses && (
          <p className="ui-error owner-inline-status">Hesabınıza bağlı bir işletme bulunmuyor.</p>
        )}

        {hasOwnerBusinesses && !selectedBusinessId && (
          <p className="owner-helper-text owner-inline-status">Hizmetleri yönetmek için yukarıdan bir işletme seçin.</p>
        )}

        {hasOwnerBusinesses && selectedBusinessId && (
          <>
            {servicesLoading && <p className="owner-inline-status">Hizmet bilgileri yükleniyor...</p>}

            {servicesError && (
              <p className="ui-error service-status-message owner-inline-status">{servicesError}</p>
            )}
            {servicesSuccess && (
              <p className="ui-success service-status-message owner-inline-status">{servicesSuccess}</p>
            )}

            {!servicesLoading && (
              <>
                <form className="service-add-form" onSubmit={handleAddService}>
                  <label>
                    Hizmet
                    {availableServices.length === 0 ? (
                      <p className="owner-helper-text">
                        Tüm aktif hizmetler bu işletmeye eklenmiş.
                      </p>
                    ) : (
                      <select
                        value={selectedServiceId}
                        onChange={(event) => {
                          setSelectedServiceId(event.target.value);
                          setServicesError('');
                          setServicesSuccess('');
                        }}
                        disabled={serviceSubmitting}
                      >
                        <option value="">Hizmet Seçin</option>
                        {availableServices.map((svc) => (
                          <option key={svc.id} value={svc.id}>
                            {svc.name}
                          </option>
                        ))}
                      </select>
                    )}
                  </label>

                  <label>
                    Minimum Başlangıç Fiyatı (₺)
                    <input
                      type="number"
                      min="0.01"
                      step="0.01"
                      value={newMinimumPrice}
                      onChange={(event) => setNewMinimumPrice(event.target.value)}
                      placeholder="0.00"
                      disabled={serviceSubmitting || availableServices.length === 0}
                    />
                  </label>

                  <button
                    type="submit"
                    disabled={
                      serviceSubmitting ||
                      availableServices.length === 0 ||
                      !selectedServiceId ||
                      !newMinimumPrice
                    }
                  >
                    {serviceSubmitting ? 'Ekleniyor...' : 'Hizmet Ekle'}
                  </button>
                </form>

                {businessServices.length === 0 && (
                  <p className="owner-helper-text owner-inline-status">
                    Bu işletmeye henüz hizmet eklenmemiş.
                  </p>
                )}

                {businessServices.length > 0 && (
                  <div className="service-management-list">
                    {businessServices.map((item) => {
                      const isUpdating = updatingServiceId === item.service_id;
                      const isDeleting = deletingServiceId === item.service_id;
                      const isDisabled = isUpdating || isDeleting;

                      return (
                        <article key={item.service_id} className="service-management-card">
                          <h4>{normalizeText(item.service_name)}</h4>
                          {item.service_description && (
                            <p className="owner-helper-text">{item.service_description}</p>
                          )}
                          <p>
                            <strong>Güncel minimum fiyat:</strong>{' '}
                            {formatCurrency(item.minimum_price)}
                          </p>
                          <p className="owner-helper-text">
                            Bu tutar minimum başlangıç fiyatıdır. Araç modeli, arıza ve parça
                            ihtiyacına göre gerçek ücret artabilir.
                          </p>

                          <div className="service-price-actions owner-action-row">
                            <input
                              type="number"
                              min="0.01"
                              step="0.01"
                              value={priceEditMap[item.service_id] ?? ''}
                              onChange={(event) => {
                                const val = event.target.value;
                                setPriceEditMap((prev) => ({
                                  ...prev,
                                  [item.service_id]: val,
                                }));
                              }}
                              disabled={isDisabled}
                              aria-label={`${item.service_name} yeni fiyatı`}
                            />

                            <button
                              type="button"
                              onClick={() => handleUpdateServicePrice(item.service_id)}
                              disabled={isDisabled}
                            >
                              {isUpdating ? 'Güncelleniyor...' : 'Fiyatı Güncelle'}
                            </button>

                            <button
                              type="button"
                              onClick={() => handleDeactivateService(item.service_id)}
                              disabled={isDisabled}
                            >
                              {isDeleting ? 'Pasifleştiriliyor...' : 'Hizmeti Pasifleştir'}
                            </button>
                          </div>
                        </article>
                      );
                    })}
                  </div>
                )}
              </>
            )}
          </>
        )}
      </div>
    </section>
  );
}

export default OwnerWorkOrdersPanel;
