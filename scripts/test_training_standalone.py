"""
Standalone Test Script for Model Training (Step 4)
Tests model training and MLflow integration without Airflow.
"""

import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.append(str(PROJECT_ROOT))

from train import train_and_log_experiment, run_multiple_experiments


def test_single_training():
    """Test single model training with MLflow tracking."""
    print("\n" + "="*60)
    print("TEST: Single Model Training")
    print("="*60 + "\n")
    
    try:
        result = train_and_log_experiment(
            model_type='random_forest',
            hyperparams={
                'n_estimators': 50,
                'max_depth': 5,
                'random_state': 42
            },
            run_name='test_rf_single'
        )
        
        print("\n[OK] Single training test passed!")
        print(f"  Run ID: {result['run_id']}")
        print(f"  Test RMSE: {result['metrics']['test_rmse']:.4f}")
        
        return True
        
    except Exception as e:
        print(f"\n[ERROR] Single training test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_multiple_experiments_training():
    """Test multiple experiments with different hyperparameters."""
    print("\n" + "="*60)
    print("TEST: Multiple Experiments")
    print("="*60 + "\n")
    
    try:
        results, best_result = run_multiple_experiments()
        
        print("\n[OK] Multiple experiments test passed!")
        print(f"  Total experiments: {len(results)}")
        print(f"  Best RMSE: {best_result['metrics']['test_rmse']:.4f}")
        
        return True
        
    except Exception as e:
        print(f"\n[ERROR] Multiple experiments test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all training tests."""
    print("\n" + "="*70)
    print("STANDALONE TRAINING TEST SUITE (PHASE II - STEP 4)")
    print("="*70 + "\n")
    
    print("This script tests:")
    print("  1. Model training with MLflow tracking")
    print("  2. Experiment logging (hyperparameters, metrics, models)")
    print("  3. Multiple experiments comparison")
    print("\n" + "="*70 + "\n")
    
    # Check if processed data exists
    processed_data_dir = PROJECT_ROOT / 'processed_data'
    if not processed_data_dir.exists() or not list(processed_data_dir.glob('*.parquet')):
        print("[ERROR] No processed data found!")
        print("  Please run the ETL pipeline first (Steps 2.1-2.3)")
        print("  Or run: python scripts/test_extraction_standalone.py")
        return
    
    print(f"[OK] Found processed data in: {processed_data_dir}\n")
    
    # Run tests
    tests = [
        ("Single Model Training", test_single_training),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\nRunning: {test_name}...")
        success = test_func()
        results.append((test_name, success))
    
    # Print summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70 + "\n")
    
    for test_name, success in results:
        status = "[OK]" if success else "[ERROR]"
        print(f"  {status} {test_name}")
    
    all_passed = all(success for _, success in results)
    
    if all_passed:
        print("\n" + "="*70)
        print("ALL TESTS PASSED!")
        print("="*70 + "\n")
        print("Next steps:")
        print("  1. Check MLflow UI to view logged experiments")
        print("  2. If using local MLflow: mlflow ui --backend-store-uri file:./mlruns")
        print("  3. If using Dagshub: Visit your Dagshub repository > Experiments tab")
        print("  4. Run multiple experiments: python scripts/train.py --multiple")
    else:
        print("\n" + "="*70)
        print("SOME TESTS FAILED")
        print("="*70 + "\n")
        print("Please check the error messages above.")


if __name__ == "__main__":
    main()

