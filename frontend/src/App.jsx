import React, { useState, useEffect } from 'react';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

function App() {
  const [backendMessage, setBackendMessage] = useState('Yükleniyor...');

  useEffect(() => {
    fetch(`${API_BASE_URL}/`)
      .then(response => response.json())
      .then(data => setBackendMessage(data.message))
      .catch(error => setBackendMessage('Hata: ' + error.message));
  }, []);

  return (
    <div>
      <h1>Dijital Otosanayi</h1>
      <p>Frontend iskeleti başarıyla çalışıyor.</p>
      <p>Backend mesajı: {backendMessage}</p>
    </div>
  );
}

export default App;