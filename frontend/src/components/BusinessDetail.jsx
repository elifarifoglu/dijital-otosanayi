import React, { useState, useEffect } from 'react';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

function BusinessDetail({ businessId, onBack }) {
  const [business, setBusiness] = useState(null);
  const [businessLoading, setBusinessLoading] = useState(true);
  const [businessError, setBusinessError] = useState(null);

  const [reviews, setReviews] = useState([]);
  const [reviewsLoading, setReviewsLoading] = useState(true);
  const [reviewsError, setReviewsError] = useState(null);

  const [reviewableWorkorders, setReviewableWorkorders] = useState([]);
  const [reviewableLoading, setReviewableLoading] = useState(false);
  const [reviewableError, setReviewableError] = useState(null);
  const [tokenAvailable, setTokenAvailable] = useState(false);
  const [currentUserRole, setCurrentUserRole] = useState(null);
  const [authStatus, setAuthStatus] = useState('idle');

  const [selectedWorkorderId, setSelectedWorkorderId] = useState('');
  const [rating, setRating] = useState('5');
  const [comment, setComment] = useState('');
  const [submitLoading, setSubmitLoading] = useState(false);
  const [submitError, setSubmitError] = useState(null);
  const [submitSuccess, setSubmitSuccess] = useState(null);

  useEffect(() => {
    fetchBusinessDetail();
    fetchBusinessReviews();
  }, [businessId]);

  useEffect(() => {
    const token = localStorage.getItem('access_token');

    if (!token) {
      setTokenAvailable(false);
      setCurrentUserRole(null);
      setAuthStatus('no-token');
      setReviewableWorkorders([]);
      setSelectedWorkorderId('');
      setReviewableError(null);
      setReviewableLoading(false);
      return;
    }

    const controller = new AbortController();

    const runAuthAndReviewableFlow = async () => {
      try {
        setTokenAvailable(true);
        setAuthStatus('checking');
        setCurrentUserRole(null);
        setReviewableError(null);
        setReviewableWorkorders([]);
        setSelectedWorkorderId('');

        const meResponse = await fetch(`${API_BASE_URL}/auth/me`, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
          signal: controller.signal,
        });

        const mePayload = await meResponse.json().catch(() => null);

        if (meResponse.status === 401) {
          setAuthStatus('unauthorized');
          setTokenAvailable(false);
          return;
        }

        if (meResponse.status === 403) {
          setAuthStatus('unauthorized');
          return;
        }

        if (!meResponse.ok) {
          setAuthStatus('unauthorized');
          return;
        }

        const role = (mePayload?.role || '').toString().trim().toLowerCase();
        setCurrentUserRole(role || null);
        setAuthStatus('authenticated');

        if (role !== 'customer') {
          return;
        }

        await fetchReviewableWorkorders(token, controller.signal);
      } catch (err) {
        if (err?.name === 'AbortError') {
          return;
        }

        setAuthStatus('unauthorized');
        setReviewableError('Kullanıcı bilgisi alınamadı. Lütfen tekrar giriş yapın.');
      }
    };

    runAuthAndReviewableFlow();

    return () => {
      controller.abort();
    };
  }, [businessId]);

  const fetchBusinessDetail = async () => {
    try {
      setBusinessLoading(true);
      setBusinessError(null);

      const response = await fetch(`${API_BASE_URL}/businesses/${businessId}`);

      if (response.status === 404) {
        setBusinessError('İşletme bulunamadı.');
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
        setBusinessError('Backend bağlantısı kurulamadı. Lütfen sunucunun çalıştığından emin olun.');
      } else {
        setBusinessError('Hata: ' + err.message);
      }
    } finally {
      setBusinessLoading(false);
    }
  };

  const fetchBusinessReviews = async () => {
    try {
      setReviewsLoading(true);
      setReviewsError(null);

      const response = await fetch(`${API_BASE_URL}/businesses/${businessId}/reviews`);

      if (response.status === 404) {
        setReviewsError('İşletme bulunamadı.');
        setReviews([]);
        return;
      }

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      if (!Array.isArray(data)) {
        throw new Error('Geçersiz API yanıtı: Array bekleniyordu');
      }

      setReviews(data);
    } catch (err) {
      if (err.message.includes('fetch')) {
        setReviewsError('Yorumlar yüklenemedi. Backend bağlantısı kurulamadı.');
      } else {
        setReviewsError('Yorumlar yüklenemedi: ' + err.message);
      }
    } finally {
      setReviewsLoading(false);
    }
  };

  const fetchReviewableWorkorders = async (token, signal) => {
    try {
      setReviewableLoading(true);
      setReviewableError(null);

      const response = await fetch(`${API_BASE_URL}/businesses/${businessId}/my-reviewable-workorders`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
        signal,
      });

      if (response.status === 404) {
        setReviewableError('İşletme bulunamadı.');
        setReviewableWorkorders([]);
        setSelectedWorkorderId('');
        return;
      }

      const payload = await response.json().catch(() => []);

      if (!response.ok) {
        const detailMessage = payload?.detail
          ? (typeof payload.detail === 'string' ? payload.detail : JSON.stringify(payload.detail))
          : `HTTP ${response.status}: ${response.statusText}`;
        setReviewableError(detailMessage);
        setReviewableWorkorders([]);
        setSelectedWorkorderId('');
        return;
      }

      if (!Array.isArray(payload)) {
        throw new Error('Geçersiz API yanıtı: Array bekleniyordu');
      }

      setReviewableWorkorders(payload);
      setSelectedWorkorderId(payload.length > 0 ? String(payload[0].workorder_id) : '');
    } catch (err) {
      if (err?.name === 'AbortError') {
        return;
      }

      if (err.message.includes('fetch')) {
        setReviewableError('Yorum yapılabilir hizmetler yüklenemedi. Backend bağlantısı kurulamadı.');
      } else {
        setReviewableError('Yorum yapılabilir hizmetler yüklenemedi: ' + err.message);
      }
      setReviewableWorkorders([]);
      setSelectedWorkorderId('');
    } finally {
      setReviewableLoading(false);
    }
  };

  const handleSubmitReview = async (event) => {
    event.preventDefault();
    setSubmitError(null);
    setSubmitSuccess(null);

    const trimmedComment = comment.trim();
    const parsedWorkorderId = Number(selectedWorkorderId);
    const parsedRating = Number(rating);

    if (!selectedWorkorderId || Number.isNaN(parsedWorkorderId) || parsedWorkorderId <= 0) {
      setSubmitError('Lütfen yorum yapılacak hizmeti seçin.');
      return;
    }

    if (Number.isNaN(parsedRating) || parsedRating < 1 || parsedRating > 5) {
      setSubmitError('Puan 1 ile 5 arasında olmalıdır.');
      return;
    }

    if (!trimmedComment) {
      setSubmitError('Yorum boş olamaz.');
      return;
    }

    const token = localStorage.getItem('access_token');
    if (!token) {
      setSubmitError('Yorum göndermek için giriş yapmalısınız.');
      return;
    }

    try {
      setSubmitLoading(true);

      const response = await fetch(`${API_BASE_URL}/businesses/${businessId}/reviews`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          workorder_id: parsedWorkorderId,
          rating: parsedRating,
          comment: trimmedComment,
        }),
      });

      const payload = await response.json().catch(() => ({}));

      if (!response.ok) {
        const detailMessage = payload?.detail
          ? (typeof payload.detail === 'string' ? payload.detail : JSON.stringify(payload.detail))
          : `HTTP ${response.status}: ${response.statusText}`;
        setSubmitError(detailMessage);
        return;
      }

      setSubmitSuccess('Yorum başarıyla gönderildi.');
      setRating('5');
      setComment('');

      await Promise.all([
        fetchBusinessReviews(),
        fetchBusinessDetail(),
        fetchReviewableWorkorders(token),
      ]);
    } catch (err) {
      if (err.message.includes('fetch')) {
        setSubmitError('Yorum gönderilemedi. Backend bağlantısı kurulamadı.');
      } else {
        setSubmitError('Yorum gönderilemedi: ' + err.message);
      }
    } finally {
      setSubmitLoading(false);
    }
  };

  if (businessLoading) {
    return <div>Yükleniyor...</div>;
  }

  if (businessError) {
    return (
      <div>
        <div style={{ color: 'red' }}>{businessError}</div>
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

  const averageRatingText = business.average_rating === null || business.average_rating === undefined
    ? 'Henüz puan yok'
    : Number(business.average_rating).toFixed(1);

  return (
    <div className="business-detail-page">
      <h2>{business.name}</h2>
      <div className="business-detail-card">
        <p><strong>Adres:</strong> {business.address || 'Belirtilmemiş'}</p>
        <p><strong>Telefon:</strong> {business.phone || 'Belirtilmemiş'}</p>
        <p><strong>Açıklama:</strong> {business.description || 'Belirtilmemiş'}</p>
        <p><strong>Ortalama Puan:</strong> {averageRatingText}</p>
        <p><strong>Yorum Sayısı:</strong> {business.review_count ?? 0}</p>
      </div>

      <div className="review-section">
        <h3>Yorumlar</h3>
        {reviewsLoading && <p>Yorumlar yükleniyor...</p>}
        {reviewsError && <p className="ui-error">{reviewsError}</p>}
        {!reviewsLoading && !reviewsError && reviews.length === 0 && (
          <p>Bu işletme için henüz yorum yok.</p>
        )}
        {!reviewsLoading && !reviewsError && reviews.length > 0 && (
          <ul className="review-list">
            {reviews.map((review) => (
              <li key={review.id} className="review-item">
                <p><strong>Puan:</strong> {review.rating}/5</p>
                {review.service_type && <p><strong>Hizmet:</strong> {review.service_type}</p>}
                {review.workorder_description && <p><strong>Başlık:</strong> {review.workorder_description}</p>}
                <p><strong>Yorum:</strong> {review.comment || 'Yorum yok'}</p>
                <p>
                  <strong>Tarih:</strong>{' '}
                  {review.created_at
                    ? new Date(review.created_at).toLocaleDateString('tr-TR')
                    : 'Bilinmiyor'}
                </p>
              </li>
            ))}
          </ul>
        )}
      </div>

      <div className="review-section">
        <h3>Yorum Bırak</h3>
        {authStatus === 'checking' && <p>Kullanıcı bilgisi kontrol ediliyor...</p>}

        {authStatus === 'no-token' && (
          <p>Yorum bırakmak için müşteri hesabıyla giriş yapmalısınız.</p>
        )}

        {authStatus === 'unauthorized' && (
          <p>Oturumunuz geçersiz veya süresi dolmuş. Yorum bırakmak için tekrar giriş yapın.</p>
        )}

        {authStatus === 'authenticated' && currentUserRole && currentUserRole !== 'customer' && (
          <p>Yorum bırakmak için müşteri hesabı gerekir.</p>
        )}

        {authStatus === 'authenticated' && currentUserRole === 'customer' && reviewableLoading && (
          <p>Yorum yapılabilir hizmetler yükleniyor...</p>
        )}
        {authStatus === 'authenticated' && currentUserRole === 'customer' && reviewableError && (
          <p className="ui-error">{reviewableError}</p>
        )}
        {authStatus === 'authenticated' && currentUserRole === 'customer' && !reviewableLoading && !reviewableError && reviewableWorkorders.length === 0 && (
          <p>Bu işletme için yorum yapılabilir hizmet kaydınız bulunmuyor.</p>
        )}

        {authStatus === 'authenticated' && currentUserRole === 'customer' && !reviewableLoading && !reviewableError && reviewableWorkorders.length > 0 && (
          <form onSubmit={handleSubmitReview} className="review-form">
            <label>
              Yorum yapılacak hizmet
              <select
                value={selectedWorkorderId}
                onChange={(event) => setSelectedWorkorderId(event.target.value)}
              >
                {reviewableWorkorders.map((workorder) => (
                  <option key={workorder.workorder_id} value={workorder.workorder_id}>
                    {workorder.service_type}
                    {workorder.description ? ` - ${workorder.description}` : ''}
                  </option>
                ))}
              </select>
            </label>

            <label>
              Puan (1-5)
              <input
                type="number"
                min="1"
                max="5"
                value={rating}
                onChange={(event) => setRating(event.target.value)}
              />
            </label>

            <label>
              Yorum
              <textarea
                rows="4"
                value={comment}
                onChange={(event) => setComment(event.target.value)}
                placeholder="Hizmet deneyiminizi yazın"
              />
            </label>

            {submitError && <p className="ui-error">{submitError}</p>}
            {submitSuccess && <p className="ui-success">{submitSuccess}</p>}

            <button type="submit" disabled={submitLoading}>
              {submitLoading ? 'Gönderiliyor...' : 'Yorum Gönder'}
            </button>
          </form>
        )}
      </div>

      <button onClick={onBack}>Listeye Geri Dön</button>
    </div>
  );
}

export default BusinessDetail;