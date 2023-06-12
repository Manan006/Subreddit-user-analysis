from typing import Tuple
import json
import common
import asyncio
from datetime import datetime
from config import *


# Initialize the things we will need
mariadb = common.mariadb()
logger = common.logger("user_lists")
reddit = common.reddit()


async def main():
    try:
        logger.info("Generating user list")
        await mariadb.cursor.execute("SELECT `author`,`score`*10 FROM `submission` WHERE  DATEDIFF(%s,`created`) <= %s AND `author` IS NOT NULL;", (datetime.now(), DAYS))
        submission_author = await mariadb.cursor.fetchall()  # Get the authors of the submissions in the last 30 days
        logger.info(f"Found {len(submission_author)} submission authors")
        await mariadb.cursor.execute("SELECT `author`,`score` FROM `comment` WHERE  DATEDIFF(%s,`created`) <= %s AND `author` IS NOT NULL;", (datetime.now(), DAYS))
        comment_author = await mariadb.cursor.fetchall()  # Get the authors of the comments in the last 30 days
        logger.info(f"Found {len(comment_author)} comment authors")
        await mariadb.cursor.execute("SELECT `username` FROM `user`;")
        users_in_db = await mariadb.cursor.fetchall()
        logger.info(
            f"Found {len(users_in_db)} users already in the database. Skipping from list") # Get the users already in the database so we can skip them
        user_scores = await calc_users_score(submission_author + comment_author, users_in_db) # Calculate the total score of each user
        logger.info(f"Found {len(user_scores)} unique authors")
        logger.info("Calculating user scores")
        user_scores = {k: v for k, v in sorted(
            user_scores.items(), key=lambda item: item[1], reverse=True)} # Sort the users by their score from highest to lowest
        coroutines = []
        logger.info("Analyzing users")
        for user, score in user_scores.items():
            coroutines.append(analyze_user(user, score)) # Create a list of coroutines to be executed
        logger.info("Waiting for all coroutines to finish")
        await asyncio.gather(*coroutines)
    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt: Exiting gracefully")
    logger.info("Closing mariadb and reddit")
    await reddit.end()
    await mariadb.end()
    logger.info("Exited successfully")


@mariadb.pool_to_cursor
async def analyze_user(cursor, user, score): # Analyze a user and add them to the database
    logger.debug(f"Loading user: {user}")
    try:
        user = await reddit.redditor(user, fetch=True)
    except Exception as e:
        logger.warning(f"Failed to load user: {user}")
        logger.exception(e)
        return
    logger.debug(f"Analyzing user: {user.name}")
    content = user.new(limit=LAST_CONTENT_LIMIT)
    active_subreddits = []
    cache = {}
    exception_count = 0
    try:
        async for item in content:
            if cache.get(item.subreddit.display_name) == None:
                cache[item.subreddit.display_name] = 1
            else:
                cache[item.subreddit.display_name] += 1
            if cache[item.subreddit.display_name] >= MINUMUM_INTERACTIONS_FOR_ACTIVITY and item.subreddit.display_name not in active_subreddits:
                cache[item.subreddit.display_name] = 0
                active_subreddits.append(item.subreddit.display_name)
    except Exception as e:
        exception_count += 1
        logger.warning(
            f"Failed to analyze user: {user.name}'s content {exception_count} times.")
        logger.exception(e)
        pass
    logger.debug(
        f"Found {len(active_subreddits)} active subreddits for user: {user.name}\n{', '.join(active_subreddits)}")
    await cursor.execute(
        "INSERT INTO `user` (`username`,`created`,`score`,`active_subreddits`) VALUES (%s,%s,%s,%s);", (user.name, datetime.fromtimestamp(user.created_utc), score, json.dumps(active_subreddits)))

# Calculate the total score of each user
async def calc_users_score(users: set, users_in_db: Tuple[tuple, ...]):
    user_scores = {}
    for user, score in users:
        if user_scores.get(user) == None:
            if (user,) not in users_in_db:
                user_scores[user] = score
        else:
            user_scores[user] += score
    return user_scores


if __name__ == "__main__":
    asyncio.run(main())
