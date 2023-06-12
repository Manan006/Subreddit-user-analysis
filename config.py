LOG_FILE="logs/logs.log" # Path to log file
LOG_LEVEL=2 # 2: DEBUG, 1: INFO, Anything else: WARNING
ENABLE_STREAM_HANDLER=1 # Whether to output/print logs to console


SUBREDDIT = "AtheismIndia" # Subreddit to analyze
DAYS = 30 # Number of days to analyze the user from (means that the user must have posted/commented within the last `DAYS` days in order to be analyzed)
LAST_CONTENT_LIMIT = 250 # Number of posts/comments to analyze from the user (the most recent `LAST_CONTENT_LIMIT` posts/comments will be analyzed)
MINUMUM_INTERACTIONS_FOR_ACTIVITY = 10 # Minimum number of posts/comments in a subreddit for it to be considered active. Tune it according to the `LAST_CONTENT_LIMIT` and `DAYS` variables
