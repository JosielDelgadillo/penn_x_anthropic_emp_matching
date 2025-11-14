# Penn × Anthropic Empowerment Matching

A landing page for the Penn × Anthropic Empowerment Matching (PXAE) initiative—a student-led program helping the Penn community explore responsible AI development.

## About the Initiative

PXAE connects Penn students with Anthropic experts through:

- **Workshops**: Weekly deep dives into frontier models, alignment, safety strategy, and practical tooling
- **Mentorship**: Small-group circles with Anthropic researchers and alumni for project guidance and career advice
- **Impact Projects**: Interdisciplinary teams building solutions for civic partners

## Tech Stack

### Frontend
- React 19.2.0
- Create React App 5.0.1
- Pure CSS styling

### Backend (GitHub Profiler)
- Python 3.9+
- FastAPI - Modern web framework
- PyGithub - GitHub API integration
- Anthropic Claude API - AI-powered profile generation
- Uvicorn - ASGI server

## Getting Started

### Frontend Setup

#### Installation

```bash
npm install
```

#### Development

```bash
npm start
```

Runs the app in development mode at [http://localhost:3000](http://localhost:3000).

### Backend Setup (GitHub Profiler Feature)

#### 1. Install Python Dependencies

```bash
pip3 install -r requirements.txt
```

#### 2. Configure API Keys

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Then edit `.env` and add your API keys:

```
GITHUB_TOKEN=ghp_your_github_personal_access_token
ANTHROPIC_API_KEY=sk-ant-your_anthropic_api_key
```

**Get your keys:**
- **GitHub Token**: https://github.com/settings/tokens (create a personal access token)
- **Anthropic API Key**: https://console.anthropic.com/settings/keys

#### 3. Run the Backend Server

```bash
python3 -m uvicorn backend:app --reload
```

Server will start at: http://localhost:8000

#### 4. Use the Profiler

With both frontend (port 3000) and backend (port 8000) running:
1. Navigate to the "Profiler" section in the app
2. Paste GitHub repository URLs (one per line)
3. Click "Generate Profiles" and wait 30-90 seconds
4. Search profiles using natural language queries like:
   - "Who knows about machine learning?"
   - "Find someone good at frontend work"
   - "Who writes comprehensive tests?"

### Build

```bash
npm run build
```

Builds the app for production to the `build` folder.

### Testing

```bash
npm test
```

Runs the test suite in interactive watch mode.

## Project Structure

```
penn_x_anthropic_emp_matching/
├── src/
│   ├── App.js              # Main React component with all sections
│   ├── App.css             # All styling including profiler
│   ├── index.js            # React entry point
│   └── [tests/setup]       # Testing configuration
├── backend.py              # FastAPI server for GitHub profiler
├── requirements.txt        # Python dependencies
├── .env.example            # Environment variables template
├── .env                    # Your API keys (not committed to git)
├── profiles.json           # Generated profiles (not committed to git)
└── package.json            # Node dependencies
```

## Features

### GitHub Developer Profiler 🆕

An AI-powered tool that analyzes GitHub repositories to automatically generate developer profiles:

- **Repository Analysis**: Extracts commit history, code patterns, and work styles
- **AI Profile Generation**: Uses Claude to create comprehensive developer profiles
- **Smart Search**: Natural language queries to find developers with specific expertise
- **Skills Detection**: Automatically identifies programming languages, frameworks, and expertise areas
- **Work Style Analysis**: Understands commit patterns and collaboration approaches

**Use Cases:**
- Find team members for specific projects
- Identify subject matter experts in your organization
- Understand developer strengths and work styles
- Build better teams based on complementary skills

### Roadmap

- [x] GitHub Developer Profiler with AI-powered analysis
- [ ] Email signup form integration
- [ ] Event calendar/schedule
- [ ] Speaker and mentor profiles
- [ ] Project showcase gallery
- [ ] Application portal
- [ ] Deployment to production

## Contributing

This is a collaborative project. Please coordinate changes via pull requests and discuss major architectural decisions with the team.

## API Endpoints (Backend)

When the backend is running, these endpoints are available:

- `GET /` - Health check and API documentation
- `POST /analyze` - Analyze GitHub repositories and generate profiles
- `GET /profiles` - Retrieve all generated profiles
- `GET /search?query=<query>` - Search developers using natural language

## Deployment

### Frontend Only (Base Landing Page)
This React app can be deployed to static hosting services like:
- Vercel
- Netlify
- GitHub Pages

No environment variables or backend dependencies required for the base landing page.

### Full Stack (With Profiler)
For deploying with the GitHub Profiler feature:
- **Frontend**: Vercel, Netlify, or any static host
- **Backend**: Railway, Render, or any Python hosting service
- **Environment Variables**: Set `GITHUB_TOKEN` and `ANTHROPIC_API_KEY` in your hosting platform
- **CORS**: Update `allow_origins` in `backend.py` for production domains

## Troubleshooting

### Backend Issues

**"Missing API keys" error:**
- Ensure `.env` file exists in the project root with valid keys
- Check that key names match exactly: `GITHUB_TOKEN` and `ANTHROPIC_API_KEY`

**GitHub rate limit:**
- Use an authenticated token (increases limit to 5000 requests/hour)
- Public API without token: 60 requests/hour

**No profiles showing:**
- Verify backend is running on port 8000
- Check browser console for error messages
- Ensure both frontend and backend are running simultaneously

**Connection refused:**
- Make sure uvicorn server is running: `python3 -m uvicorn backend:app --reload`
- Check that port 8000 is not being used by another application

## Contact

For questions about the initiative: pxae@penn.edu

---

Built with Create React App. See [CRA documentation](https://create-react-app.dev/) for additional details.
