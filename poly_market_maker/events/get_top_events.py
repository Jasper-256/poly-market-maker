import pandas as pd
from datetime import datetime, timedelta
import os
import poly_market_maker.events.fetch_data as fetch_data

def save_events():
    poly_events = fetch_data.poly_fetch_all()
    os.makedirs('data', exist_ok=True)
    fetch_data.save_data_to_csv('data/poly_events.csv', poly_events)

def get_top_events(num_of_events):
    save_events()

    input_file = "data/poly_events.csv"
    output_file = "data/selected_events.csv"

    # Load the CSV file into a pandas DataFrame
    df = pd.read_csv(input_file, sep='|')

    # Get the current date
    today = datetime.now()
    max_days_from_now = today + timedelta(days=7)

    # Apply the filtering criteria
    filtered_df = df[
        (df['rewards_daily_rate'] >= 10) &
        (df['rewards_min_size'] <= 20) &
        (df['rewards_max_spread'] >= 3) &
        (df['spread'] >= 0.02) &
        (df['spread'] <= 0.15) &
        (df['yes_price'] >= 0.15) &
        (df['no_price'] >= 0.15) &
        (pd.to_datetime(df['end']) > max_days_from_now)
    ]

    # Sort the filtered DataFrame by rewards_daily_rate in descending order
    sorted_df = filtered_df.sort_values(by='rewards_daily_rate', ascending=False)

    # Write the filtered and sorted DataFrame to a new CSV file
    sorted_df.to_csv(output_file, sep='|', index=False)

    # Get the top condition_id values
    top_condition_ids = sorted_df['condition_id'].head(num_of_events).tolist()

    return top_condition_ids

# Process the events and get the top condition IDs
# top_ids = get_top_events(5)
# print("Top condition IDs:", top_ids)
