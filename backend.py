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
