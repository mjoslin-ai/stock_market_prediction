# utils/analytics.py
# Functions
import pandas as pd
import numpy as np

def calculate_daily_returns(df):
    """
    Calculates daily percentage change for close prices
    Requires df to be sorted chronologically
    Returns a boolean column indicating if the next day's return is positive
    """
    df = df.copy()
    # Compute (today’s close − previous day’s close) / previous day’s close * 100
    df['daily_return'] = df['close'].pct_change() * 100
    # Shift close column so that each row now contains the closing price of the next trading day
    df['next_day_close'] = df['close'].shift(-1)
    # Next day return percentage change
    df['next_day_return'] = (df['next_day_close'] / df['close'] - 1) * 100
    
    return df

def calculate_threshold_probability(df, threshold, direction):
    """
    Calculates historical probability that the next day closes positive or negative based on threshold of daily returns.
    """
    direction = direction.lower().strip()
    if direction not in {"positive", "negative"}:
        raise ValueError("direction must be 'positive' or 'negative'")
    
    df_daily = calculate_daily_returns(df)

    # Drop rows where we cannot compute either today's or next day's return
    df_daily = df_daily.dropna(subset=['daily_return', 'next_day_return'])

    # Filter according to direction
    if direction == "positive":
        subset = df_daily[df_daily['daily_return'] >= threshold]
        # Probability that next day is also positive
        success = subset['next_day_return'] > 0
    else:  
        subset = df_daily[df_daily['daily_return'] <= threshold]
        # Probability that next day is also negative
        success = subset['next_day_return'] < 0

    n = len(subset)
    if n == 0:
        return 0.0

    probability = (success.sum() / n) * 100
    return round(probability, 2)

def calculate_streak_probability(df, streak_length, direction):
    """
    Calculates the probability of a streak of consecutive positive or negative days.
    """
    # Check direction input
    direction = direction.lower().strip()
    if direction not in {"positive", "negative"}:
        raise ValueError("direction must be 'positive' or 'negative'")

    # Check streak_length input
    if not isinstance(streak_length, int) or streak_length < 1:
        raise ValueError("streak_length must be a positive integer")

    df_daily = calculate_daily_returns(df)

    # Drop rows where either todays or next days return is missing
    df_daily = df_daily.dropna(subset=['daily_return', 'next_day_return'])

    # Filter according to direction
    if direction == "positive":
        is_streak_day = df_daily[df_daily['daily_return'] >= 0]
    else:
        is_streak_day = df_daily[df_daily['daily_return'] < 0]

    # Calculate streaks
    streak = (
        is_streak_day.astype(int)
        .rolling(window=streak_length, min_periods=streak_length)
        .sum() == streak_length
    )

    subset = df_daily.loc[streak]
    n = len(subset)
    if n == 0:
        return 0.0

    # Return probability of next day being positive or negative
    success = subset["next_day_return"] > 0
    probability = (success.sum() / n) * 100
    return round(probability, 2)