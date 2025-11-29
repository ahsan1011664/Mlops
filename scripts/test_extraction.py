"""
Test script to verify weather data extraction and quality check functions
without running Airflow. Useful for development and debugging.
"""

import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.append(str(PROJECT_ROOT))

# Import functions from DAG
from dags.lahore_temperature_prediction_dag import fetch_weather_data, data_quality_check


def test_extraction():
    """Test the extraction function"""
    print("="*60)
    print("TESTING WEATHER DATA EXTRACTION")
    print("="*60)
    
    # Create a mock context object
    class MockTI:
        def __init__(self):
            self.xcom_data = {}
        
        def xcom_push(self, key, value):
            self.xcom_data[key] = value
            print(f"  XCom push: {key} = {value}")
        
        def xcom_pull(self, task_ids, key):
            return self.xcom_data.get(key)
    
    class MockContext:
        def __init__(self):
            self.ti = MockTI()
    
    context = MockContext()
    
    try:
        # Test extraction
        result = fetch_weather_data(**{'ti': context.ti})
        print(f"\n✓ Extraction successful!")
        print(f"  Raw data saved to: {result}")
        
        # Test quality check
        print("\n" + "="*60)
        print("TESTING DATA QUALITY CHECK")
        print("="*60)
        
        quality_result = data_quality_check(**{'ti': context.ti})
        
        if quality_result:
            print("\n✓ All tests passed!")
            return True
        else:
            print("\n❌ Quality check failed!")
            return False
            
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\n" + "="*60)
    print("LAHORE TEMPERATURE PREDICTION - EXTRACTION TEST")
    print("="*60 + "\n")
    
    success = test_extraction()
    
    print("\n" + "="*60)
    if success:
        print("✓ ALL TESTS PASSED - Ready for Airflow deployment")
    else:
        print("❌ TESTS FAILED - Please check errors above")
    print("="*60 + "\n")
    
    sys.exit(0 if success else 1)

