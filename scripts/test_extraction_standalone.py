"""
Standalone test script for extraction and quality check - NO Airflow required
Tests the core functions directly without importing Airflow.
"""

import os
import sys
import requests
import json
import pandas as pd
from datetime import datetime, timezone
from pathlib import Path

# Configuration (same as DAG)
PROJECT_ROOT = Path(__file__).parent.parent
API_KEY = 'f1f8d5f1208905c5a795ba04a171acdf'
CITY = 'Lahore'
COUNTRY_CODE = 'PK'
RAW_DATA_DIR = PROJECT_ROOT / 'raw_data'
OPENWEATHER_BASE_URL = 'https://api.openweathermap.org/data/2.5'

# Ensure raw_data directory exists
RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)


def fetch_weather_data_standalone():
    """Extract weather data without Airflow dependencies"""
    try:
        url = f'{OPENWEATHER_BASE_URL}/forecast'
        params = {
            'q': f'{CITY},{COUNTRY_CODE}',
            'appid': API_KEY,
            'units': 'metric'
        }
        
        print(f"Fetching weather data for {CITY} from OpenWeather API...")
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        if 'list' not in data or 'city' not in data:
            raise ValueError(f"Invalid API response structure: {list(data.keys())}")
        
        collection_time = datetime.now(timezone.utc)
        timestamp_str = collection_time.strftime('%Y%m%d_%H%M%S')
        
        data['_metadata'] = {
            'collection_time_utc': collection_time.isoformat(),
            'city': CITY,
            'country_code': COUNTRY_CODE,
            'api_endpoint': url,
            'total_forecasts': len(data.get('list', []))
        }
        
        filename = f'lahore_weather_raw_{timestamp_str}.json'
        filepath = RAW_DATA_DIR / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"[OK] Successfully fetched and saved raw data to: {filepath}")
        print(f"  Total forecast entries: {len(data.get('list', []))}")
        
        return str(filepath), data
        
    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to fetch data from OpenWeather API: {str(e)}")
    except Exception as e:
        raise Exception(f"Unexpected error during data extraction: {str(e)}")


def data_quality_check_standalone(raw_data_path, data=None):
    """Quality check without Airflow dependencies"""
    try:
        print(f"\nRunning data quality check on: {raw_data_path}")
        
        # Load data if not provided
        if data is None:
            with open(raw_data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        
        required_keys = ['list', 'city']
        missing_keys = [key for key in required_keys if key not in data]
        if missing_keys:
            raise ValueError(f"Quality check failed: Missing required keys: {missing_keys}")
        
        forecast_list = data['list']
        if not forecast_list or len(forecast_list) == 0:
            raise ValueError("Quality check failed: No forecast data in response")
        
        df = pd.DataFrame(forecast_list)
        
        if 'main' not in df.columns:
            raise ValueError("Quality check failed: 'main' key missing from forecast data")
        
        df_main = pd.json_normalize(df['main'])
        
        key_columns = {
            'temp': 'Temperature',
            'feels_like': 'Feels Like Temperature',
            'pressure': 'Pressure',
            'humidity': 'Humidity'
        }
        
        quality_report = []
        quality_passed = True
        
        print("\n" + "="*60)
        print("DATA QUALITY CHECK REPORT")
        print("="*60)
        
        for col, display_name in key_columns.items():
            if col not in df_main.columns:
                print(f"[WARNING] Column '{col}' ({display_name}) not found in data")
                continue
            
            null_count = df_main[col].isnull().sum()
            total_count = len(df_main[col])
            null_percentage = (null_count / total_count) * 100 if total_count > 0 else 100
            
            if null_percentage > 1.0:
                quality_passed = False
                error_msg = (
                    f"[FAIL] QUALITY CHECK FAILED: {display_name} ({col}) has "
                    f"{null_percentage:.2f}% null values (threshold: 1.0%)\n"
                    f"   Null count: {null_count}/{total_count}"
                )
                print(error_msg)
                quality_report.append(error_msg)
            else:
                success_msg = (
                    f"[PASS] {display_name} ({col}) - "
                    f"{null_percentage:.2f}% null ({null_count}/{total_count} null)"
                )
                print(success_msg)
                quality_report.append(success_msg)
            
            if col == 'temp' and not df_main[col].isnull().all():
                min_temp = df_main[col].min()
                max_temp = df_main[col].max()
                if min_temp < -10 or max_temp > 50:
                    print(f"[WARNING] Temperature values outside expected range: {min_temp:.1f}C to {max_temp:.1f}C")
        
        required_fields = ['dt', 'main', 'weather']
        missing_fields = [field for field in required_fields if field not in df.columns]
        if missing_fields:
            quality_passed = False
            error_msg = f"[FAIL] QUALITY CHECK FAILED: Missing required fields: {missing_fields}"
            print(error_msg)
            quality_report.append(error_msg)
        
        min_required_forecasts = 5
        if len(forecast_list) < min_required_forecasts:
            quality_passed = False
            error_msg = (
                f"❌ QUALITY CHECK FAILED: Insufficient forecast data points. "
                f"Found: {len(forecast_list)}, Required: {min_required_forecasts}"
            )
            print(error_msg)
            quality_report.append(error_msg)
        
        print("="*60)
        
        if not quality_passed:
            print("\n[FAIL] DATA QUALITY CHECK FAILED")
            print("\nQuality Report Summary:")
            for report_line in quality_report:
                print(f"  {report_line}")
            return False
        else:
            print("\n[PASS] DATA QUALITY CHECK PASSED - Proceeding to next step")
            print(f"  Total forecast entries validated: {len(forecast_list)}")
            return True
        
    except Exception as e:
        print(f"\n[ERROR] Quality check error: {str(e)}")
        return False


def main():
    """Main test function"""
    print("\n" + "="*60)
    print("LAHORE TEMPERATURE PREDICTION - EXTRACTION TEST (STANDALONE)")
    print("="*60 + "\n")
    
    try:
        # Test extraction
        print("="*60)
        print("TESTING WEATHER DATA EXTRACTION")
        print("="*60)
        
        filepath, data = fetch_weather_data_standalone()
        print(f"\n[OK] Extraction successful!")
        print(f"  Raw data saved to: {filepath}")
        
        # Test quality check
        print("\n" + "="*60)
        print("TESTING DATA QUALITY CHECK")
        print("="*60)
        
        quality_result = data_quality_check_standalone(filepath, data)
        
        print("\n" + "="*60)
        if quality_result:
            print("[SUCCESS] ALL TESTS PASSED - Ready for Airflow deployment")
            print("="*60 + "\n")
            return 0
        else:
            print("[FAIL] TESTS FAILED - Please check errors above")
            print("="*60 + "\n")
            return 1
            
    except Exception as e:
        print(f"\n[ERROR] Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        print("="*60 + "\n")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

