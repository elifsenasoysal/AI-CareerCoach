import React, { useState } from 'react';
import { Upload, FileText, CheckCircle2, AlertCircle, RefreshCw, BarChart2, Star } from 'lucide-react';

export default function CvAnalyzer() {
  const [file, setFile] = useState(null);
  const [jobPosition, setJobPosition] = useState('');
  const [jobDescription, setJobDescription] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState(null);
  const [isDragOver, setIsDragOver] = useState(false);

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      if (selectedFile.type !== 'application/pdf') {
        setError('Yalnızca PDF formatındaki dosyalar desteklenmektedir.');
        setFile(null);
      } else {
        setFile(selectedFile);
        setError('');
      }
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = () => {
    setIsDragOver(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragOver(false);
    const selectedFile = e.dataTransfer.files[0];
    if (selectedFile) {
      if (selectedFile.type !== 'application/pdf') {
        setError('Yalnızca PDF formatındaki dosyalar desteklenmektedir.');
        setFile(null);
      } else {
        setFile(selectedFile);
        setError('');
      }
    }
  };

  const handleReset = () => {
    setFile(null);
    setResult(null);
    setError('');
  };

  const handleAnalyze = async (e) => {
    e.preventDefault();
    if (!file) {
      setError('Lütfen bir CV PDF dosyası seçin.');
      return;
    }

    setLoading(true);
    setError('');
    
    const formData = new FormData();
    formData.append('file', file);
    if (jobPosition) formData.append('job_position', jobPosition);
    if (jobDescription) formData.append('job_description', jobDescription);

    try {
      const response = await fetch('http://localhost:8000/api/v1/cv/analyze', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Analiz sırasında sunucu tarafında bir hata oluştu.');
      }

      const data = await response.json();
      setResult(data);
    } catch (err) {
      logger.error && logger.error(err); // Avoid console logs
      setError(err.message || 'Sunucuyla bağlantı kurulamadı. Lütfen API servisinin çalıştığından emin olun.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="analyzer-container animate-fade-in">
      <div className="section-header">
        <h2 className="section-title">CV Analizi ve ATS Optimizasyonu</h2>
        <p className="section-subtitle">CV'nizi hedeflediğiniz işe veya pozisyona göre puanlayın, eksik becerilerinizi tamamlayın.</p>
      </div>

      {error && (
        <div className="alert alert-error">
          <AlertCircle size={20} />
          <span>{error}</span>
        </div>
      )}

      {!result ? (
        <form onSubmit={handleAnalyze} className="analyzer-form">
          <div className="form-grid">
            
            {/* Left: Inputs */}
            <div className="inputs-panel glass-card">
              <div className="input-group">
                <label htmlFor="position">Hedef Pozisyon (İsteğe Bağlı)</label>
                <input
                  id="position"
                  type="text"
                  placeholder="Örn: Frontend Developer, Veri Analisti..."
                  value={jobPosition}
                  onChange={(e) => setJobPosition(e.target.value)}
                />
              </div>

              <div className="input-group">
                <label htmlFor="description">İlanın İş Tanımı / Job Description (İsteğe Bağlı)</label>
                <textarea
                  id="description"
                  rows="6"
                  placeholder="Kriterlerin çıkarılması için ilanın detaylarını buraya yapıştırabilirsiniz..."
                  value={jobDescription}
                  onChange={(e) => setJobDescription(e.target.value)}
                ></textarea>
              </div>
            </div>

            {/* Right: Dropzone */}
            <div 
              className={`dropzone glass-card ${isDragOver ? 'dragover' : ''}`}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
            >
              {!file ? (
                <div className="dropzone-content">
                  <div className="upload-icon-box">
                    <Upload size={32} />
                  </div>
                  <h3>CV Dosyanızı Yükleyin</h3>
                  <p>Dosyayı sürükleyip bırakın veya seçmek için tıklayın</p>
                  <span className="file-info-label">Sadece PDF formatı desteklenir</span>
                  <input
                    type="file"
                    accept="application/pdf"
                    onChange={handleFileChange}
                    className="file-input-hidden"
                    id="cv-file-upload"
                  />
                  <label htmlFor="cv-file-upload" className="btn-secondary file-upload-label">
                    Dosya Seçin
                  </label>
                </div>
              ) : (
                <div className="dropzone-selected">
                  <div className="file-icon-box">
                    <FileText size={40} />
                  </div>
                  <h4 className="file-name">{file.name}</h4>
                  <p className="file-size">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
                  
                  <div className="selected-actions">
                    <button type="button" onClick={handleReset} className="btn-secondary">
                      Değiştir
                    </button>
                    <button type="submit" disabled={loading} className="btn-primary">
                      {loading ? (
                        <>
                          <RefreshCw className="animate-spin" size={18} />
                          Analiz Ediliyor...
                        </>
                      ) : 'Analiz Et'}
                    </button>
                  </div>
                </div>
              )}
            </div>

          </div>
        </form>
      ) : (
        /* Analysis Results Dashboard */
        <div className="results-dashboard animate-fade-in">
          <div className="results-top-bar">
            <button onClick={handleReset} className="btn-secondary flex-center">
              <RefreshCw size={16} />
              Yeni Bir CV Yükle
            </button>
          </div>

          <div className="results-grid">
            
            {/* Left: Overall Score and Breakdown */}
            <div className="summary-column">
              
              {/* ATS Score Card */}
              <div className="glass-card score-card text-center">
                <h3>Genel Eşleşme Skoru (ATS)</h3>
                <div className="score-circle-wrapper">
                  <div className="score-circle">
                    <span className="score-number">{result.final_score}</span>
                    <span className="score-label">/ 100</span>
                  </div>
                </div>
                <p className="score-message">
                  {result.final_score >= 80 
                    ? 'Tebrikler! CV\'niz bu pozisyon için güçlü bir eşleşmeye sahip.' 
                    : result.final_score >= 60 
                      ? 'İyi bir temel var ancak geliştirilmesi gereken alanlar bulunuyor.' 
                      : 'CV\'nizin hedef pozisyona göre optimize edilmesi gerekiyor.'}
                </p>
              </div>

              {/* Score Breakdown Card */}
              <div className="glass-card breakdown-card">
                <h3>
                  <BarChart2 size={18} />
                  Puan Kırılımları
                </h3>
                <div className="progress-bars-container">
                  <div className="progress-item">
                    <div className="progress-label">
                      <span>Teknik Beceriler</span>
                      <span>{result.score_breakdown.skill_score} / 40</span>
                    </div>
                    <div className="progress-track">
                      <div className="progress-fill fill-primary" style={{ width: `${(result.score_breakdown.skill_score / 40) * 100}%` }}></div>
                    </div>
                  </div>

                  <div className="progress-item">
                    <div className="progress-label">
                      <span>Anahtar Kelime Uyum</span>
                      <span>{result.score_breakdown.keyword_score} / 30</span>
                    </div>
                    <div className="progress-track">
                      <div className="progress-fill fill-secondary" style={{ width: `${(result.score_breakdown.keyword_score / 30) * 100}%` }}></div>
                    </div>
                  </div>

                  <div className="progress-item">
                    <div className="progress-label">
                      <span>CV Biçimlendirme & Düzen</span>
                      <span>{result.score_breakdown.formatting_score} / 30</span>
                    </div>
                    <div className="progress-track">
                      <div className="progress-fill fill-accent" style={{ width: `${(result.score_breakdown.formatting_score / 30) * 100}%` }}></div>
                    </div>
                  </div>
                </div>
              </div>

            </div>

            {/* Right: Detailed feedback analysis */}
            <div className="details-column">
              
              {/* Parsed Skills */}
              <div className="glass-card details-card">
                <h3>Tespit Edilen Yetkinlikler</h3>
                <div className="skills-badge-container">
                  {result.parsed_skills.map((skill, i) => (
                    <span key={i} className="skill-badge">{skill}</span>
                  ))}
                  {result.parsed_skills.length === 0 && (
                    <p className="no-data-text">CV metninde belirgin bir yetkinlik tespit edilemedi.</p>
                  )}
                </div>
              </div>

              {/* Applied Criteria */}
              {result.applied_criteria && result.applied_criteria.length > 0 && (
                <div className="glass-card details-card">
                  <h3>Pozisyonda Aranan Değerlendirme Kriterleri</h3>
                  <div className="criteria-list">
                    {result.applied_criteria.map((criterion, i) => (
                      <div key={i} className="criterion-item">
                        <span className="criterion-name">{criterion.name}</span>
                        <span className="criterion-weight">Önem Ağırlığı: {(criterion.weight * 100).toFixed(0)}%</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Improvements Feedback */}
              <div className="glass-card details-card">
                <h3>Geliştirme ve İyileştirme Önerileri</h3>
                <ul className="feedback-list">
                  {result.suggested_improvements.map((improvement, i) => (
                    <li key={i} className="feedback-item">
                      <CheckCircle2 size={16} className="text-success" />
                      <span>{improvement}</span>
                    </li>
                  ))}
                  {result.suggested_improvements.length === 0 && (
                    <p className="no-data-text text-success">Mükemmel! Geliştirilmesi gereken kritik bir eksik bulunamadı.</p>
                  )}
                </ul>
              </div>

            </div>

          </div>
        </div>
      )}
    </div>
  );
}
