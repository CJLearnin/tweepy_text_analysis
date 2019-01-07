# Date: 12/17/18
# Assignment: Final Project

import sys
import re
import tweepy
import csv
from tweepy.streaming import StreamListener
from tweepy import OAuthHandler
from tweepy import Stream
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from textblob import TextBlob


class setup(object):
    def __init__(self):
        access_token = ""
        access_token_secret = ""
        consumer_key = ""
        consumer_secret = ""

        auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
        auth.set_access_token(access_token, access_token_secret)
        # Return API with authentication:
        self.api = tweepy.API(auth)

    def analize_sentiment(self, term):
        """
        Got from : https://www.geeksforgeeks.org/twitter-sentiment-analysis-using-python/
        Reads tweets for sentiment analysis using textblob API

        Args:
            term: term (str): is the search term that was use in the plotting function
        Returns:
            1,0 or -1 (polarity of words in the tweet):
             1 = postiive tweet, 0 neutral tweet, -1 is a negative tweet.
        """
        # COPIED FUNCTION FOR sentiment analysis

        analysis = TextBlob(self.clean_tweet(term))
        if analysis.sentiment.polarity > 0:
            return 1
        elif analysis.sentiment.polarity == 0:
            return 0
        else:
            return -1

    def clean_tweet(self, term):
        """
        Got from: https://www.geeksforgeeks.org/twitter-sentiment-analysis-using-python/
        function to clean the text in a tweet by removing links and special
        characters using regex.

        Args:
            term (str): is the search term that was use in the plotting function
        Return: the tweets with no links or special characters. 
        """

        return " ".join(
            re.sub("(@[A-Za-z0-9]+)|([^0-9A-Za-z \t])|(\w+:\/\/\S+)", " ", term).split()
        )

    def search(self, term, limit):
        """
        Gathers a collection of (count) tweets

        Args:
            term (str): Term used to search
            limit (int): Maximum of tweets to be counted
        """
        api = self.api

        # Searches a hastag. Count is the amount of tweets you want it to return.
        tweets = api.search(q=term, count=limit)
        # Ask why this is returning 97
        print("Number of tweets extracted: {}.\n".format(len(tweets)))
        for tweet in tweets[:100]:
            print(tweet.text)
            print()

        return tweets

    def tweets_into_df(self, tweets):
        """
        Most of it was from:
        https://galeascience.wordpress.com/2016/06/23/loading-tweets-into-a-pandas-dataframe-using-generators/
        Gathers a collection of (count) tweets

        Args:
            tweets: Takes the tweets as json and puts them into a
            Pandas dataframe.
        Returns:
            data (df): Dataframe of tweets
        """

        # Puts tweets in a dataframe by seperating json strings into
        # Pandas columns.
        # tags were pulled from the JSON file that shows all the metadata pulled from a search
        data = pd.DataFrame(data=[tweet.text for tweet in tweets], columns=["Tweets"])
        data["Length"] = np.array([len(tweet.text) for tweet in tweets])
        data["Screen_name"] = np.array([tweet.user.screen_name for tweet in tweets])
        data["Date"] = np.array([tweet.created_at for tweet in tweets])
        data["Source"] = np.array([tweet.source for tweet in tweets])
        data["Likes"] = np.array([tweet.favorite_count for tweet in tweets])
        data["RTs"] = np.array([tweet.retweet_count for tweet in tweets])
        data["Lang"] = np.array([tweet.lang for tweet in tweets])
        data["Location"] = np.array([tweet.user.location for tweet in tweets])
        data["SA"] = np.array(
            [self.analize_sentiment(tweet) for tweet in data["Tweets"]]
        )

        return data

    def search_top(self, count, term):
        """
        Gathers a collection of (count) tweets with the most likes

        Args:
            count (int): Number of tweets to be counted
            term (str): Term used to search
        Returns:
            popular_tweets (df) : Dataframe of tweets
        """
        api = self.api

        popular_tweets = [
            status
            for status in tweepy.Cursor(
                api.search, q=term, result_type="popular"
            ).items(count)
        ]

        popular_tweets = self.tweets_into_df(popular_tweets)
        popular_tweets = popular_tweets.sort_values(by=["Likes"], ascending=False)
        print(popular_tweets.head())
        # Sort by likes and return user name with the most likes for that term
        return popular_tweets

    def language(self):
        """
        Counts Languages
        """
        df = pd.read_csv("joale_languages.csv", dtype=str)
        df = df[pd.notnull(df["lang"])]

        count_lang = df["lang"].value_counts()
        fig, ax = plt.subplots()
        ax.tick_params(axis="x", labelsize=10)
        ax.tick_params(axis="y", labelsize=10)
        ax.set_xlabel("Languages", fontsize=15)
        ax.set_ylabel("Number of tweets", fontsize=15)
        ax.set_title("Top Languages", fontsize=15, fontweight="bold")
        count_lang[:20].plot(ax=ax, kind="bar", color="purple")

        plt.show()

    def plotting_function(self, term, count):
        """
        Takes the most recent tweets from the search term and prints the amount of people tweeting from differnt
        devices and the amount of people who are tweeting in english.
        Then runs sentiment analysis used from https://dev.to/rodolfoferro/sentiment-analysis-on-trumpss-tweets-using-python-
        on the words used in the tweet to determine the reaction of the tweet.
        Then plots the data in a piechart so the user can see the percent of
        negative,neutral and postive reactions towards their search term. 

        Args:
          term(str): Term you want to search on twitter.

          count(int):The amount of tweets you want to search for. 

          Returns: none

        """

        api = self.api
        sources = []
        langs = []

        cool_tweets = [
            status
            for status in tweepy.Cursor(api.search, q=term, result_type="recent").items(
                count
            )
        ]

        cool_tweets = self.tweets_into_df(cool_tweets)

        for lang in cool_tweets["Lang"]:
            if lang == "en":
                langs.append(lang)
        english_lang_count = langs.count("en")
        print(
            "The amount of android users tweeting about {} in english is {}".format(
                term, english_lang_count
            )
        )

        for source in cool_tweets["Source"]:
            sources.append(source)
        android_count = sources.count("Twitter for Android")
        iphone_count = sources.count("Twitter for iPhone")
        print("Creation of content sources:")
        print(
            "The amount of android users tweeting about {} is {}".format(
                term, android_count
            )
        )
        print(
            "The amount of iphone users tweeting about {} is {}".format(
                term, iphone_count
            )
        )

        print(cool_tweets.head(10))
        # Below was taken from the linked source.
        # The equations to perform sentiment analysis.
        pos_tweets = [
            tweet
            for index, tweet in enumerate(cool_tweets["Tweets"])
            if cool_tweets["SA"][index] > 0
        ]

        neu_tweets = [
            tweet
            for index, tweet in enumerate(cool_tweets["Tweets"])
            if cool_tweets["SA"][index] == 0
        ]

        neg_tweets = [
            tweet
            for index, tweet in enumerate(cool_tweets["Tweets"])
            if cool_tweets["SA"][index] < 0
        ]

        percent_neg_tweets = len(neg_tweets) * 100 / len(cool_tweets["Tweets"])
        percent_neutral_tweets = len(neu_tweets) * 100 / len(cool_tweets["Tweets"])
        percent_pos_tweets = len(pos_tweets) * 100 / len(cool_tweets["Tweets"])

        # Begin plotting
        slices = [percent_neg_tweets, percent_neutral_tweets, percent_pos_tweets]
        labels = (
            "Percent of tweets with a negative reaction",
            "Percent of tweets with a neutral reaction",
            "Percent of tweets with a positive reaction",
        )

        colors = ["gold", "yellowgreen", "skyblue"]
        explode = (0.1, 0, 0)
        plt.title(
            "Sentiment analysis based on the {} most recent "
            "tweets about {}".format(count, term)
        )

        plt.pie(
            slices,
            labels=labels,
            colors=colors,
            autopct="%1.1f%%",
            shadow=True,
            explode=explode,
            startangle=140,
        )
        plt.show()


if __name__ == "__main__":
    # THIS CREATES AN INSTANCE OF OUR CLASS
    s1 = setup()

    # Function calls

    # s1.search(50,"UMD")
    # s1.search_top(50,"UMD")
    # s1.language()
    s1.plotting_function("Cardi B", 30)

    # Enter the name of the csv file created in get_all_tweets function
    # most_used_words('joale_languages.csv')

