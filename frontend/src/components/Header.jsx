import React from 'react';
import { Sparkles, FileText, MessageSquare } from 'lucide-react';

export default function Header({ activeTab, setActiveTab }) {
  return (
    <header className="header-container">
      <div className="logo-section">
        <div className="logo-icon-box animate-pulse">
          <Sparkles size={24} />
        </div>
        <div className="logo-text-box">
          <h1 className="logo-title">AI Career Coach</h1>
          <p className="logo-subtitle">Yapay Zekâ Destekli Kariyer Asistanı</p>
        </div>
      </div>
      
      {/* Top Segmented Navigation Control */}
      <div className="tab-container">
        <button
          onClick={() => setActiveTab('cv')}
          className={`tab-btn ${activeTab === 'cv' ? 'active' : ''}`}
        >
          <FileText size={16} />
          <span>CV Analizi & ATS</span>
        </button>
        <button
          onClick={() => setActiveTab('interview')}
          className={`tab-btn ${activeTab === 'interview' ? 'active' : ''}`}
        >
          <MessageSquare size={16} />
          <span>Mülakat Koçu</span>
        </button>
      </div>
    </header>
  );
}
