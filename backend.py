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

# Demo mode: runs without API keys using sample data
DEMO_MODE = not (GITHUB_TOKEN and ANTHROPIC_KEY)

if DEMO_MODE:
    print("⚠️  Running in DEMO MODE - No API keys found. Using sample data.")
    print("   To enable real API: Create .env file with GITHUB_TOKEN and ANTHROPIC_API_KEY")
    github_client = None
    claude_client = None
else:
    github_client = Github(GITHUB_TOKEN)
    try:
        claude_client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
    except Exception as exc:
        print(f"Error initializing Claude client: {exc}")
        claude_client = None

PROFILES_FILE = "profiles.json"
DEMO_PROFILES_FILE = "demo_profiles.json"
PERSONAL_FILE = "personal.json"
PROJECTS_FILE = "projects.json"


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

    claude = get_claude_client()
    try:
        response = claude.messages.create(
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
    if DEMO_MODE:
        # In demo mode, always return demo profiles
        try:
            with open(DEMO_PROFILES_FILE, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return []

    try:
        with open(PROFILES_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []


def get_claude_client():
    """Return a ready anthropic client or raise if unavailable."""
    global claude_client

    if claude_client:
        return claude_client

    if not ANTHROPIC_KEY:
        raise HTTPException(status_code=503, detail="Anthropic API key not configured.")

    try:
        claude_client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
        return claude_client
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Failed to initialize Claude client: {exc}")


def load_json_records(filename: str, key: str) -> List[dict]:
    """
    Load list-type records from a JSON file.

    Args:
        filename: Relative path of the JSON file.
        key: Key expected to hold the list in the JSON payload.
    """
    try:
        with open(filename, 'r') as f:
            data = json.load(f)
            if key:
                return data.get(key, [])
            return data
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"{filename} not found. Add the file to use this endpoint.")
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=500, detail=f"Error parsing {filename}: {exc}")


def load_personas() -> List[dict]:
    """Return personas from personal.json"""
    return load_json_records(PERSONAL_FILE, "personas")


def load_projects() -> List[dict]:
    """Return projects from projects.json"""
    return load_json_records(PROJECTS_FILE, "projects")


def summarize_persona(persona: dict) -> dict:
    """Extract concise persona context for Claude prompts."""
    survey_answers = [resp.get("answer") for resp in persona.get("survey", {}).get("responses", []) if resp.get("answer")]
    return {
        "id": persona.get("id"),
        "name": persona.get("full_name"),
        "headline": persona.get("resume", {}).get("headline"),
        "current_role": persona.get("resume", {}).get("current_role"),
        "target_roles": persona.get("application", {}).get("target_roles", []),
        "preferred_locations": persona.get("application", {}).get("preferred_locations", []),
        "skills": persona.get("resume", {}).get("skills", []),
        "domains": persona.get("resume", {}).get("domains", []),
        "interests": survey_answers,
        "work_style": next(
            (
                resp.get("answer")
                for resp in persona.get("survey", {}).get("responses", [])
                if "working style" in resp.get("question", "").lower()
            ),
            ""
        )
    }


def summarize_project(project: dict) -> dict:
    """Extract concise project details for Claude prompts."""
    return {
        "name": project.get("project_name"),
        "description": project.get("Description"),
        "core_features": project.get("core_features", []),
        "architecture_stack": project.get("architecture_stack", {}),
        "data_model_and_pipeline": project.get("data_model_and_pipeline", {}),
        "api_endpoints": project.get("api_endpoints", []),
        "prompt_engineering": project.get("prompt_engineering", {}),
        "acceptance_criteria": project.get("acceptance_criteria", []),
        "notes": project.get("notes", "")
    }


def run_claude_matching(client, personas: List[dict], projects: List[dict]) -> List[dict]:
    """Call Claude to match personas to projects with explanations."""
    persona_summaries = [summarize_persona(p) for p in personas]
    project_summaries = [summarize_project(p) for p in projects]

    prompt = f"""You are a staffing AI that pairs candidates to innovation projects.

Personas:
{json.dumps(persona_summaries, indent=2)}

Projects:
{json.dumps(project_summaries, indent=2)}

For every persona, choose the 1-3 best-fit projects. Cite concrete evidence from their skills, interests, or work style and the project requirements.

Return ONLY valid JSON with this exact shape:
[
  {{
    "persona_id": "id",
    "persona_name": "name",
    "assignments": [
      {{
        "project_name": "Project",
        "fit_explanation": "2-3 sentences explaining the match referencing persona + project data",
        "confidence": "High|Medium|Low"
      }}
    ],
    "overall_summary": "Sentence summarizing how this persona fits the recommended projects."
  }}
]

Rules:
- Keep explanations professional and evidence-based.
- Mention overlapping skills, domains, or interests explicitly.
- If a project is a stretch fit, explain what support they would need.
- Never invent new personas or projects.
"""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1200,
        messages=[{"role": "user", "content": prompt}]
    )

    response_text = response.content[0].text.strip()

    if response_text.startswith("```"):
        response_text = response_text.split("```")[1]
        if response_text.startswith("json"):
            response_text = response_text[4:]

    return json.loads(response_text)


