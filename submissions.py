import common
import asyncio
import aiomultiprocess as amp
from datetime import datetime
from typing import Tuple
import time
reddit = common.reddit()
mariadb = common.mariadb()
logger = common.logger("submissions")
amp.set_start_method("fork")


async def main():
    logger.info("Starting the procedure")
    start_time = time.perf_counter()
    submissions = await get_subreddit_posts(1000)
    logger.debug("Fetched posts")
    pools = []
    coroutines = []
    count = 0
    try:
        async with amp.Pool() as active_pool:
            async for submission in submissions:
                if submission.author is None:
                    author = None
                else:
                    author = submission.author.name
                info = (submission.id, submission.title,
                        author, submission.created_utc, submission.score, submission.upvote_ratio)
                coroutines.append(active_pool.apply(log_data, (info,)))
                count += 1
                if not count % 20:
                    pools.append(asyncio.gather(*coroutines))
                    coroutines = []
            if len(coroutines) > 0:
                pools.append(asyncio.gather(*coroutines))
            await asyncio.gather(*pools)
            end_time = time.perf_counter()
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
    print(f"Time taken: {end_time - start_time}")


async def get_subreddit_posts(limit: int = 1000):
    logger.info(f"Fetching the last {limit} posts from AtheismIndia")
    subreddit = await reddit.subreddit("AtheismIndia", fetch=True)
    return subreddit.new(limit=limit)


@mariadb.pool_to_cursor
async def log_data(cursor, submission: Tuple[str, str, str, int, int, float]):
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
