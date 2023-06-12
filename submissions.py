import common
import asyncio
import aiomultiprocess as amp
from datetime import datetime
from typing import Tuple
from config import *


# Initialize the things we will need
reddit = common.reddit()
mariadb = common.mariadb()
logger = common.logger("submissions")
amp.set_start_method("fork") # Set the start method for the multiprocessing pool. Set to "spawn" on windows


async def main():
    logger.info("Starting the procedure")
    submissions = await get_subreddit_posts(1000) # Get the submissions from the subreddit. Max limit is 1000
    logger.debug("Fetched posts")
    pools = []
    coroutines = []
    count = 0
    try:
        async with amp.Pool() as active_pool: # Create a multiprocessing pool
            async for submission in submissions: # Iterate over the submissions
                if submission.author is None: # Incase the author deleted their account
                    author = None
                else:
                    author = submission.author.name
                info = (submission.id, submission.title,
                        author, submission.created_utc, submission.score, submission.upvote_ratio)
                coroutines.append(active_pool.apply(log_data, (info,))) # Add the coroutine to the list of coroutines to be executed
                count += 1
                if not count % 50: # When the list reaches 20, we dump the nest the list to the multiprocessing pool and empty the list
                    pools.append(asyncio.gather(*coroutines))
                    coroutines = []
            if len(coroutines) > 0: # If there are any coroutines left, we dump them into the multiprocessing pool
                pools.append(asyncio.gather(*coroutines))
            await asyncio.gather(*pools) # Wait for all the coroutines accross the pools to finish
        logger.info("All coroutines finished")
    except Exception as e:
        logger.critical(
            "Failed to insert posts into database.")
        logger.exception(e)
    else:
        logger.info("Cleaning up")
    await mariadb.end()
    await reddit.end()
    logger.info("Exiting gracefully")


async def get_subreddit_posts(limit: int = 1000): # Get the submissions from the subreddit
    logger.info(f"Fetching the last {limit} posts from AtheismIndia")
    subreddit = await reddit.subreddit(SUBREDDIT, fetch=True)
    return subreddit.new(limit=limit)


@mariadb.pool_to_cursor
async def log_data(cursor, submission: Tuple[str, str, str, int, int, float]): # Log the data into the database
    logger.debug(f"Logging data for {submission[0]}")
    if submission[2] is not None:
        author = submission[2]
    else:
        author = None
    info = (submission[0], submission[1], author, datetime.fromtimestamp(
        submission[3]), submission[4], submission[5])
    await cursor.execute("INSERT INTO submission (id, title, author, created, score, upvote_ratio) VALUES (%s,%s,%s,%s,%s,%s)", info)
    logger.debug(f"Logged data for {submission[0]}")

if __name__ == "__main__":
    asyncio.run(main())
