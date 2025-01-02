from cat.mad_hatter.decorators import tool
import asyncpraw
import pandas as pd
from datetime import datetime
from cat.log import log
import asyncio


async def setup_reddit_client(client_id, client_secret, user_agent):
    """Setup async Reddit client."""
    return asyncpraw.Reddit(
        client_id=client_id,
        client_secret=client_secret,
        user_agent=user_agent
    )


async def get_comments(submission, limit=10):
    """Extracts comments from a post asynchronously."""
    comments = []
    await submission.comments.replace_more(limit=0)  # Load hidden comments

    all_comments = await submission.comments.list()
    for comment in all_comments[:limit]:
        comments.append({
            'comment_text': comment.body,
            'score': comment.score,
            'date': datetime.fromtimestamp(comment.created_utc).strftime('%Y-%m-%d %H:%M:%S')
        })
    return [comment['comment_text'] for comment in comments if comment['score'] > 0]


async def search_on_reddit(reddit, query, subreddit=None, limit=10, comments_limit=5):
    """
    Performs an async search on Reddit including comments.
    Parameters:
    - reddit: instance of the AsyncPRAW client
    - query: string to search for
    - subreddit: specific subreddit name (optional)
    - limit: maximum number of posts to return
    - comments_limit: maximum number of comments per post
    Returns:
    - List of post dictionaries
    """
    posts_results = []
    search_location = await reddit.subreddit(subreddit if subreddit else 'all')

    async for submission in search_location.search(query, limit=limit, sort='relevance'):
        # Add the post
        posts_results.append({
            'title': submission.title,
            'url': f"https://reddit.com{submission.permalink}",
            'post_text': submission.selftext,
            'comments': await get_comments(submission, comments_limit)
        })

    return posts_results


@tool(return_direct=True)
async def search_reddit(query, cat):
    """
    When user asks you to "search on reddit" always use this tool.
    Input is the query.
    """
    # Load settings
    settings = cat.mad_hatter.get_plugin().load_settings()
    client_id = settings["client_id"]
    client_secret = settings["client_secret"]
    user_agent = 'AsyncRedditSearchScript_v1.0'
    posts_limit = settings["posts_limit"]
    comments_limit = settings["comments_limit"]

    # Initialize async Reddit client
    reddit = await setup_reddit_client(client_id, client_secret, user_agent)

    try:
        # Perform async search
        posts = await search_on_reddit(
            reddit=reddit,
            query=query,
            limit=posts_limit,
            comments_limit=comments_limit
        )

        prompt = (
            f"Generate a coherent and contextually appropriate response based on the provided array of objects: {posts}.\n"
            "Each object in the array represents a Reddit post and contains the following keys:\n"
            "title: the title of the post\n"
            "url: a link to the post\n"
            "post_text: the content of the post itself\n"
            "comments: a list of comments related to the post\n"
            "Each object in the array contains relevant data, and your task is to analyze the content and synthesize a meaningful reply.\n"
            "The response should be logically consistent, accurate, and appropriately address the context derived from the array's contents\n"
        )

        response = await cat.llm(prompt)
        log.info(f"Search Reddit response {posts}")
        return response

    finally:
        # Ensure the client is properly closed
        await reddit.close()

# Helper function to run the async tool in sync context if needed


def sync_search_reddit(query, cat):
    return asyncio.run(search_reddit(query, cat))
