import requests
import logging
import os
import re
from datetime import datetime
import dotenv

# Load environment variables
dotenv.load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# GitHub configuration
ORG_NAME = "SigmoidAI"
GITHUB_TOKEN = os.getenv("API_TOKEN_GITHUB")
HEADERS = {"Authorization": f"token {GITHUB_TOKEN}"}
GRAPHQL_HEADERS = {"Authorization": f"Bearer {GITHUB_TOKEN}"}
GRAPHQL_URL = "https://api.github.com/graphql"
REST_API_URL = "https://api.github.com"
README_FILE = "README.md"


def get_org_members():
    """Fetch all members of the organization"""
    logger.info(f"Fetching members for organization: {ORG_NAME}")
    url = f"{REST_API_URL}/orgs/{ORG_NAME}/members"
    response = requests.get(url, headers=HEADERS)

    if response.status_code != 200:
        logger.error(
            f"Failed to fetch members: {response.status_code} - {response.text}"
        )
        return []

    members = response.json()
    logger.info(f"Found {len(members)} organization members")
    return members


def get_member_prs(username):
    """Get all PRs created by a member across the organization"""
    logger.info(f"Fetching PRs for member: {username}")

    # Create the search query string
    search_query = f"org:{ORG_NAME} author:{username} is:pr"

    query = """
    query GetUserPRs($searchQuery: String!) {
      search(query: $searchQuery, type: ISSUE, first: 100) {
        issueCount
        edges {
          node {
            ... on PullRequest {
              title
              url
              state
              createdAt
              repository {
                name
                url
              }
            }
          }
        }
      }
    }
    """

    variables = {"searchQuery": search_query}

    try:
        response = requests.post(
            GRAPHQL_URL,
            headers=GRAPHQL_HEADERS,
            json={"query": query, "variables": variables},
        )

        if response.status_code != 200:
            logger.error(
                f"Failed to fetch PRs for {username}: {response.status_code} - {response.text}"
            )
            return 0

        data = response.json()

        if "errors" in data:
            logger.error(f"GraphQL errors: {data['errors']}")
            return 0

        pr_count = data.get("data", {}).get("search", {}).get("issueCount", 0)
        logger.info(f"Found {pr_count} PRs for {username}")
        return pr_count

    except Exception as e:
        logger.error(f"Error fetching PRs for {username}: {str(e)}")
        return 0


def generate_leaderboard():
    """Generate PR leaderboard for all organization members"""
    logger.info("Generating PR leaderboard")

    # Get all organization members
    members = get_org_members()

    # Get PR counts for each member
    member_stats = []
    for member in members:
        username = member.get("login")
        avatar_url = member.get("avatar_url")
        profile_url = member.get("html_url")

        if not username:
            continue

        pr_count = get_member_prs(username)

        member_stats.append(
            {
                "username": username,
                "avatar_url": avatar_url,
                "profile_url": profile_url,
                "pr_count": pr_count,
            }
        )

    # Sort by PR count (descending)
    member_stats.sort(key=lambda x: x["pr_count"], reverse=True)

    return member_stats


def create_markdown_leaderboard(member_stats):
    """Create a markdown content for the PR leaderboard section"""
    logger.info("Creating PR leaderboard content for README.md")

    # Generate timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")

    # Create markdown content
    markdown = f"""## 📊 PR Leaderboard

*Last updated: {timestamp}*

This leaderboard shows the number of pull requests created by each member of the SigmoidAI organization.

Thanks to all our contributors! 🙏

"""

    # Calculate how many members to show per row (5 is a good number)
    members_per_row = 5
    
    # Create rows of members
    rows = [member_stats[i:i + members_per_row] for i in range(0, len(member_stats), members_per_row)]
    
    # Create table for profile pictures
    for i, row in enumerate(rows):
        # Add table header for the first row
        if i == 0:
            # Header row
            markdown += "| "
            for _ in range(min(members_per_row, len(row))):
                markdown += "Contributor | "
            markdown += "\n| "
            for _ in range(min(members_per_row, len(row))):
                markdown += ":---: | "
            markdown += "\n"
        
        # Row with images and names
        markdown += "| "
        for member in row:
            username = member["username"]
            avatar_url = member["avatar_url"]
            profile_url = member["profile_url"]
            pr_count = member["pr_count"]
            if pr_count == 0:
                pr_text = "No PRs"
            elif pr_count == 1:
                pr_text = "1 PR"
            else:
                pr_text = f"{pr_count} PRs"
            markdown += f"[![{username}]({avatar_url}&s=60)]({profile_url})<br>**{username}**<br>{pr_text} | "
        
        # Fill empty cells if needed
        remaining = members_per_row - len(row)
        for _ in range(remaining):
            markdown += " | "
            
        markdown += "\n"

    return markdown


def update_readme(leaderboard_content):
    """Update the README.md file with the PR leaderboard content"""
    logger.info("Updating README.md with PR leaderboard content")

    try:
        # Read the current README.md content with UTF-8 encoding
        with open(README_FILE, "r", encoding="utf-8") as f:
            readme_content = f.read()

        # Define the pattern to find the PR leaderboard section
        # Look for a section that starts with ## 📊 PR Leaderboard and ends before the next ## heading
        pattern = r"## 📊 PR Leaderboard.*?(?=\n+## |\Z)"

        # Ensure the leaderboard content ends with two newlines for proper spacing
        formatted_content = leaderboard_content.rstrip() + "\n\n"

        # Check if the pattern exists in the README
        if re.search(pattern, readme_content, re.DOTALL):
            # Replace the existing PR leaderboard section
            updated_content = re.sub(
                pattern, formatted_content.rstrip(), readme_content, flags=re.DOTALL
            )
        else:
            # If the section doesn't exist, add it after the repository description
            repo_description_pattern = r"^# .*?\n\n.*?\n\n"
            if re.search(repo_description_pattern, readme_content, re.DOTALL):
                updated_content = re.sub(
                    repo_description_pattern,
                    lambda m: m.group(0) + formatted_content,
                    readme_content,
                    count=1,
                    flags=re.DOTALL,
                )
            else:
                # If no description pattern found, just append to the end
                updated_content = readme_content + "\n\n" + formatted_content

        # Write the updated content back to README.md with UTF-8 encoding
        with open(README_FILE, "w", encoding="utf-8") as f:
            f.write(updated_content)

        logger.info("README.md updated successfully with PR leaderboard content")
        return True
    except Exception as e:
        logger.error(f"Error updating README.md: {str(e)}")
        return False


def main():
    """Main function to generate PR leaderboard"""
    logger.info("Starting PR leaderboard generation script")

    # Check if required environment variables are set
    if not GITHUB_TOKEN:
        logger.error(
            "GitHub token not found. Please set API_TOKEN_GITHUB environment variable."
        )
        return

    # Generate leaderboard data
    member_stats = generate_leaderboard()

    # Create markdown content
    leaderboard_content = create_markdown_leaderboard(member_stats)

    # Update README.md
    update_readme(leaderboard_content)

    logger.info("PR leaderboard generation completed")


if __name__ == "__main__":
    main()
