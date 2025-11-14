import { useCallback } from 'react';
import './App.css';

const navItems = [
  { label: 'Overview', href: '#overview' },
  { label: 'Program', href: '#program' },
  { label: 'Get Involved', href: '#interest' },
];

function App() {
  const handleHelloClick = useCallback(async () => {
    try {
      const response = await fetch('/api/hello');
      if (!response.ok) {
        throw new Error('Request to /api/hello failed');
      }
      const data = await response.json();
      // eslint-disable-next-line no-console
      console.log('Backend says:', data.message);
    } catch (error) {
      // eslint-disable-next-line no-console
      console.error('Unable to fetch hello message', error);
    }
  }, []);

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
          <button type="button" className="cta-link primary cta-button" onClick={handleHelloClick}>
            Say hello
          </button>
          <p className="console-note">Click the button and check the console for the backend message.</p>
        </section>
      </main>

      <footer>
        <p>© {new Date().getFullYear()} Penn × Anthropic Emp Matching Initiative</p>
      </footer>
    </div>
  );
}

export default App;
