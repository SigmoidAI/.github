# SigmoidAI Scripts

This directory contains utility scripts for the SigmoidAI organization.

## PR Leaderboard Script

The `pr_leaderboard.py` script generates a leaderboard of pull requests created by members of the SigmoidAI organization. The leaderboard is integrated directly into the main `README.md` file of the repository.

### Features

- Fetches all members of the SigmoidAI organization
- Counts all pull requests created by each member
- Generates a visual grid of profile pictures with PR counts
- Sorts members by PR count (highest to lowest)
- Updates the main README.md file with the leaderboard
- Updates daily via GitHub Actions

### Running Locally

To run the script locally:

1. Make sure you have the required dependencies installed:
   ```
   pip install -r requirements.txt
   ```

2. Set up your GitHub API token in the `.env` file:
   ```
   API_TOKEN_GITHUB=your_github_token
   ```

3. Run the script:
   ```
   python scripts/pr_leaderboard.py
   ```

### GitHub Actions Workflow

The script is automatically run daily via GitHub Actions. The workflow is defined in `.github/workflows/pr_leaderboard.yml`.

The workflow:
- Runs every day at midnight UTC
- Generates the PR leaderboard
- Updates the README.md file with the latest leaderboard data
- Commits and pushes the updated README to the repository 