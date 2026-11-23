# utils/analytics.py
# Functions
import pandas as pd
import numpy as np


def calculate_moving_averages(df):
    """Calculates Simple and Exponential Moving Averages."""
    df = df.copy()
    
    # Simple Moving Averages
    df['SMA_20'] = df['close'].rolling(window=20).mean()
    df['SMA_50'] = df['close'].rolling(window=50).mean()
    df['SMA_150'] = df['close'].rolling(window=150).mean()
    
    return df


def calculate_daily_returns(df):
    """Calculates daily percentage change for close prices.
    Requires df to be sorted chronologically.
    """
    df = df.copy()
    df["daily_return"] = df["close"].pct_change() * 100
    df["next_day_close"] = df["close"].shift(-1)
    df["next_day_return"] = (df["next_day_close"] / df["close"] - 1) * 100
    return df


def threshold_success(df, threshold, direction):
    direction = direction.lower().strip()
    if direction not in {"positive", "negative"}:
        raise ValueError("direction must be 'positive' or 'negative'")

    df_daily = calculate_daily_returns(df)
    df_daily = df_daily.dropna(subset=["daily_return", "next_day_return"])

    if direction == "positive":
        subset = df_daily[df_daily["daily_return"] >= threshold]
        success = subset["next_day_return"] > 0
    else:
        subset = df_daily[df_daily["daily_return"] <= threshold]
        success = subset["next_day_return"] < 0
    return success


def calculate_threshold_probability(df, threshold, direction):
    """Historical probability that the next close continues in the same direction
    after today's move clears a threshold.

    Positive: P(next close up | today's return >= threshold).
    Negative: P(next close down | today's return <= threshold).
    """
    success = threshold_success(df, threshold, direction)
    n = len(success)
    if n == 0:
        return 0.0
    return round(float(success.sum() / n * 100), 2)


def streak_success(df, streak_length, direction):
    direction = direction.lower().strip()
    if direction not in {"positive", "negative"}:
        raise ValueError("direction must be 'positive' or 'negative'")
    if not isinstance(streak_length, int) or streak_length < 1:
        raise ValueError("streak_length must be a positive integer >= 1")

    df_daily = calculate_daily_returns(df)
    df_daily = df_daily.dropna()

    if direction == "positive":
        condition = df_daily["daily_return"] >= 0
    else:
        condition = df_daily["daily_return"] < 0

    streak = (
        condition.astype(int).rolling(window=streak_length, min_periods=streak_length).sum()
        == streak_length
    )
    subset = df_daily.loc[streak]
    return subset["next_day_return"] > 0


def calculate_streak_probability(df, streak_length, direction):
    """Probability the next close is positive after streak_length
    """
    success = streak_success(df, streak_length, direction)
    n = len(success)
    if n == 0:
        return 0.0
    return round(float(success.sum() / n * 100), 2)

