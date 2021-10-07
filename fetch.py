#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import json
import util
import itertools
import tweepy
import logging.handlers
from dotenv import load_dotenv

TWEETS_PER_USER = 200

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    logger = logging.getLogger(__name__)
    if not os.path.exists('logs'):
        os.makedirs('logs')
    handler = logging.handlers.RotatingFileHandler('logs/fetch.log', maxBytes=50 * 1024 * 1024, backupCount=10)
    handler.setFormatter(logging.Formatter('(%(asctime)s) [%(process)d] %(levelname)s: %(message)s'))
    logger.addHandler(handler)
    logger.info(sys.version)

    load_dotenv()

    if not os.path.exists('data'):
        os.makedirs('data')

    try:
        client = tweepy.Client(os.getenv('BEARER_TOKEN'), wait_on_rate_limit=True)

        logger.info('Fetching seed user data...')
        # TODO get follower count
        seed_users = sys.argv[1:]
        users = client.get_users(usernames=seed_users, user_fields=['public_metrics']).data

        logger.info('Fetching friends...')
        friendList = []
        for user in users:
            friends = list(tweepy.Paginator(client.get_users_following, user.id, max_results=1000,
                                            user_fields=['public_metrics']).flatten())
            logger.info('Fetched %d followers for user %s' % (len(friends), user.username))
            friendList.append(friends)
        commonFriends = list(set.intersection(*map(set, friendList)))
        logger.info(
            'Fetched %d followers; %d common followers' % (len(list(itertools.chain(*friendList))), len(commonFriends)))

        logger.info('Fetching tweets...')
        outfile = 'data/output.json'
        if os.path.isfile(outfile):
            os.remove(outfile)
        allTweets = []
        for user in users + commonFriends:
            tweets = list(tweepy.Paginator(client.get_users_tweets, user.id, exclude='replies', max_results=100,
                                           tweet_fields=['public_metrics']).flatten(limit=TWEETS_PER_USER))
            logger.info('Fetched %d tweets for account %s' % (len(tweets), user.username))
            allTweets.extend(tweets)
            with open(outfile, 'a') as outfile:
                json.dump([tweet.data for tweet in tweets], outfile)
                outfile.write('\n')

        logger.info('Done! %d tweets total' % len(allTweets))

    except KeyboardInterrupt:
        logger.error('Ctrl+C was pressed, exiting...')
        pass
    except Exception as exc:
        logger.error(exc)
        logger.error(util.full_stack())
    finally:
        pass
