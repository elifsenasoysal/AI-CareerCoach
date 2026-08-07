import React, { useState } from 'react';
import Header from './components/Header';
import CvAnalyzer from './components/CvAnalyzer';
import InterviewSimulator from './components/InterviewSimulator';

export default function App() {
  const [activeTab, setActiveTab] = useState('cv'); // 'cv' or 'interview'

  return (
    <div className="app-layout">
      {/* Top Header & Navigation */}
      <Header activeTab={activeTab} setActiveTab={setActiveTab} />
      
      {/* Active Tab Screen */}
      <main className="main-content">
        {activeTab === 'cv' ? <CvAnalyzer /> : <InterviewSimulator />}
      </main>

      {/* Footer */}
      <footer className="footer">
        <p>© 2026 AI Career Coach. Tüm hakları saklıdır. Yapay zeka ile yerel olarak güçlendirilmiştir.</p>
      </footer>
    </div>
  );
}
