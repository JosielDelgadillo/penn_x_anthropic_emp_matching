# GitHub Developer Profiler - MVP Build Specification

## Project Overview
Build a system that analyzes GitHub repositories to automatically generate AI-powered developer profiles. The system extracts commit history, code patterns, and work styles to create searchable developer profiles without manual data entry.

## Time Estimate
2 hours to fully functional MVP

---

## Tech Stack

- **Backend**: Python 3.11+ with FastAPI
- **GitHub Integration**: PyGithub library
- **LLM**: Anthropic Claude API (Sonnet 4)
- **Frontend**: Single HTML file with vanilla JS + Tailwind CSS
- **Storage**: JSON file (no database needed for MVP)
- **Server**: Uvicorn

---

## Project Structure

```
github-profiler-mvp/
├── backend.py           # FastAPI server with all logic
├── profiles.json        # Generated developer profiles (auto-created)
├── index.html          # Single-page UI
├── .env                # API keys (create manually)
├── .gitignore          # Exclude .env and profiles.json
├── requirements.txt    # Python dependencies
└── README.md          # Setup instructions
```

---

## Dependencies (requirements.txt)

```
fastapi==0.104.1
uvicorn[standard]==0.24.0
PyGithub==2.1.1
anthropic==0.7.8
python-dotenv==1.0.0
```

---

## Environment Variables (.env)

```
GITHUB_TOKEN=ghp_your_github_personal_access_token_here
ANTHROPIC_API_KEY=sk-ant-your_anthropic_api_key_here
```

**Note**: User must create this file manually with their actual API keys.

---

## Backend Implementation (backend.py)

### Complete Backend Code

