import './App.css';
import { useState } from 'react';

const navItems = [
  { label: 'Overview', href: '#overview' },
  { label: 'Program', href: '#program' },
  { label: 'Profiler', href: '#profiler' },
  { label: 'Get Involved', href: '#interest' },
];

function App() {
  const [repos, setRepos] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [profiles, setProfiles] = useState([]);
  const [status, setStatus] = useState({ message: '', type: '' });
  const [loading, setLoading] = useState(false);

  const API_BASE = 'http://localhost:8000';

  const showStatus = (message, type) => {
    setStatus({ message, type });
    if (type === 'success') {
      setTimeout(() => setStatus({ message: '', type: '' }), 5000);
    }
  };

  const analyzeRepos = async () => {
    const repoList = repos.split('\n').filter(r => r.trim());

    if (repoList.length === 0) {
      showStatus('Please enter at least one repository URL', 'error');
      return;
    }

    setLoading(true);
    showStatus(`Analyzing ${repoList.length} repositor${repoList.length > 1 ? 'ies' : 'y'}... This may take 30-90 seconds`, 'loading');

    try {
      const response = await fetch(`${API_BASE}/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(repoList)
      });

      if (!response.ok) {
        throw new Error('Analysis failed');
      }

      const data = await response.json();
      showStatus(`Success! Generated ${data.profiles_generated} developer profile${data.profiles_generated !== 1 ? 's' : ''}`, 'success');
      setProfiles(data.profiles);
    } catch (error) {
      showStatus(`Error: ${error.message}. Make sure backend is running on port 8000.`, 'error');
      console.error('Error:', error);
    } finally {
      setLoading(false);
    }
  };

  const searchDevelopers = async () => {
    if (!searchQuery.trim()) {
      showStatus('Please enter a search query', 'error');
      return;
    }

    showStatus('Searching...', 'loading');

    try {
      const response = await fetch(`${API_BASE}/search?query=${encodeURIComponent(searchQuery)}`);
      const data = await response.json();

      if (data.matches && data.matches.length > 0) {
        showStatus(`Found ${data.matches.length} matching developer${data.matches.length !== 1 ? 's' : ''}`, 'success');
        setProfiles(data.matches);
      } else {
        showStatus('No matches found. Try a different query.', 'error');
      }
    } catch (error) {
      showStatus(`Search error: ${error.message}`, 'error');
      console.error('Error:', error);
    }
  };

  const loadExistingProfiles = async () => {
    try {
      const response = await fetch(`${API_BASE}/profiles`);
      const data = await response.json();
      if (data.profiles && data.profiles.length > 0) {
        setProfiles(data.profiles);
      }
    } catch (error) {
      console.log('No existing profiles or server not running');
    }
  };

  return (
    <div className="App">
      <nav className="nav">
        <div className="brand">
          <span className="brand-pill">PXAE</span>
          <span>Penn × Anthropic</span>
        </div>
        <ul className="nav-links">
          {navItems.map((item) => (
            <li key={item.label}>
              <a href={item.href}>{item.label}</a>
            </li>
          ))}
        </ul>
        <a className="cta-link" href="#interest">
          Join the list
        </a>
      </nav>

      <main>
        <section id="overview" className="hero">
          <p className="eyebrow">Penn x Anthropic</p>
          <h1>Empowering ethical AI builders on campus</h1>
          <p className="lede">
            We are a student-led initiative helping the Penn community explore responsible AI
            development through hands-on projects, mentorship, and access to Anthropic experts.
          </p>
          <div className="hero-actions">
            <a className="cta-link primary" href="#program">
              Explore the program
            </a>
            <a className="cta-link secondary" href="#interest">
              Share interest
            </a>
          </div>
        </section>

        <section id="program" className="info-grid">
          <article className="info-card">
            <h2>Workshops</h2>
            <p>
              Weekly deep dives into frontier models, alignment, safety strategy, and practical
              tooling. Sessions balance technical skill building with facilitated discussions.
            </p>
          </article>
          <article className="info-card">
            <h2>Mentorship</h2>
            <p>
              Small-group circles pair students with Anthropic researchers and alumni to review
              ideas, get career advice, and workshop project milestones.
            </p>
          </article>
          <article className="info-card">
            <h2>Impact Projects</h2>
            <p>
              Interdisciplinary teams prototype solutions for civic partners, producing case studies
              that showcase how safe AI systems can solve real problems.
            </p>
          </article>
        </section>

        <section id="profiler" className="profiler-section">
          <div className="profiler-header">
            <p className="eyebrow">Developer Discovery</p>
            <h2>GitHub Developer Profiler</h2>
            <p className="profiler-desc">
              AI-powered developer profiles from repository analysis. Find the right expertise for your project.
            </p>
          </div>

          <div className="profiler-content">
            <div className="profiler-card">
              <div className="profiler-card-header">
                <span className="step-badge">1</span>
                <h3>Analyze Repositories</h3>
              </div>
              <textarea
                value={repos}
                onChange={(e) => setRepos(e.target.value)}
                placeholder="Paste GitHub repository URLs (one per line)&#10;&#10;Example:&#10;https://github.com/fastapi/fastapi&#10;https://github.com/anthropics/anthropic-sdk-python"
                className="repo-input"
                rows="6"
              />
              <button
                onClick={analyzeRepos}
                disabled={loading}
                className="profiler-btn primary"
              >
                {loading ? '⏳ Analyzing...' : '🔍 Generate Profiles'}
              </button>
              {status.message && (
                <div className={`status-message ${status.type}`}>
                  {status.message}
                </div>
              )}
            </div>

            <div className="profiler-card">
              <div className="profiler-card-header">
                <span className="step-badge">2</span>
                <h3>Search Developers</h3>
              </div>
              <div className="search-container">
                <input
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && searchDevelopers()}
                  placeholder="Who can help with machine learning? Who writes good tests? Who's a React expert?"
                  className="search-input"
                />
                <button onClick={searchDevelopers} className="profiler-btn secondary">
                  Search
                </button>
              </div>
              <button onClick={loadExistingProfiles} className="profiler-btn tertiary">
                Load All Profiles
              </button>
            </div>
          </div>

          {profiles.length > 0 && (
            <div className="profiles-grid">
              {profiles.map((profile) => (
                <div key={profile.github_username} className="profile-card">
                  <div className="profile-header">
                    <img
                      src={profile.avatar_url}
                      alt={profile.github_username}
                      className="profile-avatar"
                    />
                    <div className="profile-info">
                      <h4>{profile.name || profile.github_username}</h4>
                      <a
                        href={`https://github.com/${profile.github_username}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="profile-link"
                      >
                        @{profile.github_username}
                      </a>
                    </div>
                  </div>

                  {profile.match_reason && (
                    <div className="match-reason">
                      <strong>Match:</strong> {profile.match_reason}
                    </div>
                  )}

                  <p className="profile-summary">{profile.ai_summary}</p>

                  <div className="profile-section">
                    <span className="profile-label">Languages</span>
                    <div className="tag-container">
                      {profile.primary_languages.map((lang) => (
                        <span key={lang} className="tag language-tag">
                          {lang}
                        </span>
                      ))}
                    </div>
                  </div>

                  <div className="profile-section">
                    <span className="profile-label">Expertise</span>
                    <div className="expertise-text">
                      {profile.expertise_areas.slice(0, 3).join(' • ')}
                    </div>
                  </div>

                  {profile.best_for && (
                    <div className="profile-section">
                      <span className="profile-label">Best For</span>
                      <ul className="best-for-list">
                        {profile.best_for.slice(0, 3).map((item, idx) => (
                          <li key={idx}>
                            <span className="check-icon">✓</span>
                            <span>{item}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  <div className="profile-footer">
                    <span>📊 {profile.total_commits} commits</span>
                    <span className="work-style">{profile.work_style}</span>
                  </div>
                </div>
              ))}
            </div>
          )}

          {profiles.length === 0 && !loading && (
            <div className="empty-state">
              <svg className="empty-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"></path>
              </svg>
              <p>No profiles yet. Start by analyzing a repository!</p>
            </div>
          )}
        </section>

        <section id="interest" className="info-card interest-card">
          <h2>Stay in the loop</h2>
          <p>
            We&apos;re finalizing the full semester roadmap. Leave your info and we&apos;ll send
            updates on kickoff dates, speaker announcements, and open application windows.
          </p>
          <ul>
            <li>Monthly digest with speaker reveals</li>
            <li>Early invitations to build weekends</li>
            <li>Priority mentorship matching</li>
          </ul>
          <a className="cta-link primary" href="mailto:pxae@penn.edu">
            Email pxae@penn.edu
          </a>
        </section>
      </main>

      <footer>
        <p>© {new Date().getFullYear()} Penn × Anthropic Emp Matching Initiative</p>
      </footer>
    </div>
  );
}

export default App;
