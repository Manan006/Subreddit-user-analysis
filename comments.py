import common
import asyncio
import aiomultiprocess as amp
from datetime import datetime
from typing import Tuple
import time
reddit = common.reddit()
mariadb = common.mariadb(['comment'])
logger = common.logger("comments")
amp.set_start_method("fork")


async def main():
    logger.info("Starting the procedure")
    start_time = time.perf_counter()
    logger.info(f"Fetching the last {None} posts from the Database")
    submissions = await get_submissions_from_db()
    logger.debug("Fetched posts")
    pools = []
    coroutines = []
    try:
        async with amp.Pool() as active_pool:
            for submission in submissions:
                comments = await get_comments_from_post(submission[0])
                for comment in comments:
                    logger.debug(comment.body)
                    if comment.author is None:
                        author = None
                    else:
                        author = comment.author.name
                    info = (comment.id, comment.body, author,
                            comment.created_utc, comment.score)
                    coroutines.append(active_pool.apply(log_data, (info,)))
                    if not len(coroutines) % 250:
                        pools.append(asyncio.gather(*coroutines))
                        coroutines = []
                        # await asyncio.sleep(0.07)
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


async def get_submissions_from_db(limit: int = None):
    logger.info(f"Fetching the last {limit} posts from the Database")
    if limit is None:
        await mariadb.cursor.execute(
            "SELECT `id` FROM `submission` ORDER BY `created` DESC")
    else:
        await mariadb.cursor.execute(
            "SELECT `id` FROM `submission` ORDER BY `created` DESC LIMIT %s", (limit,))
    return await mariadb.cursor.fetchall()


async def get_comments_from_post(submission: str):
    submission = await reddit.submission(submission)
    logger.debug(f"Got submission {submission.title}")
    await submission.comments.replace_more(limit=None)
    return submission.comments.list()


@mariadb.pool_to_cursor
async def log_data(cursor, comment: Tuple[str, str, str, int, int]):
    logger.debug(f"Logging data for {comment[0]}")
    info = (comment[0], comment[1], comment[2], datetime.fromtimestamp(
        comment[3]), comment[4])
    await cursor.execute("INSERT INTO comment (id, body, author, created, score) VALUES (%s,%s,%s,%s,%s)", info)
    logger.debug(f"Logged data for {comment[0]}")

if __name__ == "__main__":
    asyncio.run(main())
