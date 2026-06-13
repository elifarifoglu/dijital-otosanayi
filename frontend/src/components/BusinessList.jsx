import React, { useState, useEffect } from 'react';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

function BusinessList({ onSelectBusiness }) {
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
    return (
      <section className="business-list-page">
        <header className="business-list-header">
          <h2>İşletmeler</h2>
          <p>Bölgenizdeki işletmeleri inceleyip detaylarını görüntüleyin.</p>
        </header>
        <p className="business-list-state">İşletmeler yükleniyor...</p>
      </section>
    );
  }

  if (error) {
    return (
      <section className="business-list-page">
        <header className="business-list-header">
          <h2>İşletmeler</h2>
          <p>Bölgenizdeki işletmeleri inceleyip detaylarını görüntüleyin.</p>
        </header>
        <p className="ui-error business-list-state">{error}</p>
      </section>
    );
  }

  if (businesses.length === 0) {
    return (
      <section className="business-list-page">
        <header className="business-list-header">
          <h2>İşletmeler</h2>
          <p>Bölgenizdeki işletmeleri inceleyip detaylarını görüntüleyin.</p>
        </header>
        <p className="business-list-state">Henüz kayıtlı işletme bulunamadı.</p>
      </section>
    );
  }

  return (
    <section className="business-list-page">
      <header className="business-list-header">
        <h2>İşletmeler</h2>
        <p>Bölgenizdeki işletmeleri inceleyip detaylarını görüntüleyin.</p>
      </header>

      <ul className="business-list-grid" aria-label="İşletme listesi">
        {businesses.map((business) => (
          <li key={business.id} className="business-list-card">
            <h3>{business.name}</h3>
            <p className="business-list-description">{business.description || 'Açıklama belirtilmemiş.'}</p>
            <p><strong>Adres:</strong> {business.address || 'Belirtilmemiş'}</p>
            <p><strong>Telefon:</strong> {business.phone || 'Belirtilmemiş'}</p>
            <p>
              <strong>Ortalama Puan:</strong>{' '}
              {business.average_rating === null || business.average_rating === undefined
                ? 'Henüz puan yok'
                : Number(business.average_rating).toFixed(1)}
            </p>
            <button
              type="button"
              className="business-list-action"
              onClick={() => onSelectBusiness(business.id)}
            >
              Detayları Gör
            </button>
          </li>
        ))}
      </ul>
    </section>
  );
}

export default BusinessList;