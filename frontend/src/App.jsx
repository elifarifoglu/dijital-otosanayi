import React, { useState } from 'react';
import BusinessList from './components/BusinessList.jsx';
import BusinessDetail from './components/BusinessDetail.jsx';

function App() {
  const [selectedBusinessId, setSelectedBusinessId] = useState(null);

  return (
    <div style={{ padding: '2rem', fontFamily: 'Arial, sans-serif' }}>
      <h1>Dijital Otosanayi</h1>
      {selectedBusinessId ? (
        <BusinessDetail businessId={selectedBusinessId} onBack={() => setSelectedBusinessId(null)} />
      ) : (
        <BusinessList onSelectBusiness={setSelectedBusinessId} />
      )}
    </div>
  );
}

export default App;