def _project_text_blob(project: dict) -> str:
    """Construct a lowercase text blob for rule-based scoring."""
    sections = [
        project.get("project_name", ""),
        project.get("Description", ""),
        " ".join(project.get("core_features", [])),
        json.dumps(project.get("architecture_stack", {})),
        json.dumps(project.get("data_model_and_pipeline", {})),
        " ".join(project.get("acceptance_criteria", [])),
        project.get("notes", "")
    ]
    return " ".join(sections).lower()


def _rule_based_match(personas: List[dict], projects: List[dict]) -> List[dict]:
    """Fallback matcher when Claude is unavailable."""
    project_blobs = {proj.get("project_name"): _project_text_blob(proj) for proj in projects}
    results = []

    for persona in personas:
        persona_skills = [skill.lower() for skill in persona.get("resume", {}).get("skills", [])]
        persona_domains = [domain.lower() for domain in persona.get("resume", {}).get("domains", [])]
        persona_targets = [role.lower() for role in persona.get("application", {}).get("target_roles", [])]

        scored_projects = []
        for project in projects:
            blob = project_blobs.get(project.get("project_name"), "")
            skill_overlap = [skill for skill in persona_skills if skill in blob]
            domain_overlap = [domain for domain in persona_domains if domain in blob]
            role_overlap = [role for role in persona_targets if role in blob]
            score = len(skill_overlap) * 2 + len(domain_overlap) + len(role_overlap)
            scored_projects.append((project, score, skill_overlap, domain_overlap))

        scored_projects.sort(key=lambda item: item[1], reverse=True)
        top_projects = scored_projects[:3] if scored_projects else []

        assignments = []
        for project, score, skill_overlap, domain_overlap in top_projects:
            explanation_bits = []
            if skill_overlap:
                explanation_bits.append(f"skills match: {', '.join(set(skill_overlap))}")
            if domain_overlap:
                explanation_bits.append(f"domain experience in {', '.join(set(domain_overlap))}")
            if not explanation_bits:
                explanation_bits.append("relevant interests based on target roles and general experience")
            confidence = "High" if score >= 6 else "Medium" if score >= 3 else "Low"
            assignments.append({
                "project_name": project.get("project_name"),
                "fit_explanation": f"Rule-based match ({'; '.join(explanation_bits)}).",
                "confidence": confidence
            })

        results.append({
            "persona_id": persona.get("id"),
            "persona_name": persona.get("full_name"),
            "assignments": assignments or [],
            "overall_summary": "Rule-based recommendation generated because Claude was unavailable."
        })

    return results


def save_profiles(profiles: List[dict]):
    """Save profiles to JSON file"""
    with open(PROFILES_FILE, 'w') as f:
        json.dump(profiles, f, indent=2)


def match_personas_to_projects(personas: List[dict], projects: List[dict]) -> List[dict]:
    """Generate persona-to-project matches using Claude or rule-based fallback."""
    if not personas or not projects:
        return []

    if DEMO_MODE:
        return _rule_based_match(personas, projects)

    client = get_claude_client()
    try:
        return run_claude_matching(client, personas, projects)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Claude matching error: {exc}")