```python
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from github import Github
import anthropic
import json
from collections import Counter
from datetime import datetime
import os
from dotenv import load_dotenv
from typing import List

# Load environment variables
load_dotenv()

app = FastAPI(title="GitHub Developer Profiler")

# CORS middleware for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize clients
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
ANTHROPIC_KEY = os.getenv("ANTHROPIC_API_KEY")

if not GITHUB_TOKEN or not ANTHROPIC_KEY:
    raise Exception("Missing API keys in .env file")

github_client = Github(GITHUB_TOKEN)
claude_client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)

PROFILES_FILE = "profiles.json"


def extract_repo_name(url: str) -> str:
    """Extract owner/repo from GitHub URL"""
    # Handle various URL formats
    url = url.strip().rstrip('/')
    if url.startswith('http'):
        parts = url.split('github.com/')[-1].split('/')
        return f"{parts[0]}/{parts[1]}"
    return url


def detect_language(filename: str) -> str:
    """Detect programming language from file extension"""
    ext_map = {
        ".py": "Python",
        ".js": "JavaScript",
        ".ts": "TypeScript",
        ".jsx": "React",
        ".tsx": "React",
        ".java": "Java",
        ".go": "Go",
        ".rs": "Rust",
        ".cpp": "C++",
        ".c": "C",
        ".rb": "Ruby",
        ".php": "PHP",
        ".swift": "Swift",
        ".kt": "Kotlin",
        ".scala": "Scala",
        ".sql": "SQL",
        ".sh": "Shell",
        ".yml": "YAML",
        ".yaml": "YAML",
        ".json": "JSON",
        ".md": "Markdown",
    }
    for ext, lang in ext_map.items():
        if filename.endswith(ext):
            return lang
    return None


def analyze_repository(repo_url: str) -> List[dict]:
    """
    Scrape GitHub repository and build developer profiles
    """
    try:
        repo_name = extract_repo_name(repo_url)
        repo = github_client.get_repo(repo_name)
        
        print(f"Analyzing repository: {repo.full_name}")
        
        # Get commits (limit to 100 for speed)
        commits = list(repo.get_commits()[:100])
        
        # Group data by author
        author_data = {}
        
        for commit in commits:
            if not commit.author:
                continue
                
            author = commit.author.login
            
            if author not in author_data:
                author_data[author] = {
                    "name": commit.author.name or author,
                    "avatar_url": commit.author.avatar_url,
                    "commits": [],
                    "files_changed": [],
                    "languages": Counter(),
                    "commit_times": [],
                }
            
            # Store commit details
            author_data[author]["commits"].append({
                "message": commit.commit.message,
                "date": str(commit.commit.author.date),
                "additions": commit.stats.additions,
                "deletions": commit.stats.deletions,
            })
            
            author_data[author]["commit_times"].append(commit.commit.author.date.hour)
            
            # Analyze files in commit
            try:
                for file in commit.files:
                    author_data[author]["files_changed"].append(file.filename)
                    lang = detect_language(file.filename)
                    if lang:
                        author_data[author]["languages"][lang] += 1
            except:
                # Some commits may not have file details
                pass
        
        # Generate profiles using Claude
        profiles = []
        for username, data in author_data.items():
            if len(data["commits"]) < 2:  # Skip developers with <2 commits
                continue
            profile = generate_profile(username, data, repo.name)
            profiles.append(profile)
        
        return profiles
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error analyzing repository: {str(e)}")


def generate_profile(username: str, commit_data: dict, repo_name: str) -> dict:
    """
    Use Claude to analyze commit patterns and generate developer profile
    """
    
    # Prepare context for Claude
    recent_messages = [c["message"] for c in commit_data["commits"][:20]]
    top_languages = commit_data["languages"].most_common(5)
    file_paths = list(set(commit_data["files_changed"][:40]))
    
    # Calculate work patterns
    avg_additions = sum(c["additions"] for c in commit_data["commits"]) / len(commit_data["commits"])
    avg_deletions = sum(c["deletions"] for c in commit_data["commits"]) / len(commit_data["commits"])
    
    context = f"""Developer: {username}
Repository: {repo_name}
Total Commits: {len(commit_data["commits"])}
Average Lines Added per Commit: {avg_additions:.0f}
Average Lines Deleted per Commit: {avg_deletions:.0f}
Top Languages: {", ".join([f"{lang} ({count} files)" for lang, count in top_languages])}

Recent Commit Messages:
{chr(10).join(['- ' + msg.split(chr(10))[0][:100] for msg in recent_messages])}

Sample File Paths Modified:
{chr(10).join(['- ' + path for path in file_paths[:20]])}
"""
    
    prompt = f"""Analyze this developer's GitHub activity and create a comprehensive profile.

{context}

Based on the commit messages, file paths, and patterns, generate a JSON profile with these exact fields:

{{
  "expertise_areas": ["list 3-5 specific technical areas based on files and commits"],
  "frameworks": ["infer 2-4 frameworks/libraries from file paths and commit messages"],
  "work_style": "2-4 word description of their coding style (e.g., 'methodical test-driven', 'rapid iterative prototyping', 'documentation-focused maintainer')",
  "commit_pattern": "describe their commit habits in one sentence",
  "ai_summary": "Write a 2-3 sentence professional profile highlighting their technical strengths and work approach",
  "best_for": ["3-4 specific things they'd be excellent to consult on based on their work"]
}}

Rules:
- Be specific and evidence-based (cite file types, commit patterns)
- Infer frameworks from import statements in commits or config files
- Identify expertise from directory structure (e.g., /auth/* = authentication, /ml/* = machine learning)
- Keep descriptions professional and actionable

CRITICAL: Return ONLY valid JSON. DO NOT include markdown code blocks, explanations, or any text outside the JSON object.
"""
    
    try:
        response = claude_client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1200,
            messages=[{"role": "user", "content": prompt}]
        )
        
        # Parse Claude's response
        response_text = response.content[0].text.strip()
        
        # Remove markdown code blocks if present
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
        
        profile_data = json.loads(response_text)
        
        # Merge with basic data
        full_profile = {
            "github_username": username,
            "name": commit_data["name"],
            "avatar_url": commit_data["avatar_url"],
            "total_commits": len(commit_data["commits"]),
            "primary_languages": [lang for lang, _ in top_languages[:3]],
            "repo_analyzed": repo_name,
            **profile_data
        }
        
        return full_profile
    
    except Exception as e:
        print(f"Error generating profile for {username}: {e}")
        # Return basic profile if Claude fails
        return {
            "github_username": username,
            "name": commit_data["name"],
            "avatar_url": commit_data["avatar_url"],
            "total_commits": len(commit_data["commits"]),
            "primary_languages": [lang for lang, _ in top_languages[:3]],
            "expertise_areas": ["Code contribution"],
            "frameworks": [],
            "work_style": "active contributor",
            "commit_pattern": f"Made {len(commit_data['commits'])} commits",
            "ai_summary": f"Active contributor to {repo_name}",
            "best_for": ["Code review", "Technical questions"],
            "repo_analyzed": repo_name,
        }


def load_profiles() -> List[dict]:
    """Load profiles from JSON file"""
    try:
        with open(PROFILES_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []


def save_profiles(profiles: List[dict]):
    """Save profiles to JSON file"""
    with open(PROFILES_FILE, 'w') as f:
        json.dump(profiles, f, indent=2)


@app.post("/analyze")
async def analyze_repos(repos: List[str]):
    """
    Analyze GitHub repositories and generate developer profiles
    
    Input: List of GitHub repository URLs
    Output: Generated developer profiles
    """
    all_profiles = {}
    
    for repo_url in repos:
        if not repo_url.strip():
            continue
            
        print(f"\nAnalyzing: {repo_url}")
        profiles = analyze_repository(repo_url)
        
        # Merge profiles if same developer appears in multiple repos
        for profile in profiles:
            username = profile["github_username"]
            if username in all_profiles:
                # Update with more commits
                all_profiles[username]["total_commits"] += profile["total_commits"]
                # Merge expertise areas
                existing_areas = set(all_profiles[username]["expertise_areas"])
                new_areas = set(profile["expertise_areas"])
                all_profiles[username]["expertise_areas"] = list(existing_areas | new_areas)[:5]
            else:
                all_profiles[username] = profile
    
    # Save all profiles
    profiles_list = list(all_profiles.values())
    save_profiles(profiles_list)
    
    return {
        "success": True,
        "profiles_generated": len(profiles_list),
        "profiles": profiles_list
    }


@app.get("/profiles")
async def get_profiles():
    """Return all generated developer profiles"""
    profiles = load_profiles()
    return {"profiles": profiles, "count": len(profiles)}


@app.get("/search")
async def search_profiles(query: str):
    """
    Search for developers using natural language query
    
    Uses Claude to semantically match query against profiles
    """
    profiles = load_profiles()
    
    if not profiles:
        return {"matches": [], "message": "No profiles available. Analyze repositories first."}
    
    prompt = f"""You are a developer matching system. Given a search query and developer profiles, identify the top 3 most relevant developers.

Query: "{query}"

Developer Profiles:
{json.dumps(profiles, indent=2)}

Analyze each profile and return the top 3 matches based on:
1. Technical expertise matching the query
2. Relevant frameworks and languages
3. Work style alignment if mentioned in query
4. Domain expertise from their file paths and commits

Return ONLY valid JSON in this exact format:
[
  {{
    "github_username": "username",
    "relevance_score": 95,
    "match_reason": "Specific reason they match the query (cite their expertise, languages, or work)"
  }}
]

If fewer than 3 profiles match well, return only the good matches.

CRITICAL: Return ONLY valid JSON array. DO NOT include markdown, explanations, or any text outside the JSON.
"""
    
    try:
        response = claude_client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        response_text = response.content[0].text.strip()
        
        # Remove markdown if present
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
        
        matches = json.loads(response_text)
        
        # Enrich with full profile data
        result = []
        for match in matches:
            full_profile = next(
                (p for p in profiles if p["github_username"] == match["github_username"]),
                None
            )
            if full_profile:
                result.append({**full_profile, **match})
        
        return {"matches": result, "query": query}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "running",
        "message": "GitHub Developer Profiler API",
        "endpoints": {
            "POST /analyze": "Analyze GitHub repositories",
            "GET /profiles": "Get all profiles",
            "GET /search?query=<query>": "Search for developers"
        }
    }
```

