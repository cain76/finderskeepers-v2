#!/usr/bin/env python3
"""
Integration test script for the diary API ingestion module.

This module defines lightweight asynchronous tests that verify the core
ingestion components:

* Importing key models, the format detector, the storage service, and the
  main ingestion service.
* Detecting the file format of a temporary document and reporting the chosen
  processing method and metadata.
* Performing a storage health check to validate connectivity to the backend
  storage system.

Running this script executes all tests sequentially and prints a summary of
the results.
"""

import os
import sys
import asyncio
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

async def test_basic_imports():
    """Test basic module imports"""
    print("🧪 Testing ingestion module imports...")
    
    try:
        # Test basic models
        from app.api.v1.ingestion.models import (
            IngestionRequest, IngestionStatus, FileFormat, ProcessingMethod
        )
        print("✅ Models imported successfully")
        
        # Test format detector
        from app.api.v1.ingestion.format_detector import FormatDetector
        detector = FormatDetector()
        print("✅ Format detector imported successfully")
        
        # Test storage service
        from app.api.v1.ingestion.storage import StorageService
        storage = StorageService()
        print("✅ Storage service imported successfully")
        
        # Test the main service (may fail if processors have missing deps)
        try:
            from app.api.v1.ingestion.services import IngestionService
            ingestion = IngestionService()
            print("✅ Ingestion service imported successfully")
        except Exception as e:
            print(f"⚠️  Ingestion service failed (expected with missing deps): {e}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

async def test_format_detection():
    """Test format detection functionality"""
    print("\n🧪 Testing format detection...")
    
    try:
        from app.api.v1.ingestion.format_detector import FormatDetector
        detector = FormatDetector()
        
        # Create test file
        test_file = Path("/tmp/test_document.txt")
        test_file.write_text("This is a test document.")
        
        # Test detection
        format_type, method, metadata = detector.detect_format(str(test_file))
        
        print(f"✅ Detected format: {format_type}")
        print(f"✅ Processing method: {method}")
        print(f"✅ Metadata: {metadata}")
        
        # Cleanup
        test_file.unlink()
        
        return True
        
    except Exception as e:
        print(f"❌ Format detection failed: {e}")
        return False

async def test_storage_health():
    """Test storage service health check"""
    print("\n🧪 Testing storage health check...")
    
    try:
        from app.api.v1.ingestion.storage import StorageService
        storage = StorageService()
        
        # Test health check (will likely fail in test environment)
        health = await storage.health_check()
        print(f"📊 Storage health: {health}")
        
        return True
        
    except Exception as e:
        print(f"❌ Storage health check failed: {e}")
        return False

async def main():
    """Run all tests"""
    print("🚀 FindersKeepers v2 Ingestion Module Test")
    print("=" * 50)
    
    tests = [
        test_basic_imports,
        test_format_detection,
        test_storage_health
    ]
    
    results = []
    
    for test in tests:
        try:
            result = await test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            results.append(False)
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {sum(results)}/{len(results)} passed")
    
    if all(results):
        print("🎉 All tests passed! Ingestion module is ready.")
        return 0
    else:
        print("⚠️  Some tests failed. Check dependencies.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
