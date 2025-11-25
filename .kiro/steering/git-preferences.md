# Project Preferences

## Language Preferences

- Communicate with the user in Russian
- Write all plans, documentation, and explanations in Russian
- Write git commit messages in English only

## Shell and Tools Preferences

- Use PowerShell for Windows-native commands
- Run git commands directly using git CLI (without WSL prefix)
- Use WSL for Linux utilities (grep, sed, awk, bash scripts, etc.)
- Prefix Linux utility commands with `wsl` when running on Windows system
- Show commands before executing them for transparency

## Git Workflow

- Always work in feature branches, never commit directly to main
- Create a new branch for each feature or fix
- Make commits with clear, descriptive messages in English
- Create pull requests (PR) for code review
- Merge to main branch only upon user's explicit request
- Keep branches up to date with main before merging

## Git Access

- Git access is configured for both HTTPS and SSH protocols
- Both Windows git CLI and WSL git have access configured
- Use the appropriate protocol based on the repository configuration
