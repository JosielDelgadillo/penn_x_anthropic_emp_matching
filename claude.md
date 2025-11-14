# Penn × Anthropic Empowerment Matching

## Project Overview

**Type**: Student Initiative Landing Page
**Stack**: React (Create React App)
**Status**: Active Development
**Collaborators**: Working with Josiel Delgadillo and team
**Repository**: https://github.com/JosielDelgadillo/penn_x_anthropic_emp_matching

## Purpose

Landing page for Penn × Anthropic Empowerment Matching (PXAE), a student-led initiative helping the Penn community explore responsible AI development through:
- Weekly workshops on frontier models, alignment, and safety
- Small-group mentorship with Anthropic researchers and alumni
- Interdisciplinary impact projects for civic partners

## Development Goals

### Current Focus
- **UI/UX Enhancement**: Improve design and user experience
- **Feature Development**: Add new functionality (forms, backend integration, etc.)
- **Deployment**: Get the site publicly accessible

### Potential Features to Add
- Email signup form integration
- Event calendar/schedule
- Speaker/mentor profiles
- Project showcase gallery
- Application portal

## Technical Context

### Stack
- React 19.2.0
- Create React App 5.0.1
- Pure CSS styling (no framework currently)

### Current Structure
```
src/
├── App.js          - Main component with all sections
├── App.css         - All styling
├── index.js        - Entry point
└── [CRA defaults]  - Test setup, reportWebVitals, etc.
```

### Key Sections
1. **Navigation**: Brand + nav links + CTA
2. **Hero**: Overview of initiative
3. **Program**: Three cards (Workshops, Mentorship, Impact Projects)
4. **Interest**: Email signup section
5. **Footer**: Copyright info

## Development Workflow

### Local Development
```bash
npm install         # Install dependencies
npm start          # Run dev server (localhost:3000)
npm test           # Run tests
npm run build      # Production build
```

### Before Making Changes
- Review current styling in App.css
- Component is currently monolithic (all in App.js)
- Consider componentization for scalability

## Design Principles

Based on existing code:
- Clean, minimal design
- Clear hierarchy with eyebrow → headline → body copy
- Focus on clarity and accessibility
- Branded with "PXAE" pill design

## Deployment Considerations

- React app ready for static hosting (Vercel, Netlify, GitHub Pages)
- No environment variables currently needed
- No backend/API dependencies (yet)
- Consider domain: pxae.org or similar

## Future Architecture Ideas

If adding backend functionality:
- Consider Next.js migration for SSR/API routes
- Airtable/Notion for email collection
- Contentful/Sanity for content management
- Firebase/Supabase for authentication (if building member portal)

## Collaboration Notes

- This is Josiel's repository
- Coordinate changes via PRs
- Discuss major architectural changes before implementing
- Keep commits atomic and well-documented

## Portfolio Relevance

This project demonstrates:
- React development skills
- Product thinking (student initiative)
- Collaboration with technical teams
- Understanding of responsible AI themes

Could be featured as a case study showing:
- How you contribute to mission-driven tech initiatives
- Full-stack thinking (even if starting with frontend)
- Community building through product

---

**Last Updated**: 2025-11-14
**Next Steps**: Discuss with team what features to prioritize
