import httpx
from mcp.server.fastmcp import FastMCP, Context
import os

# Create a Dev.to MCP server
mcp = FastMCP(
    "Dev.to API", 
    instructions="""
    # Dev.to API Server
    
    This server provides access to Dev.to content through various tools.
    
    ## Available Tools
    - `get_latest_articles()` - Get the latest articles from Dev.to
    - `get_top_articles()` - Get the most popular articles from Dev.to
    - `get_articles_by_tag(tag)` - Get articles by tag
    - `get_article_by_id(id)` - Get a specific article by ID
    - `search_articles(query, page=1)` - Search for articles by keywords in title/description
    - `get_article_details(article_id)` - Get full content and metadata for a specific article
    - `get_articles_by_username(username)` - Get articles written by a specific author
    - `create_article(title, body_markdown, tags, published)` - Create and publish a new article
    - `update_article(article_id, title, body_markdown, tags, published)` - Update an existing article
    - `get_user_info(username)` - Get information about a Dev.to user
    
    ## When to use what
    - For browsing recent content: Use `get_latest_articles()` 
    - For popular content: Use `get_top_articles()`
    - For articles on specific topics: Use `get_articles_by_tag(tag)` with the tag name
    - For searching by keywords: Use `search_articles(query)`
    - For author-specific content: Use `get_articles_by_username(username)`
    - For full article content: Use `get_article_details(article_id)` or `get_article_by_id(id)`
    - For publishing new content: Use `create_article(title, body_markdown, tags, published)`
    - For updating existing content: Use `update_article(article_id, title, body_markdown, tags, published)`
    - For user profiles: Use `get_user_info(username)`
    
    ## Example Queries
    - "Find articles about Python on Dev.to" → Use `search_articles("Python")` or `get_articles_by_tag("python")`
    - "Show me the latest Dev.to articles" → Use `get_latest_articles()`
    - "Get details for article 1234" → Use `get_article_by_id("1234")` or `get_article_details(1234)`
    - "Find articles by author ben" → Use `get_articles_by_username("ben")`
    - "Create a new article about Python" → Use `create_article("My Python Article", "# Python\nContent here...", "python,webdev", false)`
    - "Update my article with ID 1234" → Use `update_article(1234, "New Title", "Updated content...")`
    - "Get user info for username dev_user" → Use `get_user_info("dev_user")`

    ## Notes
    - Ensure you have a valid Dev.to API key set in the environment variable `DEV_TO_API_KEY`.
    - The API key is required for creating and updating articles.
    - The API key can be obtained from your Dev.to account settings.
    - The API key should be kept secret and not shared publicly.
    - The API key is used to authenticate requests to the Dev.to API.

    """
)

# Constants
BASE_URL = "https://dev.to/api"

# Helper functions
async def fetch_from_api(path: str, params: dict = None) -> dict:
    """Helper function to fetch data from Dev.to API"""
    async with httpx.AsyncClient() as client:
        url = f"{BASE_URL}{path}"
        response = await client.get(url, params=params, timeout=10.0)
        response.raise_for_status()
        return response.json()

# Resources

@mcp.tool()
async def get_latest_articles() -> str:
    """Get the latest articles from Dev.to"""
    articles = await fetch_from_api("/articles/latest")
    return format_articles(articles[:10])  # Limiting to 10 for readability
    
@mcp.tool()
async def get_top_articles() -> str:
    """Get the top articles from Dev.to"""
    articles = await fetch_from_api("/articles")
    return format_articles(articles[:10])  # Limiting to 10 for readability

@mcp.tool()
async def get_articles_by_tag(tag: str) -> str:
    """Get articles by tag from Dev.to"""
    articles = await fetch_from_api("/articles", params={"tag": tag})
    return format_articles(articles[:10])  # Limiting to 10 for readability

@mcp.tool()
async def get_article_by_id(id: str) -> str:
    """Get a specific article by ID from Dev.to"""
    article = await fetch_from_api(f"/articles/{id}")
    return format_article_details(article)

# Tools

@mcp.tool()
async def search_articles(query: str, page: int = 1) -> str:
    """
    Search for articles on Dev.to
    
    Args:
        query: Search term to find articles
        page: Page number for pagination (default: 1)
    """
    articles = await fetch_from_api("/articles", params={"page": page})
    
    filtered_articles = [
        article for article in articles 
        if query.lower() in article.get("title", "").lower() or 
           query.lower() in article.get("description", "").lower()
    ]
    
    return format_articles(filtered_articles[:10])

@mcp.tool()
async def get_article_details(article_id: int) -> str:
    """
    Get detailed information about a specific article
    
    Args:
        article_id: The ID of the article to retrieve
    """
    article = await fetch_from_api(f"/articles/{article_id}")
    return format_article_details(article)

@mcp.tool()
async def get_articles_by_username(username: str) -> str:
    """
    Get articles written by a specific user
    
    Args:
        username: The username of the author
    """
    articles = await fetch_from_api("/articles", params={"username": username})
    return format_articles(articles[:10])

