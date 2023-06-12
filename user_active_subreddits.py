from common import *


async def main():
    reddit = await init()
    async with aiosqlite.connect("main.db") as db:
        async with await db.execute("SELECT author FROM submission") as cursor:
            authors = await cursor.fetchall()
        for redditor in authors:
            redditor = await reddit.redditor(redditor)
            subreddits = []
            async for submission in redditor.submissions.new(limit=25):
               subreddits.append(submission.subreddit.display_name)
             await db.execute("INSERT INTO user (user,subreddits) VALUES (?,?)",(redditor.name,subreddits))
    await end(reddit)




if __name__=="__main__":
    asyncio.run(main())