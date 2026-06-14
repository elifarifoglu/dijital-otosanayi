import React, { useState } from 'react';
import BusinessList from './components/BusinessList.jsx';
import BusinessDetail from './components/BusinessDetail.jsx';
import CustomerWorkOrders from './components/CustomerWorkOrders.jsx';
import OwnerWorkOrdersPanel from './components/OwnerWorkOrdersPanel.jsx';
import LoginPanel from './components/LoginPanel.jsx';

function App() {
  const [selectedBusinessId, setSelectedBusinessId] = useState(null);
  const [activeScreen, setActiveScreen] = useState('business-list');
  const [isAuthenticated, setIsAuthenticated] = useState(Boolean(localStorage.getItem('access_token')));

  const handleLoginSuccess = (targetScreen = 'business-list') => {
    setIsAuthenticated(true);
    setSelectedBusinessId(null);
    setActiveScreen(targetScreen);
  };

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    setIsAuthenticated(false);
    setSelectedBusinessId(null);
    setActiveScreen('business-list');
  };

  if (!isAuthenticated) {
    return <LoginPanel onLoginSuccess={handleLoginSuccess} />;
  }

  return (
    <div className="app-shell">
      <header className="app-header">
        <div className="app-brand" aria-label="Dijital Otosanayi marka alanı">
          <span className="app-brand-title">Dijital Otosanayi</span>
          <span className="app-brand-tagline">Dijital Servis Takip Platformu</span>
        </div>
        <nav className="app-nav">
          <button
            type="button"
            className={activeScreen === 'business-list' && !selectedBusinessId ? 'active' : ''}
            onClick={() => {
              setSelectedBusinessId(null);
              setActiveScreen('business-list');
            }}
          >
            İşletmeler
          </button>
          <button
            type="button"
            className={activeScreen === 'customer-workorders' ? 'active' : ''}
            onClick={() => {
              setSelectedBusinessId(null);
              setActiveScreen('customer-workorders');
            }}
          >
            İş Emirlerim
          </button>
          <button
            type="button"
            className={activeScreen === 'owner-workorders' ? 'active' : ''}
            onClick={() => {
              setSelectedBusinessId(null);
              setActiveScreen('owner-workorders');
            }}
          >
            İşletme Sahibi Paneli
          </button>
        </nav>
        <button type="button" className="logout-button" onClick={handleLogout}>
          Çıkış Yap
        </button>
      </header>

      <main className="app-content">
        {selectedBusinessId ? (
          <BusinessDetail businessId={selectedBusinessId} onBack={() => setSelectedBusinessId(null)} />
        ) : activeScreen === 'customer-workorders' ? (
          <CustomerWorkOrders onBack={() => setActiveScreen('business-list')} />
        ) : activeScreen === 'owner-workorders' ? (
          <OwnerWorkOrdersPanel onBack={() => setActiveScreen('business-list')} />
        ) : (
          <BusinessList onSelectBusiness={setSelectedBusinessId} />
        )}
      </main>
    </div>
  );
}

export default App;