---

## Frontend Implementation (index.html)

### Complete Frontend Code

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GitHub Developer Profiler</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gradient-to-br from-gray-50 to-gray-100 min-h-screen">
    <div class="max-w-7xl mx-auto p-8">
        <!-- Header -->
        <div class="mb-12 text-center">
            <h1 class="text-5xl font-bold text-gray-800 mb-3">GitHub Developer Profiler</h1>
            <p class="text-gray-600 text-lg">AI-powered developer profiles from repository analysis</p>
        </div>
        
        <!-- Step 1: Analyze Repositories -->
        <div class="bg-white rounded-xl shadow-lg p-8 mb-8">
            <div class="flex items-center mb-6">
                <span class="bg-blue-500 text-white rounded-full w-8 h-8 flex items-center justify-center font-bold mr-3">1</span>
                <h2 class="text-2xl font-bold text-gray-800">Analyze Repositories</h2>
            </div>
            
            <textarea 
                id="repoInput" 
                placeholder="Paste GitHub repository URLs (one per line)&#10;&#10;Example:&#10;https://github.com/fastapi/fastapi&#10;https://github.com/anthropics/anthropic-sdk-python"
                class="w-full p-4 border-2 border-gray-200 rounded-lg mb-4 font-mono text-sm focus:border-blue-500 focus:outline-none"
                rows="6"
            ></textarea>
            
            <button 
                onclick="analyzeRepos()"
                id="analyzeBtn"
                class="bg-blue-500 text-white px-8 py-3 rounded-lg hover:bg-blue-600 transition font-semibold shadow-md hover:shadow-lg"
            >
                🔍 Generate Profiles
            </button>
            
            <div id="status" class="mt-4 p-4 rounded-lg hidden"></div>
        </div>
        
        <!-- Step 2: Search Developers -->
        <div class="bg-white rounded-xl shadow-lg p-8 mb-8">
            <div class="flex items-center mb-6">
                <span class="bg-green-500 text-white rounded-full w-8 h-8 flex items-center justify-center font-bold mr-3">2</span>
                <h2 class="text-2xl font-bold text-gray-800">Search Developers</h2>
            </div>
            
            <div class="flex gap-3">
                <input 
                    id="searchInput"
                    placeholder="Who can help with machine learning? Who writes good tests? Who's a React expert?"
                    class="flex-1 p-4 border-2 border-gray-200 rounded-lg focus:border-green-500 focus:outline-none"
                    onkeypress="if(event.key==='Enter') searchDevelopers()"
                />
                <button 
                    onclick="searchDevelopers()"
                    class="bg-green-500 text-white px-8 py-3 rounded-lg hover:bg-green-600 transition font-semibold shadow-md hover:shadow-lg"
                >
                    Search
                </button>
            </div>
        </div>
        
        <!-- Results Grid -->
        <div id="results" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"></div>
        
        <!-- Empty State -->
        <div id="emptyState" class="text-center py-16 text-gray-400">
            <svg class="w-24 h-24 mx-auto mb-4 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"></path>
            </svg>
            <p class="text-xl">No profiles yet. Start by analyzing a repository!</p>
        </div>
    </div>

    <script>
        const API_BASE = 'http://localhost:8000';
        
        // Check if profiles exist on load
        window.onload = async () => {
            try {
                const response = await fetch(`${API_BASE}/profiles`);
                const data = await response.json();
                if (data.profiles && data.profiles.length > 0) {
                    displayProfiles(data.profiles);
                }
            } catch (error) {
                console.log('No existing profiles or server not running');
            }
        };
        
        async function analyzeRepos() {
            const input = document.getElementById('repoInput').value;
            const repos = input.split('\n').filter(r => r.trim());
            
            if (repos.length === 0) {
                showStatus('Please enter at least one repository URL', 'error');
                return;
            }
            
            const btn = document.getElementById('analyzeBtn');
            btn.disabled = true;
            btn.textContent = '⏳ Analyzing...';
            
            showStatus(`Analyzing ${repos.length} repositor${repos.length > 1 ? 'ies' : 'y'}... This may take 30-90 seconds`, 'loading');
            
            try {
                const response = await fetch(`${API_BASE}/analyze`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(repos)
                });
                
                if (!response.ok) {
                    throw new Error('Analysis failed');
                }
                
                const data = await response.json();
                showStatus(`✅ Success! Generated ${data.profiles_generated} developer profile${data.profiles_generated !== 1 ? 's' : ''}`, 'success');
                displayProfiles(data.profiles);
                
            } catch (error) {
                showStatus(`❌ Error: ${error.message}. Check console for details.`, 'error');
                console.error('Error:', error);
            } finally {
                btn.disabled = false;
                btn.textContent = '🔍 Generate Profiles';
            }
        }
        
        async function searchDevelopers() {
            const query = document.getElementById('searchInput').value.trim();
            
            if (!query) {
                showStatus('Please enter a search query', 'error');
                return;
            }
            
            showStatus('🔍 Searching...', 'loading');
            
            try {
                const response = await fetch(`${API_BASE}/search?query=${encodeURIComponent(query)}`);
                const data = await response.json();
                
                if (data.matches && data.matches.length > 0) {
                    showStatus(`Found ${data.matches.length} matching developer${data.matches.length !== 1 ? 's' : ''}`, 'success');
                    displayProfiles(data.matches, true);
                } else {
                    showStatus('No matches found. Try a different query.', 'error');
                }
                
            } catch (error) {
                showStatus(`Search error: ${error.message}`, 'error');
                console.error('Error:', error);
            }
        }
        
        function displayProfiles(profiles, showMatch = false) {
            document.getElementById('emptyState').style.display = 'none';
            
            const html = profiles.map(p => `
                <div class="bg-white rounded-xl shadow-lg hover:shadow-xl transition p-6 border-2 border-gray-100 hover:border-blue-200">
                    <!-- Header -->
                    <div class="flex items-start gap-4 mb-4">
                        <img 
                            src="${p.avatar_url}" 
                            alt="${p.github_username}"
                            class="w-16 h-16 rounded-full border-2 border-gray-200"
                        >
                        <div class="flex-1 min-w-0">
                            <h3 class="text-xl font-bold text-gray-800 truncate">${p.name || p.github_username}</h3>
                            <a 
                                href="https://github.com/${p.github_username}" 
                                target="_blank"
                                class="text-sm text-blue-600 hover:underline"
                            >
                                @${p.github_username}
                            </a>
                        </div>
                    </div>
                    
                    <!-- Match Reason (if search result) -->
                    ${showMatch && p.match_reason ? `
                        <div class="bg-green-50 border-l-4 border-green-500 p-3 mb-4 rounded">
                            <p class="text-sm text-green-800">
                                <span class="font-semibold">Match:</span> ${p.match_reason}
                            </p>
                        </div>
                    ` : ''}
                    
                    <!-- AI Summary -->
                    <p class="text-sm text-gray-700 mb-4 leading-relaxed">${p.ai_summary}</p>
                    
                    <!-- Languages -->
                    <div class="mb-3">
                        <span class="text-xs font-semibold text-gray-500 uppercase">Languages</span>
                        <div class="flex flex-wrap gap-2 mt-2">
                            ${p.primary_languages.map(l => `
                                <span class="bg-blue-100 text-blue-800 text-xs px-3 py-1 rounded-full font-medium">
                                    ${l}
                                </span>
                            `).join('')}
                        </div>
                    </div>
                    
                    <!-- Expertise -->
                    <div class="mb-3">
                        <span class="text-xs font-semibold text-gray-500 uppercase">Expertise</span>
                        <div class="mt-2 text-sm text-gray-700">
                            ${p.expertise_areas.slice(0, 3).join(' • ')}
                        </div>
                    </div>
                    
                    <!-- Best For -->
                    ${p.best_for ? `
                        <div class="mb-3">
                            <span class="text-xs font-semibold text-gray-500 uppercase">Best For</span>
                            <ul class="mt-2 text-sm text-gray-700 space-y-1">
                                ${p.best_for.slice(0, 3).map(item => `
                                    <li class="flex items-start">
                                        <span class="text-green-500 mr-2">✓</span>
                                        <span>${item}</span>
                                    </li>
                                `).join('')}
                            </ul>
                        </div>
                    ` : ''}
                    
                    <!-- Footer Stats -->
                    <div class="pt-3 border-t border-gray-200 mt-4 flex items-center justify-between text-xs text-gray-500">
                        <span>📊 ${p.total_commits} commits</span>
                        <span class="italic">${p.work_style}</span>
                    </div>
                </div>
            `).join('');
            
            document.getElementById('results').innerHTML = html;
        }
        
        function showStatus(message, type) {
            const statusEl = document.getElementById('status');
            statusEl.className = `mt-4 p-4 rounded-lg ${
                type === 'error' ? 'bg-red-50 text-red-700 border border-red-200' :
                type === 'success' ? 'bg-green-50 text-green-700 border border-green-200' :
                'bg-blue-50 text-blue-700 border border-blue-200'
            }`;
            statusEl.textContent = message;
            statusEl.classList.remove('hidden');
            
            if (type === 'success') {
                setTimeout(() => statusEl.classList.add('hidden'), 5000);
            }
        }
    </script>
