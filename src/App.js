import './App.css';
import { useState, useEffect } from 'react';

const curatedRepos = [
  'https://github.com/fastai/fastai',
  'https://github.com/sindresorhus/awesome',
  'https://github.com/twbs/bootstrap'
];

const defaultMatchMeta = {
  usingClaude: false,
  demoMode: false,
  personaCount: 0,
  projectCount: 0,
  generatedAt: null,
};

function App() {
  const [demoMode, setDemoMode] = useState(null);
  const [personas, setPersonas] = useState([]);
  const [projects, setProjects] = useState([]);
  const [matchResults, setMatchResults] = useState([]);
  const [matchMeta, setMatchMeta] = useState(defaultMatchMeta);
  const [personasLoading, setPersonasLoading] = useState(false);
  const [projectsLoading, setProjectsLoading] = useState(false);
  const [matchesLoading, setMatchesLoading] = useState(false);
  const [personasError, setPersonasError] = useState('');
  const [projectsError, setProjectsError] = useState('');
  const [matchesError, setMatchesError] = useState('');
  const [matchAlert, setMatchAlert] = useState({ message: '', tone: '' });
  const [repoStatus, setRepoStatus] = useState({ message: '', type: '' });

  const API_BASE = 'http://localhost:8000';

  const checkDemoMode = async () => {
    try {
      const response = await fetch(`${API_BASE}/mode`);
      const data = await response.json();
      setDemoMode(data.demo_mode);
    } catch (error) {
      setDemoMode(true);
    }
  };

  const fetchPersonas = async () => {
    setPersonasLoading(true);
    setPersonasError('');
    try {
      const response = await fetch(`${API_BASE}/personas`);
      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(data.detail || 'Unable to load personas');
      }
      setPersonas(data.personas || []);
    } catch (error) {
      setPersonasError(error.message);
      setPersonas([]);
    } finally {
      setPersonasLoading(false);
    }
  };

  const fetchProjects = async () => {
    setProjectsLoading(true);
    setProjectsError('');
    try {
      const response = await fetch(`${API_BASE}/projects`);
      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(data.detail || 'Unable to load projects');
      }
      setProjects(data.projects || []);
    } catch (error) {
      setProjectsError(error.message);
      setProjects([]);
    } finally {
      setProjectsLoading(false);
    }
  };

  const fetchSavedMatches = async (showMessage = false) => {
    setMatchesLoading(true);
    setMatchesError('');
    if (showMessage) {
      setMatchAlert({ message: 'Refreshing saved results...', tone: 'info' });
    }
    try {
      const response = await fetch(`${API_BASE}/matches`);
      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        if (response.status === 404) {
          setMatchResults([]);
          setMatchMeta({ ...defaultMatchMeta });
          if (showMessage) {
            setMatchAlert({
              message: 'No saved matches yet. Run the matcher to generate recommendations.',
              tone: 'info',
            });
          }
          return;
        }
        throw new Error(data.detail || 'Unable to load saved matches');
      }

      setMatchResults(data.matches || []);
      setMatchMeta({
        usingClaude: Boolean(data.using_claude),
        demoMode: Boolean(data.demo_mode),
        personaCount: data.persona_count || 0,
        projectCount: data.project_count || 0,
        generatedAt: data.generated_at || null,
      });
      if (showMessage) {
        setMatchAlert({ message: 'Loaded latest saved matches.', tone: 'success' });
      }
    } catch (error) {
      setMatchesError(error.message);
      setMatchResults([]);
      setMatchMeta({ ...defaultMatchMeta });
      setMatchAlert({ message: '', tone: '' });
    } finally {
      setMatchesLoading(false);
    }
  };

  const runMatch = async () => {
    setMatchesLoading(true);
    setMatchesError('');
    setMatchAlert({ message: 'Contacting backend for fresh recommendations...', tone: 'info' });
    try {
      const response = await fetch(`${API_BASE}/match`, { method: 'POST' });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(data.detail || 'Unable to generate matches');
      }

      setMatchResults(data.matches || []);
      setMatchMeta({
        usingClaude: Boolean(data.using_claude),
        demoMode: Boolean(data.demo_mode),
        personaCount: data.persona_count || 0,
        projectCount: data.project_count || 0,
        generatedAt: data.generated_at || null,
      });
      setMatchAlert({
        message: data.using_claude
          ? 'Claude-generated matches ready!'
          : 'Demo recommendations refreshed.',
        tone: 'success',
      });
    } catch (error) {
      setMatchesError(error.message);
      setMatchAlert({ message: '', tone: '' });
    } finally {
      setMatchesLoading(false);
    }
  };

  const analyzeCuratedRepos = async () => {
    setRepoStatus({ message: 'Analyzing curated repositories...', type: 'loading' });
    try {
      const response = await fetch(`${API_BASE}/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(curatedRepos),
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(data.detail || 'Analysis failed');
      }
      setDemoMode(data.demo_mode);
      setRepoStatus({
        message: data.demo_mode
          ? `Demo data: showing ${data.profiles_generated} profile(s).`
          : `Success! Generated ${data.profiles_generated} developer profile(s).`,
        type: data.demo_mode ? 'info' : 'success',
      });
    } catch (error) {
      setRepoStatus({ message: error.message, type: 'error' });
    }
  };

  useEffect(() => {
    checkDemoMode();
    fetchPersonas();
    fetchProjects();
    fetchSavedMatches();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="App">
      <header className="app-header">
        <div>
          <p className="eyebrow">Penn × Anthropic</p>
          <h1>Matching Control Center</h1>
          <p className="header-desc">
            Monitor personas, project briefs, and Claude's pairing output from a single dashboard.
          </p>
        </div>
        <div className="header-status">
          <span className={`demo-flag ${demoMode ? 'on' : 'off'}`}>
            {demoMode ? 'Demo Mode' : 'API Mode'}
          </span>
        </div>
      </header>

      <main>
        <section className="curated-section">
          <div className="curated-info">
            <h2>Curated GitHub Repositories</h2>
            <p>
              Kick off profiling for our starter set of repositories. The backend will contact GitHub and store
              developer profiles that fuel downstream matching.
            </p>
          </div>
          <ul className="repo-list">
            {curatedRepos.map((repo) => (
              <li key={repo}>
                <span className="repo-bullet">↳</span>
                <a href={repo} target="_blank" rel="noopener noreferrer">
                  {repo}
                </a>
              </li>
            ))}
          </ul>
          <button className="primary-btn" onClick={analyzeCuratedRepos}>
            Analyze curated repositories
          </button>
          {repoStatus.message && (
            <div className={`repo-status ${repoStatus.type}`}>{repoStatus.message}</div>
          )}
        </section>

        <section className="matching-section">
          <div className="matching-header">
            <h2>Personas, Projects & Matches</h2>
            <p className="matching-desc">
              Everything shown here is read straight from <code>personal.json</code>, <code>projects.json</code>, and
              the last <code>/match</code> response saved to <code>output.json</code>.
            </p>
          </div>

          <div className="matching-actions">
            <div className="matching-meta">
              <span>👥 Personas: {personas.length}</span>
              <span>🧩 Projects: {projects.length}</span>
              {matchMeta.generatedAt && (
                <span>🕒 Last match: {new Date(matchMeta.generatedAt).toLocaleString()}</span>
              )}
              <span className={`claude-chip ${matchMeta.usingClaude ? 'on' : 'off'}`}>
                {matchMeta.usingClaude ? 'Claude AI' : 'Demo logic'}
              </span>
            </div>
            <div className="matching-buttons">
              <button
                className="ghost-btn"
                onClick={() => fetchSavedMatches(true)}
                disabled={matchesLoading}
              >
                {matchesLoading ? 'Refreshing…' : 'Reload saved matches'}
              </button>
              <button className="primary-btn" onClick={runMatch} disabled={matchesLoading}>
                {matchesLoading ? 'Matching…' : 'Run match with Claude'}
              </button>
            </div>
          </div>

          {matchAlert.message && (
            <div className={`match-alert ${matchAlert.tone}`}>{matchAlert.message}</div>
          )}
          {matchesError && <div className="match-alert error">{matchesError}</div>}

          <div className="matching-grid">
            <article className="data-panel">
              <div className="panel-header">
                <div>
                  <h3>Personas</h3>
                  <p className="panel-subtitle">Loaded from personal.json</p>
                </div>
                <button
                  className="refresh-btn"
                  onClick={fetchPersonas}
                  disabled={personasLoading}
                  aria-label="Refresh personas"
                >
                  ↻
                </button>
              </div>
              {personasLoading ? (
                <p className="data-status">Loading personas…</p>
              ) : personasError ? (
                <p className="data-status error">{personasError}</p>
              ) : (
                <div className="personas-list">
                  {personas.map((persona) => {
                    const targetRoles = persona?.application?.target_roles || [];
                    const skills = persona?.resume?.skills || [];
                    const interests =
                      persona?.survey?.responses?.find((resp) =>
                        resp.question?.toLowerCase().includes('projects')
                      )?.answer || '';

                    return (
                      <div key={persona.id} className="persona-card">
                        <div className="card-title">
                          <h4>{persona.full_name}</h4>
                          {persona?.application?.role_seniority && (
                            <span className="mini-pill">{persona.application.role_seniority}</span>
                          )}
                        </div>
                        {persona?.resume?.headline && (
                          <p className="persona-headline">{persona.resume.headline}</p>
                        )}
                        {targetRoles.length > 0 && (
                          <div className="tag-row">
                            {targetRoles.slice(0, 3).map((role) => (
                              <span key={role} className="tag-chip">
                                {role}
                              </span>
                            ))}
                          </div>
                        )}
                        {skills.length > 0 && (
                          <div className="skill-grid">
                            {skills.slice(0, 4).map((skill) => (
                              <span key={skill} className="skill-pill">
                                {skill}
                              </span>
                            ))}
                          </div>
                        )}
                        {interests && <p className="persona-quote">“{interests}”</p>}
                      </div>
                    );
                  })}
                </div>
              )}
            </article>

            <article className="data-panel">
              <div className="panel-header">
                <div>
                  <h3>Projects</h3>
                  <p className="panel-subtitle">Loaded from projects.json</p>
                </div>
                <button
                  className="refresh-btn"
                  onClick={fetchProjects}
                  disabled={projectsLoading}
                  aria-label="Refresh projects"
                >
                  ↻
                </button>
              </div>
              {projectsLoading ? (
                <p className="data-status">Loading projects…</p>
              ) : projectsError ? (
                <p className="data-status error">{projectsError}</p>
              ) : (
                <div className="projects-list">
                  {projects.map((project) => {
                    const features = project?.core_features || [];
                    const stack = project?.architecture_stack || {};

                    return (
                      <div key={project.project_name} className="project-card">
                        <h4>{project.project_name}</h4>
                        <p className="project-description">{project.Description}</p>
                        {features.length > 0 && (
                          <div className="tag-row">
                            {features.slice(0, 3).map((feature) => (
                              <span key={feature} className="tag-chip secondary">
                                {feature}
                              </span>
                            ))}
                          </div>
                        )}
                        {Object.keys(stack).length > 0 && (
                          <div className="stack-grid">
                            {Object.entries(stack).slice(0, 3).map(([layer, value]) => {
                              const items = Array.isArray(value) ? value.join(', ') : JSON.stringify(value);
                              return (
                                <div key={layer} className="stack-chip">
                                  <span className="stack-label">{layer}</span>
                                  <span className="stack-value">{items}</span>
                                </div>
                              );
                            })}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}
            </article>

            <article className="data-panel">
              <div className="panel-header">
                <div>
                  <h3>Match Output</h3>
                  <p className="panel-subtitle">Reflects output.json</p>
                </div>
                <button
                  className="refresh-btn"
                  onClick={() => fetchSavedMatches(true)}
                  disabled={matchesLoading}
                  aria-label="Refresh matches"
                >
                  ↻
                </button>
              </div>
              {matchesLoading && matchResults.length === 0 ? (
                <p className="data-status">Waiting for match results…</p>
              ) : matchResults.length === 0 ? (
                <p className="data-status">No matches yet. Run the matcher to populate this panel.</p>
              ) : (
                <div className="matches-list">
                  {matchResults.map((match) => (
                    <div key={match.persona_id} className="match-card">
                      <div className="card-title">
                        <h4>{match.persona_name}</h4>
                        <span className="mini-pill secondary">{match.persona_id}</span>
                      </div>
                      <p className="overall-summary">{match.overall_summary}</p>
                      {match.assignments && match.assignments.length > 0 && (
                        <ul className="assignment-list">
                          {match.assignments.map((assignment, index) => (
                            <li key={`${assignment.project_name}-${index}`} className="assignment-card">
                              <div className="assignment-header">
                                <strong>{assignment.project_name}</strong>
                                <span className={`confidence-pill ${assignment.confidence?.toLowerCase()}`}>
                                  {assignment.confidence}
                                </span>
                              </div>
                              <p>{assignment.fit_explanation}</p>
                            </li>
                          ))}
                        </ul>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </article>
          </div>
        </section>
      </main>

      <footer>
        <p>© {new Date().getFullYear()} Penn × Anthropic Emp Matching</p>
      </footer>
    </div>
  );
}

export default App;