@mcp.tool()
async def get_user_info(username: str) -> str:
    """
    Get information about a Dev.to user
    
    Args:
        username: The username of the user
    """
    try:
        user = await fetch_from_api(f"/users/{username}")
        return format_user_profile(user)
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return f"User {username} not found."
        raise e

@mcp.tool()
async def create_article(title: str, body_markdown: str, tags: str = "", published: bool = False) -> str:
    """
    Create and publish a new article on Dev.to
    
    Args:
        title: The title of the article
        body_markdown: The content of the article in markdown format
        tags: Comma-separated list of tags (e.g., "python,tutorial,webdev")
        published: Whether to publish immediately (True) or save as draft (False)
    """
    article_data = {
        "article": {
            "title": title,
            "body_markdown": body_markdown,
            "published": published,
            "tags": tags
        }
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{BASE_URL}/articles", json=article_data, headers={"Content-Type": "application/json", "api-key": os.getenv("DEV_TO_API_KEY")}, timeout=10.0)
        response.raise_for_status()
        article = response.json()
        
    return f"Article created successfully with ID: {article.get('id')}\nURL: {article.get('url')}"

@mcp.tool()
async def update_article(article_id: int, title: str = None, body_markdown: str = None, 
                        tags: str = None, published: bool = None) -> str:
    """
    Update an existing article on Dev.to
    
    Args:
        article_id: The ID of the article to update
        title: New title for the article (optional)
        body_markdown: New content in markdown format (optional)
        tags: New comma-separated list of tags (optional)
        published: Change publish status (optional)
    """
    # First get the current article data
    article = await fetch_from_api(f"/articles/{article_id}")
    
    # Prepare update data with only the fields that are provided
    update_data = {"article": {}}
    if title is not None:
        update_data["article"]["title"] = title
    if body_markdown is not None:
        update_data["article"]["body_markdown"] = body_markdown
    if tags is not None:
        update_data["article"]["tags"] = tags
    if published is not None:
        update_data["article"]["published"] = published
    
    async with httpx.AsyncClient() as client:
        response = await client.put(f"{BASE_URL}/articles/{article_id}", json=update_data, timeout=10.0)
        response.raise_for_status()
        updated_article = response.json()
    
    return f"Article updated successfully\nURL: {updated_article.get('url')}"

# Prompts

@mcp.prompt()
def search_prompt(query: str) -> str:
    """Create a search prompt for Dev.to articles"""
    return f"Please search for articles on Dev.to about {query} and summarize the key findings."

@mcp.prompt()
def analyze_article(article_id: str) -> str:
    """Create a prompt to analyze a specific article"""
    return f"Please analyze the Dev.to article with ID {article_id} and provide a summary of its key points and insights."

# Helper formatting functions

def format_articles(articles: list) -> str:
    """Format a list of articles for display"""
    if not articles:
        return "No articles found."
    
    result = "# Dev.to Articles\n\n"
    for article in articles:
        title = article.get("title", "Untitled")
        author = article.get("user", {}).get("name", "Unknown Author")
        published_date = article.get("readable_publish_date", "Unknown date")
        article_id = article.get("id", "")
        tags = article.get("tags", "")
        
        result += f"## {title}\n"
        result += f"ID: {article_id}\n"
        result += f"Author: {author}\n"
        result += f"Published: {published_date}\n"
        result += f"Tags: {tags}\n"
        result += f"Description: {article.get('description', 'No description available.')}\n\n"
    
    return result

def format_article_details(article: dict) -> str:
    """Format a single article with full details"""
    if not article:
        return "Article not found."
    
    title = article.get("title", "Untitled")
    author = article.get("user", {}).get("name", "Unknown Author")
    published_date = article.get("readable_publish_date", "Unknown date")
    body = article.get("body_markdown", "No content available.")
    tags = article.get("tags", "")
    
    result = f"# {title}\n\n"
    result += f"Author: {author}\n"
    result += f"Published: {published_date}\n"
    result += f"Tags: {tags}\n\n"
    result += "## Content\n\n"
    result += body
    
    return result

def format_user_profile(user: dict) -> str:
    """Format a user profile for display"""
    if not user:
        return "User not found."
    
    username = user.get("username", "Unknown")
    name = user.get("name", "Unknown")
    bio = user.get("summary", "No bio available.")
    twitter = user.get("twitter_username", "")
    github = user.get("github_username", "")
    website = user.get("website_url", "")
    location = user.get("location", "")
    joined = user.get("joined_at", "")
    
    result = f"# {name} (@{username})\n\n"
    result += f"Bio: {bio}\n\n"
    
    result += "## Details\n"
    if location:
        result += f"Location: {location}\n"
    if joined:
        result += f"Member since: {joined}\n"
    
    result += "\n## Links\n"
    if twitter:
        result += f"Twitter: @{twitter}\n"
    if github:
        result += f"GitHub: {github}\n"
    if website:
        result += f"Website: {website}\n"
    
    return result


if __name__ == "__main__":
    print("Starting Dev.to MCP server...")
    mcp.run() 