import React, { useState } from 'react';
import BusinessList from './components/BusinessList.jsx';
import BusinessDetail from './components/BusinessDetail.jsx';
import CustomerWorkOrders from './components/CustomerWorkOrders.jsx';
import OwnerWorkOrdersPanel from './components/OwnerWorkOrdersPanel.jsx';

function App() {
  const [selectedBusinessId, setSelectedBusinessId] = useState(null);
  const [activeScreen, setActiveScreen] = useState('business-list');

  return (
    <div style={{ padding: '2rem', fontFamily: 'Arial, sans-serif' }}>
      <h1>Dijital Otosanayi</h1>
      {selectedBusinessId ? (
        <BusinessDetail businessId={selectedBusinessId} onBack={() => setSelectedBusinessId(null)} />
      ) : activeScreen === 'customer-workorders' ? (
        <CustomerWorkOrders onBack={() => setActiveScreen('business-list')} />
      ) : activeScreen === 'owner-workorders' ? (
        <OwnerWorkOrdersPanel onBack={() => setActiveScreen('business-list')} />
      ) : (
        <>
          <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap', marginBottom: '1rem' }}>
            <button
              onClick={() => {
                setSelectedBusinessId(null);
                setActiveScreen('customer-workorders');
              }}
            >
              İş Emirlerim
            </button>
            <button
              onClick={() => {
                setSelectedBusinessId(null);
                setActiveScreen('owner-workorders');
              }}
            >
              İşletme Sahibi Paneli
            </button>
          </div>
          <BusinessList onSelectBusiness={setSelectedBusinessId} />
        </>
      )}
    </div>
  );
}

export default App;