</body>
</html>
```

---

## Setup Instructions (README.md)

```markdown
# GitHub Developer Profiler

AI-powered developer profile generation from GitHub repository analysis.

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure API Keys

Create a `.env` file in the project root:

```
GITHUB_TOKEN=ghp_your_github_personal_access_token
ANTHROPIC_API_KEY=sk-ant-your_anthropic_api_key
```

**Get your keys:**
- GitHub: https://github.com/settings/tokens (create a personal access token)
- Anthropic: https://console.anthropic.com/settings/keys

### 3. Run the Server

```bash
uvicorn backend:app --reload
```

Server will start at: http://localhost:8000

### 4. Open the UI

Open `index.html` in your browser or serve it:

```bash
python -m http.server 8080
```

Then visit: http://localhost:8080

## Usage

1. **Analyze Repositories**: Paste GitHub repo URLs (one per line) and click "Generate Profiles"
2. **Wait 30-90 seconds** for analysis to complete
3. **Search**: Use natural language queries like:
   - "Who knows about machine learning?"
   - "Find someone good at frontend work"
   - "Who writes comprehensive tests?"

## Example Repositories to Test

```
https://github.com/fastapi/fastapi
https://github.com/anthropics/anthropic-sdk-python
https://github.com/vercel/next.js
```

