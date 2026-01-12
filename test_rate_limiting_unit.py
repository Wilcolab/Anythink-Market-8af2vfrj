"""
Unit tests for rate limiting functionality.

This test suite validates the rate limiting configuration without requiring
a running server or external dependencies.
"""

import sys
import pytest
from unittest.mock import Mock, patch
from fastapi import Request, Response
from fastapi.testclient import TestClient
from slowapi.errors import RateLimitExceeded

# Test imports
def test_slowapi_import():
    """Test that slowapi is properly installed"""
    try:
        from slowapi import Limiter
        from slowapi.util import get_remote_address
        from slowapi.errors import RateLimitExceeded
        print("✓ slowapi imports successful")
        return True
    except ImportError as e:
        print(f"✗ slowapi import failed: {e}")
        return False


def test_middleware_import():
    """Test that rate limiter middleware can be imported"""
    try:
        from app.middleware.rate_limiter import limiter, rate_limit_exceeded_handler, RATE_LIMITS
        print("✓ Rate limiter middleware imports successful")
        print(f"  Rate limits configured: {list(RATE_LIMITS.keys())}")
        return True
    except ImportError as e:
        print(f"✗ Rate limiter import failed: {e}")
        return False


def test_rate_limits_configuration():
    """Test that rate limits are properly configured"""
    try:
        from app.middleware.rate_limiter import RATE_LIMITS
        
        expected_limits = {
            "llm": "10/minute",
            "auth": "5/minute",
            "user_info": "30/minute",
            "health": "120/minute",
        }
        
        for key, expected_value in expected_limits.items():
            if key not in RATE_LIMITS:
                print(f"✗ Missing rate limit: {key}")
                return False
            if RATE_LIMITS[key] != expected_value:
                print(f"✗ Incorrect rate limit for {key}: expected {expected_value}, got {RATE_LIMITS[key]}")
                return False
        
        print("✓ All rate limits properly configured")
        for key, value in RATE_LIMITS.items():
            print(f"  {key}: {value}")
        return True
        
    except Exception as e:
        print(f"✗ Rate limits configuration test failed: {e}")
        return False


def test_limiter_initialization():
    """Test that the limiter is properly initialized"""
    try:
        from app.middleware.rate_limiter import limiter
        from slowapi import Limiter
        
        if not isinstance(limiter, Limiter):
            print("✗ limiter is not a Limiter instance")
            return False
        
        print("✓ Limiter properly initialized")
        return True
        
    except Exception as e:
        print(f"✗ Limiter initialization test failed: {e}")
        return False


