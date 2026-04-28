import React, { useState, useEffect } from 'react';

function App() {
  const [backendMessage, setBackendMessage] = useState('Yükleniyor...');

  useEffect(() => {
    fetch('http://localhost:8000/')
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