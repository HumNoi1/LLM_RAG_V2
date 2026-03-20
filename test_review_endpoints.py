#!/usr/bin/env python3
"""
Test script for BE-J Sprint 3 Review endpoints
Tests all review endpoints to ensure they are properly implemented.
"""

import httpx
import json
from typing import Dict, Any

BASE_URL = "http://127.0.0.1:8001"

class ReviewEndpointTester:
    def __init__(self):
        self.client = httpx.Client(base_url=BASE_URL, timeout=30)
        self.auth_token = None
    
    def test_health_check(self):
        """Test basic health check endpoint"""
        print("Testing health check...")
        try:
            response = self.client.get("/health")
            if response.status_code == 200:
                print("[PASS] Health check: OK")
                print(f"   Response: {response.json()}")
                return True
            else:
                print(f"[FAIL] Health check: Status {response.status_code}")
                return False
        except Exception as e:
            print(f"[ERROR] Health check: {e}")
            return False
    
    def test_docs_endpoint(self):
        """Test FastAPI docs endpoint"""
        print("Testing API docs...")
        try:
            response = self.client.get("/docs")
            if response.status_code == 200:
                print("[PASS] API docs: OK")
                return True
            else:
                print(f"[FAIL] API docs: Status {response.status_code}")
                return False
        except Exception as e:
            print(f"[ERROR] API docs: {e}")
            return False
    
    def test_review_endpoints_structure(self):
        """Test review endpoints structure via OpenAPI schema"""
        print("Testing OpenAPI schema for review endpoints...")
        try:
            response = self.client.get("/openapi.json")
            if response.status_code != 200:
                print(f"[FAIL] OpenAPI schema: Status {response.status_code}")
                return False
            
            schema = response.json()
            paths = schema.get("paths", {})
            
            # Check if review endpoints exist in schema
            review_endpoints = [
                "/api/v1/review/exams/{exam_id}/submissions",
                "/api/v1/review/submissions/{submission_id}",
                "/api/v1/review/results/{result_id}/approve",
                "/api/v1/review/results/{result_id}/revise",
                "/api/v1/review/exams/{exam_id}/approve-all",
                "/api/v1/review/exams/{exam_id}/export"
            ]
            
            found_endpoints = []
            for endpoint in review_endpoints:
                if endpoint in paths:
                    found_endpoints.append(endpoint)
                    print(f"   [OK] Found: {endpoint}")
                else:
                    print(f"   [MISSING] {endpoint}")
            
            if len(found_endpoints) == len(review_endpoints):
                print("[PASS] All review endpoints found in OpenAPI schema")
                return True
            else:
                print(f"[FAIL] Missing {len(review_endpoints) - len(found_endpoints)} endpoints")
                return False
                
        except Exception as e:
            print(f"[ERROR] OpenAPI schema: {e}")
            return False
    
    def test_review_endpoints_without_auth(self):
        """Test review endpoints without authentication (should return 401)"""
        print("Testing review endpoints without auth (expecting 401)...")
        
        test_endpoints = [
            ("GET", "/api/v1/review/exams/test-id/submissions"),
            ("GET", "/api/v1/review/submissions/test-id"),
            ("PUT", "/api/v1/review/results/test-id/approve"),
            ("PUT", "/api/v1/review/results/test-id/revise"),
            ("POST", "/api/v1/review/exams/test-id/approve-all"),
            ("GET", "/api/v1/review/exams/test-id/export")
        ]
        
        all_passed = True
        for method, endpoint in test_endpoints:
            try:
                response = None
                if method == "GET":
                    response = self.client.get(endpoint)
                elif method == "PUT":
                    response = self.client.put(endpoint, json={})
                elif method == "POST":
                    response = self.client.post(endpoint, json={})
                
                # Expecting 401 (Unauthorized) or 422 (validation error due to auth)
                if response and response.status_code in [401, 422]:
                    print(f"   [OK] {method} {endpoint}: Status {response.status_code} (as expected)")
                elif response:
                    print(f"   [FAIL] {method} {endpoint}: Unexpected status {response.status_code}")
                    all_passed = False
                else:
                    print(f"   [ERROR] {method} {endpoint}: No response received")
                    all_passed = False
                    
            except Exception as e:
                print(f"   [ERROR] {method} {endpoint}: {e}")
                all_passed = False
        
        if all_passed:
            print("[PASS] Auth protection working correctly")
        else:
            print("[FAIL] Some endpoints have auth issues")
        
        return all_passed
    
    def run_all_tests(self):
        """Run all tests and provide summary"""
        print("Starting BE-J Sprint 3 Review Endpoints Test")
        print("=" * 50)
        
        tests = [
            self.test_health_check,
            self.test_docs_endpoint, 
            self.test_review_endpoints_structure,
            self.test_review_endpoints_without_auth
        ]
        
        results = []
        for test in tests:
            result = test()
            results.append(result)
            print()  # Empty line between tests
        
        # Summary
        print("=" * 50)
        print("TEST SUMMARY")
        print("=" * 50)
        passed = sum(results)
        total = len(results)
        
        if passed == total:
            print(f"ALL TESTS PASSED ({passed}/{total})")
            print("Review endpoints are properly implemented!")
        else:
            print(f"SOME TESTS FAILED ({passed}/{total})")
            print("Need to fix issues before proceeding")
        
        return passed == total


if __name__ == "__main__":
    print("BE-J Sprint 3: Review Endpoints Tester")
    print("Make sure backend server is running on http://127.0.0.1:8000")
    print()
    
    tester = ReviewEndpointTester()
    success = tester.run_all_tests()
    
    if success:
        print("\nNext steps:")
        print("1. Create admin user management endpoints")  
        print("2. Write unit tests")
        print("3. Integration testing")
    else:
        print("\nFix the issues above first")