def test_error_handler():
    """Test that the error handler is properly defined"""
    try:
        from app.middleware.rate_limiter import rate_limit_exceeded_handler
        
        # Create mock request
        mock_request = Mock(spec=Request)
        mock_request.url.path = "/test"
        mock_request.client.host = "127.0.0.1"
        
        # Create mock exception with detail attribute
        mock_exc = Mock()
        mock_exc.detail = "10 per 1 minute"
        
        # Call error handler
        response = rate_limit_exceeded_handler(mock_request, mock_exc)
        
        if response.status_code != 429:
            print(f"✗ Error handler returned wrong status code: {response.status_code}")
            return False
        
        print("✓ Error handler properly configured")
        print(f"  Returns status code: 429")
        return True
        
    except Exception as e:
        print(f"✗ Error handler test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_main_app_integration():
    """Test that main.py properly integrates rate limiting"""
    try:
        import os
        # Use relative path from current directory
        main_py_path = os.path.join(os.path.dirname(__file__), 'app', 'main.py')
        
        with open(main_py_path, 'r') as f:
            content = f.read()
        
        required_imports = [
            'from slowapi.errors import RateLimitExceeded',
            'from app.middleware.rate_limiter import limiter, rate_limit_exceeded_handler',
        ]
        
        required_code = [
            'app.state.limiter = limiter',
            'app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)',
            '@limiter.limit("120/minute")',
        ]
        
        for import_stmt in required_imports:
            if import_stmt not in content:
                print(f"✗ Missing import in main.py: {import_stmt}")
                return False
        
        for code_stmt in required_code:
            if code_stmt not in content:
                print(f"✗ Missing code in main.py: {code_stmt}")
                return False
        
        print("✓ main.py properly integrates rate limiting")
        return True
        
    except Exception as e:
        print(f"✗ main.py integration test failed: {e}")
        return False


def test_api_routes_integration():
    """Test that api/routes.py properly applies rate limiting"""
    try:
        import os
        import re
        
        api_routes_path = os.path.join(os.path.dirname(__file__), 'app', 'api', 'routes.py')
        
        with open(api_routes_path, 'r') as f:
            content = f.read()
        
        required_imports = [
            'Request',  # Check Request is imported
            'from app.middleware.rate_limiter import limiter',
        ]
        
        for import_stmt in required_imports:
            if import_stmt not in content:
                print(f"✗ Missing import in api/routes.py: {import_stmt}")
                return False
        
        # Use regex for more flexible matching
        if not re.search(r'@limiter\.limit\(["\']10/minute["\']\)', content):
            print("✗ Missing 10/minute rate limit in api/routes.py")
            return False
        
        if not re.search(r'@limiter\.limit\(["\']30/minute["\']\)', content):
            print("✗ Missing 30/minute rate limit in api/routes.py")
            return False
        
        # Check that secure_query has Request parameter
        if not re.search(r'async def secure_query\([^)]*request:\s*Request', content, re.DOTALL):
            print("✗ secure_query missing Request parameter")
            return False
        
        # Check that get_current_user_info has Request parameter
        if not re.search(r'async def get_current_user_info\([^)]*request:\s*Request', content, re.DOTALL):
            print("✗ get_current_user_info missing Request parameter")
            return False
        
        print("✓ api/routes.py properly applies rate limiting")
        return True
        
    except Exception as e:
        print(f"✗ api/routes.py integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_auth_routes_integration():
    """Test that auth/routes.py properly applies rate limiting"""
    try:
        import os
        import re
        
        auth_routes_path = os.path.join(os.path.dirname(__file__), 'app', 'auth', 'routes.py')
        
        with open(auth_routes_path, 'r') as f:
            content = f.read()
        
        required_imports = [
            'Request',  # Check Request is imported
            'from app.middleware.rate_limiter import limiter',
        ]
        
        for import_stmt in required_imports:
            if import_stmt not in content:
                print(f"✗ Missing import in auth/routes.py: {import_stmt}")
                return False
        
        # Use regex for more flexible matching
        if not re.search(r'@limiter\.limit\(["\']5/minute["\']\)', content):
            print("✗ Missing 5/minute rate limit in auth/routes.py")
            return False
        
        # Check that login_for_access_token has Request parameter
        if not re.search(r'async def login_for_access_token\([^)]*request:\s*Request', content, re.DOTALL):
            print("✗ login_for_access_token missing Request parameter")
            return False
        
        print("✓ auth/routes.py properly applies rate limiting")
        return True
        
    except Exception as e:
        print(f"✗ auth/routes.py integration test failed: {e}")
        return False


def test_files_created():
    """Test that all required files were created"""
    import os
    
    base_dir = os.path.dirname(__file__)
    
    required_files = [
        'app/middleware/__init__.py',
        'app/middleware/rate_limiter.py',
        'test_rate_limiting.py',
        'RATE_LIMITING_GUIDE.md',
        'RATE_LIMITING_PR.md',
    ]
    
    all_exist = True
    for filepath in required_files:
        full_path = os.path.join(base_dir, filepath)
        if not os.path.exists(full_path):
            print(f"✗ Missing file: {filepath}")
            all_exist = False
    
    if all_exist:
        print("✓ All required files created")
        for filepath in required_files:
            filename = os.path.basename(filepath)
            print(f"  {filename}")
    
    return all_exist


def run_all_tests():
    """Run all unit tests"""
    print("=" * 80)
    print("RATE LIMITING UNIT TESTS")
    print("=" * 80)
    print()
    
    tests = [
        ("slowapi Import", test_slowapi_import),
        ("Middleware Import", test_middleware_import),
        ("Rate Limits Configuration", test_rate_limits_configuration),
        ("Limiter Initialization", test_limiter_initialization),
        ("Error Handler", test_error_handler),
        ("main.py Integration", test_main_app_integration),
        ("api/routes.py Integration", test_api_routes_integration),
        ("auth/routes.py Integration", test_auth_routes_integration),
        ("Required Files", test_files_created),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\nTest: {test_name}")
        print("-" * 80)
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ Test failed with exception: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
        print()
    
    # Print summary
    print("=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {total} | Passed: {passed} | Failed: {total - passed}")
    print(f"Success Rate: {(passed/total*100):.1f}%")
    print("=" * 80)
    
    return passed == total


def main():
    """Main entry point"""
    try:
        success = run_all_tests()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ ERROR running tests: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