## Architecture

- **Backend**: FastAPI server that scrapes GitHub and uses Claude for analysis
- **LLM**: Claude Sonnet 4 analyzes commit patterns to generate profiles
- **Storage**: Simple JSON file (profiles.json)
- **Frontend**: Vanilla JavaScript with Tailwind CSS

## API Endpoints

- `POST /analyze` - Analyze repositories
- `GET /profiles` - Get all profiles
- `GET /search?query=<query>` - Search developers

## Troubleshooting

**"Missing API keys" error:**
- Ensure `.env` file exists with valid keys

**GitHub rate limit:**
- Use an authenticated token (increases limit to 5000/hour)

**No profiles showing:**
- Check that backend is running on port 8000
- Open browser console for error messages
```

---

## .gitignore

```
.env
profiles.json
__pycache__/
*.pyc
.DS_Store
venv/
env/
```

---

## Build Instructions for Claude Code

### Phase 1: Project Setup (5 min)
1. Create the project directory structure
2. Generate all files: `backend.py`, `index.html`, `requirements.txt`, `README.md`, `.gitignore`
3. Create empty `.env` file with placeholder comments

### Phase 2: Dependencies (2 min)
1. Install Python packages from `requirements.txt`
2. Verify installations

### Phase 3: Testing (3 min)
1. Start the FastAPI server: `uvicorn backend:app --reload`
2. Test root endpoint: `curl http://localhost:8000`
3. Open `index.html` in browser