@app.post("/analyze")
async def analyze_repos(repos: List[str]):
    """
    Analyze GitHub repositories and generate developer profiles

    Input: List of GitHub repository URLs
    Output: Generated developer profiles
    """
    if DEMO_MODE:
        # In demo mode, return sample profiles
        demo_profiles = load_profiles()
        return {
            "success": True,
            "profiles_generated": len(demo_profiles),
            "profiles": demo_profiles,
            "demo_mode": True,
            "message": "Demo mode: Using sample data. Add API keys to analyze real repositories."
        }

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
        "profiles": profiles_list,
        "demo_mode": False
    }


@app.get("/profiles")
async def get_profiles():
    """Return all generated developer profiles"""
    profiles = load_profiles()
    return {
        "profiles": profiles,
        "count": len(profiles),
        "demo_mode": DEMO_MODE
    }


@app.get("/search")
async def search_profiles(query: str):
    """
    Search for developers using natural language query

    Uses Claude to semantically match query against profiles (or simple keyword matching in demo mode)
    """
    profiles = load_profiles()

    if not profiles:
        return {
            "matches": [],
            "message": "No profiles available. Analyze repositories first.",
            "demo_mode": DEMO_MODE
        }

    if DEMO_MODE:
        # Simple keyword-based search for demo mode
        query_lower = query.lower()
        matches = []

        for profile in profiles:
            score = 0
            reasons = []

            # Check expertise areas
            for expertise in profile.get("expertise_areas", []):
                if any(word in expertise.lower() for word in query_lower.split()):
                    score += 30
                    reasons.append(f"expertise in {expertise}")

            # Check languages
            for lang in profile.get("primary_languages", []):
                if lang.lower() in query_lower:
                    score += 20
                    reasons.append(f"works with {lang}")

            # Check frameworks
            for framework in profile.get("frameworks", []):
                if framework.lower() in query_lower:
                    score += 25
                    reasons.append(f"uses {framework}")

            # Check best_for
            for item in profile.get("best_for", []):
                if any(word in item.lower() for word in query_lower.split() if len(word) > 3):
                    score += 15
                    reasons.append(f"good at {item.lower()}")

            if score > 0:
                match_reason = "Strong match: " + ", ".join(reasons[:3])
                matches.append({
                    **profile,
                    "relevance_score": min(score, 100),
                    "match_reason": match_reason
                })

        # Sort by score and return top 3
        matches.sort(key=lambda x: x["relevance_score"], reverse=True)
        top_matches = matches[:3]

        return {
            "matches": top_matches,
            "query": query,
            "demo_mode": True,
            "message": "Demo mode: Using simple keyword matching. Add API keys for AI-powered semantic search."
        }

    claude = get_claude_client()

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
        response = claude.messages.create(
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

        return {
            "matches": result,
            "query": query,
            "demo_mode": False
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")


@app.post("/match")
async def match_endpoint():
    """
    Pair personas with projects using Claude for reasoning (or rule-based fallback).
    """
    personas = load_personas()
    projects = load_projects()

    if not personas:
        raise HTTPException(status_code=400, detail="No personas found in personal.json")
    if not projects:
        raise HTTPException(status_code=400, detail="No projects found in projects.json")

    matches = match_personas_to_projects(personas, projects)

    return {
        "success": True,
        "persona_count": len(personas),
        "project_count": len(projects),
        "matches": matches,
        "using_claude": not DEMO_MODE,
        "demo_mode": DEMO_MODE
    }


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "running",
        "message": "GitHub Developer Profiler API",
        "demo_mode": DEMO_MODE,
        "endpoints": {
            "POST /analyze": "Analyze GitHub repositories",
            "GET /profiles": "Get all profiles",
            "GET /search?query=<query>": "Search for developers",
            "GET /mode": "Check if running in demo mode"
        }
    }


@app.get("/mode")
async def get_mode():
    """Check if API is running in demo mode"""
    return {
        "demo_mode": DEMO_MODE,
        "message": "Using sample data" if DEMO_MODE else "Using real GitHub and Claude APIs",
        "has_github_token": bool(GITHUB_TOKEN),
        "has_anthropic_key": bool(ANTHROPIC_KEY)
    }
