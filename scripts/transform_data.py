"""
Data Transformation and Feature Engineering for Lahore Temperature Prediction
This module handles cleaning, feature engineering, and data profiling.
"""

import json
import pandas as pd
import numpy as np
from datetime import datetime, timezone
from pathlib import Path


def load_raw_data(raw_data_path):
    """Load raw JSON data from file"""
    with open(raw_data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data


def clean_and_flatten_data(data):
    """
    Clean and flatten the nested JSON structure into a flat DataFrame.
    Extracts all relevant weather features.
    """
    forecast_list = data['list']
    
    # Initialize list to store flattened records
    records = []
    
    for item in forecast_list:
        record = {
            # Timestamp features
            'timestamp': pd.to_datetime(item['dt_txt']),
            'dt_unix': item['dt'],
            
            # Temperature features (from main)
            'temp': item['main']['temp'],
            'feels_like': item['main']['feels_like'],
            'temp_min': item['main']['temp_min'],
            'temp_max': item['main']['temp_max'],
            
            # Atmospheric features
            'pressure': item['main']['pressure'],
            'humidity': item['main']['humidity'],
            'sea_level': item['main'].get('sea_level', None),
            'grnd_level': item['main'].get('grnd_level', None),
            
            # Weather condition
            'weather_main': item['weather'][0]['main'],
            'weather_description': item['weather'][0]['description'],
            'weather_id': item['weather'][0]['id'],
            
            # Cloud coverage
            'clouds_all': item['clouds']['all'],
            
            # Wind features
            'wind_speed': item['wind']['speed'],
            'wind_deg': item['wind']['deg'],
            'wind_gust': item['wind'].get('gust', 0),
            
            # Other features
            'visibility': item.get('visibility', None),
            'pop': item.get('pop', 0),  # Probability of precipitation
            'pod': item['sys']['pod'],  # Part of day (n=night, d=day)
        }
        records.append(record)
    
    df = pd.DataFrame(records)
    
    # Sort by timestamp
    df = df.sort_values('timestamp').reset_index(drop=True)
    
    return df


def engineer_time_series_features(df):
    """
    Create time-series features for 4-hour ahead temperature prediction.
    Features include:
    - Lag features (previous temperature values)
    - Rolling statistics (mean, std, min, max)
    - Time-based features (hour, day of week, etc.)
    - Cyclical encodings (sin/cos for hour, day)
    """
    # Make a copy to avoid modifying original
    df_features = df.copy()
    
    # ===== TIME-BASED FEATURES =====
    df_features['hour'] = df_features['timestamp'].dt.hour
    df_features['day_of_week'] = df_features['timestamp'].dt.dayofweek
    df_features['day_of_month'] = df_features['timestamp'].dt.day
    df_features['month'] = df_features['timestamp'].dt.month
    df_features['is_weekend'] = (df_features['day_of_week'] >= 5).astype(int)
    
    # Cyclical encoding for hour (0-23) - helps model understand time cycles
    df_features['hour_sin'] = np.sin(2 * np.pi * df_features['hour'] / 24)
    df_features['hour_cos'] = np.cos(2 * np.pi * df_features['hour'] / 24)
    
    # Cyclical encoding for day of week (0-6)
    df_features['dow_sin'] = np.sin(2 * np.pi * df_features['day_of_week'] / 7)
    df_features['dow_cos'] = np.cos(2 * np.pi * df_features['day_of_week'] / 7)
    
    # Cyclical encoding for month (1-12)
    df_features['month_sin'] = np.sin(2 * np.pi * df_features['month'] / 12)
    df_features['month_cos'] = np.cos(2 * np.pi * df_features['month'] / 12)
    
    # Part of day (already have 'pod', but encode as numeric)
    df_features['is_day'] = (df_features['pod'] == 'd').astype(int)
    
    # ===== LAG FEATURES =====
    # Temperature lags (previous values)
    df_features['temp_lag_1'] = df_features['temp'].shift(1)  # 3 hours ago (since data is 3-hourly)
    df_features['temp_lag_2'] = df_features['temp'].shift(2)  # 6 hours ago
    df_features['temp_lag_3'] = df_features['temp'].shift(3)  # 9 hours ago
    df_features['temp_lag_4'] = df_features['temp'].shift(4)  # 12 hours ago
    
    # Pressure and humidity lags
    df_features['pressure_lag_1'] = df_features['pressure'].shift(1)
    df_features['humidity_lag_1'] = df_features['humidity'].shift(1)
    df_features['wind_speed_lag_1'] = df_features['wind_speed'].shift(1)
    
    # ===== ROLLING STATISTICS =====
    # Rolling mean (moving average) - helps capture trends
    window_3 = 3  # 9 hours (3 data points)
    window_6 = 6  # 18 hours (6 data points)
    
    df_features['temp_rolling_mean_3'] = df_features['temp'].rolling(window=window_3, min_periods=1).mean()
    df_features['temp_rolling_mean_6'] = df_features['temp'].rolling(window=window_6, min_periods=1).mean()
    df_features['temp_rolling_std_3'] = df_features['temp'].rolling(window=window_3, min_periods=1).std()
    df_features['temp_rolling_min_3'] = df_features['temp'].rolling(window=window_3, min_periods=1).min()
    df_features['temp_rolling_max_3'] = df_features['temp'].rolling(window=window_3, min_periods=1).max()
    
    # Rolling statistics for other features
    df_features['pressure_rolling_mean_3'] = df_features['pressure'].rolling(window=window_3, min_periods=1).mean()
    df_features['humidity_rolling_mean_3'] = df_features['humidity'].rolling(window=window_3, min_periods=1).mean()
    
    # ===== DIFFERENCE FEATURES =====
    # Temperature change (rate of change)
    df_features['temp_diff_1'] = df_features['temp'].diff(1)  # Change from previous
    df_features['temp_diff_2'] = df_features['temp'].diff(2)  # Change from 2 steps ago
    
    # Pressure change (can indicate weather changes)
    df_features['pressure_diff_1'] = df_features['pressure'].diff(1)
    
    # ===== INTERACTION FEATURES =====
    # Temperature-pressure interaction
    df_features['temp_pressure_interaction'] = df_features['temp'] * df_features['pressure']
    
    # Temperature-humidity interaction
    df_features['temp_humidity_interaction'] = df_features['temp'] * df_features['humidity']
    
    # Wind chill effect (simplified)
    df_features['wind_chill_effect'] = df_features['temp'] - (df_features['wind_speed'] * 0.5)
    
    # ===== TARGET VARIABLE =====
    # For 4-hour ahead prediction, we need to shift target by appropriate amount
    # Since data is 3-hourly, 4 hours ahead is approximately 1-2 steps ahead
    # We'll use 2 steps ahead (6 hours, closest to 4 hours)
    df_features['target_temp_4h'] = df_features['temp'].shift(-2)  # 6 hours ahead (closest to 4h)
    
    # Also create 1-step ahead for comparison
    df_features['target_temp_3h'] = df_features['temp'].shift(-1)  # 3 hours ahead
    
    # ===== FEATURE ENGINEERING SUMMARY =====
    print(f"\nFeature Engineering Summary:")
    print(f"  Original features: {len(df.columns)}")
    print(f"  Engineered features: {len(df_features.columns)}")
    print(f"  Total features: {len(df_features.columns)}")
    print(f"  Rows: {len(df_features)}")
    
    # Show feature categories
    lag_features = [col for col in df_features.columns if 'lag' in col]
    rolling_features = [col for col in df_features.columns if 'rolling' in col]
    time_features = [col for col in df_features.columns if col in ['hour', 'day_of_week', 'month', 'hour_sin', 'hour_cos']]
    
    print(f"\n  Feature Categories:")
    print(f"    - Lag features: {len(lag_features)}")
    print(f"    - Rolling features: {len(rolling_features)}")
    print(f"    - Time features: {len(time_features)}")
    
    return df_features


def save_processed_data(df, output_path):
    """Save processed DataFrame to CSV and Parquet formats"""
    # Save as CSV (human-readable)
    csv_path = output_path.with_suffix('.csv')
    df.to_csv(csv_path, index=False)
    print(f"  Saved CSV: {csv_path}")
    
    # Save as Parquet (efficient, preserves data types)
    parquet_path = output_path.with_suffix('.parquet')
    df.to_parquet(parquet_path, index=False, engine='pyarrow')
    print(f"  Saved Parquet: {parquet_path}")
    
    return csv_path, parquet_path


def transform_weather_data(raw_data_path, processed_data_dir):
    """
    Main transformation function that orchestrates the entire transformation pipeline.
    
    Args:
        raw_data_path: Path to raw JSON data file
        processed_data_dir: Directory to save processed data
    
    Returns:
        Path to processed data file
    """
    print(f"\n{'='*60}")
    print("TRANSFORMATION AND FEATURE ENGINEERING")
    print(f"{'='*60}\n")
    
    # Step 1: Load raw data
    print("Step 1: Loading raw data...")
    data = load_raw_data(raw_data_path)
    print(f"  Loaded {len(data['list'])} forecast entries")
    
    # Step 2: Clean and flatten
    print("\nStep 2: Cleaning and flattening data...")
    df_clean = clean_and_flatten_data(data)
    print(f"  Created DataFrame with {len(df_clean)} rows and {len(df_clean.columns)} columns")
    
    # Step 3: Feature engineering
    print("\nStep 3: Engineering time-series features...")
    df_features = engineer_time_series_features(df_clean)
    
    # Step 4: Save processed data
    print("\nStep 4: Saving processed data...")
    processed_data_dir = Path(processed_data_dir)
    processed_data_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp_str = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
    output_filename = f'lahore_weather_processed_{timestamp_str}'
    output_path = processed_data_dir / output_filename
    
    csv_path, parquet_path = save_processed_data(df_features, output_path)
    
    print(f"\n{'='*60}")
    print("TRANSFORMATION COMPLETE")
    print(f"{'='*60}\n")
    
    return str(parquet_path), df_features

