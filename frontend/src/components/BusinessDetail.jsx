import React, { useState, useEffect } from 'react';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

function BusinessDetail({ businessId, onBack }) {
  const [business, setBusiness] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchBusinessDetail();
  }, [businessId]);

  const fetchBusinessDetail = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch(`${API_BASE_URL}/businesses/${businessId}`);

      if (response.status === 404) {
        setError('İşletme bulunamadı.');
        setBusiness(null);
        return;
      }

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      setBusiness(data);
    } catch (err) {
      if (err.message.includes('fetch')) {
        setError('Backend bağlantısı kurulamadı. Lütfen sunucunun çalıştığından emin olun.');
      } else {
        setError('Hata: ' + err.message);
      }
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div>Yükleniyor...</div>;
  }

  if (error) {
    return (
      <div>
        <div style={{ color: 'red' }}>{error}</div>
        <button onClick={onBack}>Listeye Geri Dön</button>
      </div>
    );
  }

  if (!business) {
    return (
      <div>
        <div>Veri yüklenemedi.</div>
        <button onClick={onBack}>Listeye Geri Dön</button>
      </div>
    );
  }

  return (
    <div style={{ padding: '1rem', maxWidth: '600px' }}>
      <h2>{business.name}</h2>
      <div style={{ backgroundColor: '#f9f9f9', padding: '1rem', borderRadius: '8px', marginBottom: '1rem' }}>
        <p><strong>ID:</strong> {business.id}</p>
        <p><strong>Adres:</strong> {business.address || 'Belirtilmemiş'}</p>
        <p><strong>Telefon:</strong> {business.phone || 'Belirtilmemiş'}</p>
        <p><strong>Açıklama:</strong> {business.description || 'Belirtilmemiş'}</p>
        <p><strong>Sahibi ID:</strong> {business.owner_id || 'Belirtilmemiş'}</p>
        {business.created_at && (
          <p><strong>Oluşturulma Tarihi:</strong> {new Date(business.created_at).toLocaleDateString('tr-TR')}</p>
        )}
      </div>
      <button onClick={onBack}>Listeye Geri Dön</button>
    </div>
  );
}

export default BusinessDetail;