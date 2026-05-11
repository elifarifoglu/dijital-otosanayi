import React, { useState, useEffect } from 'react';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

function BusinessList() {
  const [businesses, setBusinesses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchBusinesses();
  }, []);

  const fetchBusinesses = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch(`${API_BASE_URL}/businesses`);

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();

      // Response'un array olup olmadığını kontrol et
      if (!Array.isArray(data)) {
        throw new Error('Geçersiz API yanıtı: Array bekleniyordu');
      }

      setBusinesses(data);
    } catch (err) {
      // Özel hata mesajları
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
    return <div style={{ color: 'red' }}>{error}</div>;
  }

  if (businesses.length === 0) {
    return <div>Henüz kayıtlı işletme bulunamadı.</div>;
  }

  return (
    <div>
      <h2>İşletmeler</h2>
      <div style={{ display: 'grid', gap: '1rem', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))' }}>
        {businesses.map((business) => (
          <div key={business.id} style={{
            border: '1px solid #ddd',
            borderRadius: '8px',
            padding: '1rem',
            backgroundColor: '#f9f9f9'
          }}>
            <h3>{business.name}</h3>
            <p><strong>Adres:</strong> {business.address || 'Belirtilmemiş'}</p>
            <p><strong>Telefon:</strong> {business.phone || 'Belirtilmemiş'}</p>
            <p><strong>Açıklama:</strong> {business.description || 'Belirtilmemiş'}</p>
            <p><strong>ID:</strong> {business.id}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

export default BusinessList;