### Phase 4: End-to-End Test (10 min)
1. Add actual API keys to `.env`
2. Test with a small repo (e.g., `https://github.com/anthropics/anthropic-sdk-python`)
3. Verify profile generation
4. Test search functionality

---

## Expected Results

After analyzing 1-2 repositories, you should see:

- **Developer cards** with avatars, names, and GitHub links
- **AI-generated summaries** describing their coding style
- **Language tags** showing their primary tech stack
- **Expertise areas** inferred from their commits
- **Work style** descriptions (e.g., "methodical test-driven")
- **Search results** that accurately match queries to developers

---

## Next Steps After MVP

1. Add support for private repositories
2. Analyze pull request reviews for collaboration patterns
3. Track skill evolution over time
4. Generate team skill matrices
5. Build manager dashboard for team insights
6. Add Slack/email notifications for expert recommendations

---

## Success Criteria

✅ Generates profiles from GitHub commits  
✅ Claude accurately extracts skills and expertise  
✅ Search returns relevant developers  
✅ UI is clean and functional  
✅ Takes <2 hours to build and run  

---

## Technical Notes

- **Rate Limits**: GitHub API has 5000 req/hour with auth token
- **Commit Limit**: MVP analyzes last 100 commits per repo for speed
- **Profile Quality**: Improves with more commits per developer
- **Search Accuracy**: Claude's semantic matching works best with 5+ profiles

---

## Support

This is an MVP. For production use, consider:
- Database instead of JSON
- Background job processing for large repos
- Caching layer for repeated queries
- Authentication and authorization
- Error monitoring (Sentry)
- Deployment (Docker + cloud hosting)
