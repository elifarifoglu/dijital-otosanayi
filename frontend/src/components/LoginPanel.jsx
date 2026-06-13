import React, { useState } from 'react';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

const DEMO_CREDENTIALS = {
  customer: {
    email: 'demo.customer@example.com',
    password: 'Demo12345',
    targetScreen: 'customer-workorders',
  },
  owner: {
    email: 'demo.owner@example.com',
    password: 'Demo12345',
    targetScreen: 'owner-workorders',
  },
};

function LoginPanel({ onLoginSuccess }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');

  const submitLogin = async ({
    loginEmail,
    loginPassword,
    targetScreen = 'business-list',
  }) => {
    setErrorMessage('');
    setLoading(true);

    try {
      const response = await fetch(`${API_BASE_URL}/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: loginEmail,
          password: loginPassword,
        }),
      });

      const payload = await response.json().catch(() => ({}));

      if (!response.ok) {
        if (response.status === 401) {
          setErrorMessage('E-posta veya şifre hatalı. Lütfen bilgilerinizi kontrol edin.');
        } else if (response.status >= 500) {
          setErrorMessage('Sunucu hatası oluştu. Lütfen daha sonra tekrar deneyin.');
        } else {
          const detail = payload?.detail;
          if (typeof detail === 'string' && detail.trim()) {
            setErrorMessage(detail);
          } else {
            setErrorMessage('Giriş yapılırken bir hata oluştu. Lütfen tekrar deneyin.');
          }
        }
        return;
      }

      const accessToken = payload?.access_token;
      if (!accessToken || typeof accessToken !== 'string') {
        setErrorMessage('Giriş başarılı fakat token bilgisi alınamadı.');
        return;
      }

      localStorage.setItem('access_token', accessToken);
      onLoginSuccess(targetScreen);
    } catch (error) {
      setErrorMessage('Backend bağlantısı kurulamadı. Sunucunun çalıştığından emin olun.');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (event) => {
    event.preventDefault();

    const trimmedEmail = email.trim();
    if (!trimmedEmail || !password) {
      setErrorMessage('Lütfen e-posta ve şifre alanlarını doldurun.');
      return;
    }

    await submitLogin({
      loginEmail: trimmedEmail,
      loginPassword: password,
      targetScreen: 'business-list',
    });
  };

  const handleDemoLogin = async (demoType) => {
    const demo = DEMO_CREDENTIALS[demoType];
    if (!demo) {
      return;
    }

    setEmail(demo.email);
    setPassword(demo.password);

    await submitLogin({
      loginEmail: demo.email,
      loginPassword: demo.password,
      targetScreen: demo.targetScreen,
    });
  };

  return (
    <section className="login-page">
      <div className="login-card">
        <h1>Dijital Otosanayi</h1>
        <p className="login-subtitle">Demo ortamı için giriş yapın.</p>

        <form className="login-form" onSubmit={handleSubmit}>
          <label>
            E-posta
            <input
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              placeholder="ornek@email.com"
              autoComplete="username"
              disabled={loading}
            />
          </label>

          <label>
            Şifre
            <input
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              placeholder="********"
              autoComplete="current-password"
              disabled={loading}
            />
          </label>

          {errorMessage && <p className="ui-error">{errorMessage}</p>}

          <button type="submit" disabled={loading}>
            {loading ? 'Giriş yapılıyor...' : 'Giriş Yap'}
          </button>
        </form>

        <p className="login-demo-title">Hızlı demo girişi</p>
        <div className="login-demo-actions">
          <button
            type="button"
            onClick={() => handleDemoLogin('customer')}
            disabled={loading}
          >
            {loading ? 'İşleniyor...' : 'Müşteri Demo Girişi'}
          </button>
          <button
            type="button"
            onClick={() => handleDemoLogin('owner')}
            disabled={loading}
          >
            {loading ? 'İşleniyor...' : 'İşletme Sahibi Demo Girişi'}
          </button>
        </div>
      </div>
    </section>
  );
}

export default LoginPanel;
