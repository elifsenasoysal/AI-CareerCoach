import React, { useState, useRef, useEffect } from 'react';
import { User, MessageSquare, AlertCircle, RefreshCw, ChevronRight, Award, ThumbsUp, Send } from 'lucide-react';

export default function InterviewSimulator() {
  const [role, setRole] = useState('');
  const [experienceLevel, setExperienceLevel] = useState('Mid');
  const [focusAreas, setFocusAreas] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  
  // Session State
  const [sessionId, setSessionId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [userAnswer, setUserAnswer] = useState('');
  const [waitingForFeedback, setWaitingForFeedback] = useState(false);
  
  // Active Question Feedback State (temporary feedback show before moving to next question)
  const [currentFeedback, setCurrentFeedback] = useState(null);
  const [sessionFinished, setSessionFinished] = useState(false);
  const [scores, setScores] = useState([]);

  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, waitingForFeedback, currentFeedback]);

  const handleStartInterview = async (e) => {
    e.preventDefault();
    if (!role.trim()) {
      setError('Lütfen simüle edilecek iş pozisyonunu girin.');
      return;
    }

    setLoading(true);
    setError('');

    const focusAreasList = focusAreas
      ? focusAreas.split(',').map((x) => x.trim()).filter((x) => x.length > 0)
      : [];

    try {
      const response = await fetch('http://localhost:8000/api/v1/interview/start', {
        method: 'POST',
        Haders: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          role: role.trim(),
          experience_level: experienceLevel,
          focus_areas: focusAreasList.length > 0 ? focusAreasList : null,
        }),
      });

      if (!response.ok) {
        throw new Error('Mülakat oturumu başlatılırken bir hata oluştu.');
      }

      const data = await response.json();
      setSessionId(data.session_id);
      
      // Add first question to chat
      setMessages([
        {
          id: 1,
          sender: 'recruiter',
          text: data.first_question,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        },
      ]);
      setScores([]);
      setSessionFinished(false);
      setCurrentFeedback(null);
    } catch (err) {
      logger.error && logger.error(err); // Avoid console logs
      setError(err.message || 'Sunucuyla bağlantı kurulamadı. Mülakat başlatılamıyor.');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmitAnswer = async (e) => {
    e.preventDefault();
    if (!userAnswer.trim()) return;

    const currentQuestion = messages[messages.length - 1].text;
    const answerText = userAnswer.trim();
    
    // Add user's answer to message list
    setMessages((prev) => [
      ...prev,
      {
        id: prev.length + 1,
        sender: 'candidate',
        text: answerText,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      },
    ]);
    
    setUserAnswer('');
    setWaitingForFeedback(true);
    setError('');

    try {
      const response = await fetch('http://localhost:8000/api/v1/interview/respond', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          question: currentQuestion,
          answer: answerText,
        }),
      });

      if (!response.ok) {
        throw new Error('Cevap değerlendirilirken bir hata oluştu.');
      }

      const data = await response.json();
      
      // Store evaluation feedback to present it to the user
      setCurrentFeedback({
        feedback: data.feedback,
        score: data.score,
        nextQuestion: data.next_question,
      });
      
      setScores((prev) => [...prev, data.score]);
    } catch (err) {
      logger.error && logger.error(err); // Avoid console logs
      setError(err.message || 'Sunucuyla bağlantı kurulamadı. Cevap gönderilemedi.');
      // Remove candidate's un-evaluated answer so they can try again
      setMessages((prev) => prev.slice(0, -1));
    } finally {
      setWaitingForFeedback(false);
    }
  };

  const handleNextQuestion = () => {
    if (!currentFeedback) return;

    if (currentFeedback.nextQuestion) {
      // Append next recruiter question to conversation
      setMessages((prev) => [
        ...prev,
        {
          id: prev.length + 1,
          sender: 'recruiter',
          text: currentFeedback.nextQuestion,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        },
      ]);
      setCurrentFeedback(null);
    } else {
      // No more questions, finish simulation
      setSessionFinished(true);
    }
  };

  const handleRestart = () => {
    setSessionId(null);
    setMessages([]);
    setUserAnswer('');
    setCurrentFeedback(null);
    setSessionFinished(false);
    setScores([]);
  };

  const getAverageScore = () => {
    if (scores.length === 0) return 0;
    const sum = scores.reduce((a, b) => a + b, 0);
    return (sum / scores.length).toFixed(1);
  };

  return (
    <div className="simulator-container animate-fade-in">
      <div className="section-header">
        <h2 className="section-title">Yapay Zekâ Mülakat Koçu</h2>
        <p className="section-subtitle">Hedeflediğiniz pozisyona göre dinamik, teknik bir mülakat simülasyonuna katılın ve anlık geri bildirim alın.</p>
      </div>

      {error && (
        <div className="alert alert-error">
          <AlertCircle size={20} />
          <span>{error}</span>
        </div>
      )}

      {/* 1. Setup Panel */}
      {!sessionId && (
        <form onSubmit={handleStartInterview} className="simulator-setup-form glass-card animate-fade-in">
          <h3>Mülakat Oturumu Ayarları</h3>
          
          <div className="setup-grid">
            <div className="input-group">
              <label htmlFor="interview-role">Hedef İş Pozisyonu</label>
              <input
                id="interview-role"
                type="text"
                placeholder="Örn: React Developer, Python Backend..."
                value={role}
                onChange={(e) => setRole(e.target.value)}
              />
            </div>

            <div className="input-group">
              <label htmlFor="interview-level">Deneyim Düzeyi</label>
              <select
                id="interview-level"
                value={experienceLevel}
                onChange={(e) => setExperienceLevel(e.target.value)}
              >
                <option value="Junior">Junior (Başlangıç)</option>
                <option value="Mid">Mid (Orta Seviye)</option>
                <option value="Senior">Senior (İleri Seviye)</option>
                <option value="Lead">Lead / Architect</option>
              </select>
            </div>
          </div>

          <div className="input-group">
            <label htmlFor="interview-focus">Odak Alanları / Konular (İsteğe Bağlı)</label>
            <input
              id="interview-focus"
              type="text"
              placeholder="Virgülle ayırın, örn: React Hooks, Redux, CSS Grid..."
              value={focusAreas}
              onChange={(e) => setFocusAreas(e.target.value)}
            />
          </div>

          <button type="submit" disabled={loading} className="btn-primary start-btn">
            {loading ? (
              <>
                <RefreshCw className="animate-spin" size={18} />
                Mülakat Başlatılıyor...
              </>
            ) : (
              <>
                Mülakatı Başlat
                <ChevronRight size={18} />
              </>
            )}
          </button>
        </form>
      )}

      {/* 2. Simulation Chat interface */}
      {sessionId && !sessionFinished && (
        <div className="chat-interface glass-card animate-fade-in">
          
          {/* Chat Header */}
          <div className="chat-header">
            <div className="chat-header-info">
              <div className="status-indicator"></div>
              <h4>{role} Mülakatı ({experienceLevel})</h4>
            </div>
            <button onClick={handleRestart} className="btn-secondary btn-small">
              Yeniden Başlat
            </button>
          </div>

          {/* Messages Flow Area */}
          <div className="chat-flow">
            {messages.map((msg) => (
              <div key={msg.id} className={`message-bubble-wrapper ${msg.sender}`}>
                <div className="message-sender-avatar">
                  {msg.sender === 'recruiter' ? <MessageSquare size={16} /> : <User size={16} />}
                </div>
                <div className="message-bubble">
                  <div className="message-text">{msg.text}</div>
                  <span className="message-time">{msg.timestamp}</span>
                </div>
              </div>
            ))}

            {/* Waiting for feedback loader */}
            {waitingForFeedback && (
              <div className="message-bubble-wrapper recruiter">
                <div className="message-sender-avatar">
                  <RefreshCw size={16} className="animate-spin" />
                </div>
                <div className="message-bubble loading-bubble">
                  <p>Cevabınız analiz ediliyor, puanınız hesaplanıyor...</p>
                </div>
              </div>
            )}

            {/* Floating current feedback card */}
            {currentFeedback && (
              <div className="feedback-container-bubble animate-fade-in">
                <div className="feedback-header">
                  <div className="feedback-score-badge">
                    <Award size={18} />
                    <span>Cevap Skoru: {currentFeedback.score} / 10</span>
                  </div>
                  <div className="feedback-icon-title">
                    <ThumbsUp size={16} />
                    <span>Mülakatçı Değerlendirmesi</span>
                  </div>
                </div>
                <p className="feedback-text">{currentFeedback.feedback}</p>
                
                <button onClick={handleNextQuestion} className="btn-primary next-question-btn">
                  {currentFeedback.nextQuestion ? 'Sonraki Soruya Geç' : 'Mülakatı Sonlandır'}
                  <ChevronRight size={16} />
                </button>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* User Input Form */}
          <form onSubmit={handleSubmitAnswer} className="chat-input-bar">
            <textarea
              rows="2"
              placeholder={
                currentFeedback
                  ? 'Devam etmek için yukarıdaki "Sonraki Soru" butonuna basın...'
                  : 'Cevabınızı buraya yazın...'
              }
              value={userAnswer}
              onChange={(e) => setUserAnswer(e.target.value)}
              disabled={waitingForFeedback || !!currentFeedback}
            ></textarea>
            <button 
              type="submit" 
              className="send-button btn-primary"
              disabled={!userAnswer.trim() || waitingForFeedback || !!currentFeedback}
            >
              <Send size={18} />
            </button>
          </form>

        </div>
      )}

      {/* 3. Session Completed Dashboard */}
      {sessionFinished && (
        <div className="finished-dashboard glass-card text-center animate-fade-in">
          <div className="award-icon-box">
            <Award size={48} />
          </div>
          <h2>Mülakat Simülasyonu Tamamlandı!</h2>
          <p className="subtitle">Cevaplarınız genel bir analiz süzgecinden geçirildi.</p>

          <div className="final-stats-grid">
            <div className="stat-card">
              <span className="stat-number">{scores.length}</span>
              <span className="stat-label">Cevaplanan Soru</span>
            </div>
            <div className="stat-card highlight">
              <span className="stat-number">{getAverageScore()} / 10</span>
              <span className="stat-label">Ortalama Mülakat Skoru</span>
            </div>
          </div>

          <p className="finished-message">
            {getAverageScore() >= 8
              ? 'Mükemmel bir performans! Teknik yetkinlikleriniz ve ifade yeteneğiniz bu pozisyon için fazlasıyla yeterli.'
              : getAverageScore() >= 6
                ? 'İyi bir performans çıkardınız. Ufak tefek eksikliklerinizi tamamlayarak çok daha güçlü cevaplar verebilirsiniz.'
                : 'Birkaç teknik konuda eksiklikler tespit edildi. İlgili odak alanlarındaki konuları çalışarak tekrar denemenizi öneririz.'}
          </p>

          <button onClick={handleRestart} className="btn-primary restart-sim-btn">
            Yeni Mülakat Başlat
          </button>
        </div>
      )}
    </div>
  );
}
