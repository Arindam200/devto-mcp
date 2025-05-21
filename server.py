import httpx
from mcp.server.fastmcp import FastMCP, Context
import os

# Create a Dev.to MCP server
mcp = FastMCP("Dev.to MCP Server")

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