import React, { useState } from 'react';
import BusinessList from './components/BusinessList.jsx';
import BusinessDetail from './components/BusinessDetail.jsx';
import CustomerWorkOrders from './components/CustomerWorkOrders.jsx';

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
      ) : (
        <>
          <button
            onClick={() => {
              setSelectedBusinessId(null);
              setActiveScreen('customer-workorders');
            }}
            style={{ marginBottom: '1rem' }}
          >
            İş Emirlerim
          </button>
          <BusinessList onSelectBusiness={setSelectedBusinessId} />
        </>
      )}
    </div>
  );
}

export default App;