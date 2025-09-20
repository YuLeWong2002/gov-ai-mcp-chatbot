#!/usr/bin/env python3
"""
Complete Test Script for Government Vehicle Management System API
Tests all API endpoints with comprehensive validation
"""

import requests
import json
from datetime import date, datetime
import time
import sys

# Configuration
BASE_URL = "http://127.0.0.1:8000"
TIMEOUT = 30

class APITester:
    def __init__(self):
        self.base_url = BASE_URL
        self.passed = 0
        self.failed = 0
        self.test_vehicle = "TEST999X"
        self.test_ic = "990101019999"
        self.created_summons_id = None
    
    def log(self, test_name, success, message=""):
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if message:
            print(f"    → {message}")
        
        if success:
            self.passed += 1
        else:
            self.failed += 1
        return success
    
    def request(self, method, endpoint, expected_status=200, **kwargs):
        """Make HTTP request with error handling"""
        try:
            url = f"{self.base_url}{endpoint}"
            response = requests.request(method, url, timeout=TIMEOUT, **kwargs)
            
            if response.status_code != expected_status:
                return False, f"Expected {expected_status}, got {response.status_code}: {response.text[:200]}"
            
            try:
                return True, response.json()
            except:
                return True, response.text
        except requests.exceptions.ConnectionError:
            return False, "Connection failed - is the server running?"
        except Exception as e:
            return False, str(e)
    
    def test_root(self):
        """Test root endpoint"""
        success, data = self.request("GET", "/")
        if success and isinstance(data, dict) and 'message' in data:
            return self.log("Root Endpoint", True, f"API: {data.get('message')}")
        return self.log("Root Endpoint", False, str(data))
    
    def test_get_all_licenses(self):
        """Test getting all licenses"""
        success, data = self.request("GET", "/licenses/")
        if success and isinstance(data, list):
            return self.log("GET All Licenses", True, f"Found {len(data)} licenses")
        return self.log("GET All Licenses", False, str(data))
    
    def test_get_license_by_vehicle(self, vehicle_id="W 1234 A"):
        """Test getting license by vehicle ID"""
        success, data = self.request("GET", f"/licenses/{vehicle_id}")
        if success and isinstance(data, dict) and data.get('vehicle_id') == vehicle_id:
            return self.log(f"GET License ({vehicle_id})", True, f"Owner: {data.get('owner_name')}")
        return self.log(f"GET License ({vehicle_id})", False, str(data))
    
    def test_get_license_not_found(self):
        """Test getting non-existent license"""
        success, data = self.request("GET", "/licenses/NOTFOUND", expected_status=404)
        return self.log("GET License Not Found", success, "Correctly returned 404" if success else str(data))
    
    def test_get_licenses_by_ic(self, ic_number="900101-01-1234"):
        """Test getting licenses by IC"""
        success, data = self.request("GET", f"/licenses/ic/{ic_number}")
        if success and isinstance(data, list):
            return self.log(f"GET Licenses by IC ({ic_number})", True, f"Found {len(data)} vehicles")
        return self.log(f"GET Licenses by IC ({ic_number})", False, str(data))
    
    def test_get_expiring_licenses(self):
        """Test getting expiring licenses"""
        success, data = self.request("GET", "/licenses/expiring/365")
        if success and isinstance(data, list):
            return self.log("GET Expiring Licenses", True, f"Found {len(data)} expiring licenses")
        return self.log("GET Expiring Licenses", False, str(data))
    
    def test_create_license(self):
        """Test creating new license"""
        license_data = {
            "vehicle_id": self.test_vehicle,
            "owner_name": "Test User API",
            "ic_number": self.test_ic,
            "expiry_date": "2025-12-31",
            "renewal_fee": 100.0
        }
        
        success, data = self.request("POST", "/licenses/", json=license_data)
        if success and isinstance(data, dict) and data.get('vehicle_id') == self.test_vehicle:
            return self.log("CREATE License", True, f"Created for {data.get('owner_name')}")
        elif not success and "already exists" in str(data).lower():
            return self.log("CREATE License", True, "Already exists (expected for repeat tests)")
        return self.log("CREATE License", False, str(data))
    
    def test_update_license(self):
        """Test updating license"""
        update_data = {
            "vehicle_id": self.test_vehicle,
            "owner_name": "Test User Updated",
            "ic_number": self.test_ic,
            "expiry_date": "2025-12-31",
            "renewal_fee": 150.0
        }
        
        success, data = self.request("PUT", f"/licenses/{self.test_vehicle}", json=update_data)
        if success and isinstance(data, dict) and data.get('owner_name') == "Test User Updated":
            return self.log("UPDATE License", True, "Successfully updated")
        return self.log("UPDATE License", False, str(data))
    
    def test_get_all_summons(self):
        """Test getting all summons"""
        success, data = self.request("GET", "/summons/")
        if success and isinstance(data, list):
            return self.log("GET All Summons", True, f"Found {len(data)} summons")
        return self.log("GET All Summons", False, str(data))
    
    def test_get_summons_by_vehicle(self, vehicle_id="W 1234 A"):
        """Test getting summons by vehicle"""
        success, data = self.request("GET", f"/summons/{vehicle_id}")
        if success and isinstance(data, list):
            return self.log(f"GET Summons ({vehicle_id})", True, f"Found {len(data)} summons")
        return self.log(f"GET Summons ({vehicle_id})", False, str(data))
    
    def test_get_summons_by_status(self, status="Unpaid"):
        """Test getting summons by status"""
        success, data = self.request("GET", f"/summons/status/{status}")
        if success and isinstance(data, list):
            return self.log(f"GET Summons by Status ({status})", True, f"Found {len(data)} {status} summons")
        return self.log(f"GET Summons by Status ({status})", False, str(data))
    
    def test_create_summons(self):
        """Test creating summons"""
        # Ensure test vehicle exists first
        self.test_create_license()
        
        summons_data = {
            "vehicle_id": self.test_vehicle,
            "summons_type": "API Test Violation",
            "summons_date": str(date.today()),
            "amount": 50.0,
            "status": "Unpaid"
        }
        
        success, data = self.request("POST", "/summons/", json=summons_data)
        if success and isinstance(data, dict) and 'summons_id' in data:
            self.created_summons_id = data['summons_id']
            return self.log("CREATE Summons", True, f"Created summons ID {data['summons_id']}")
        return self.log("CREATE Summons", False, str(data))
    
    def test_pay_summons(self):
        """Test paying summons"""
        if not self.created_summons_id:
            return self.log("PAY Summons", False, "No summons ID available")
        
        success, data = self.request("PUT", f"/summons/{self.created_summons_id}/pay")
        if success and isinstance(data, dict) and 'message' in data:
            return self.log("PAY Summons", True, data['message'])
        return self.log("PAY Summons", False, str(data))
    
    def test_delete_summons(self):
        """Test deleting summons"""
        if not self.created_summons_id:
            return self.log("DELETE Summons", True, "No summons to delete (skipped)")
        
        success, data = self.request("DELETE", f"/summons/{self.created_summons_id}")
        if success:
            return self.log("DELETE Summons", True, "Successfully deleted")
        return self.log("DELETE Summons", False, str(data))
    
    def test_delete_license(self):
        """Test deleting license"""
        success, data = self.request("DELETE", f"/licenses/{self.test_vehicle}")
        if success:
            return self.log("DELETE License", True, "Successfully deleted")
        return self.log("DELETE License", False, str(data))
    
    def test_get_stats(self):
        """Test getting system statistics"""
        success, data = self.request("GET", "/stats/summary")
        if success and isinstance(data, dict):
            required_keys = ['total_licenses', 'total_summons', 'unpaid_summons', 'unpaid_amount']
            if all(key in data for key in required_keys):
                message = f"Licenses: {data['total_licenses']}, Summons: {data['total_summons']}, Unpaid: RM{data['unpaid_amount']:.2f}"
                return self.log("GET System Statistics", True, message)
        return self.log("GET System Statistics", False, str(data))
    
    def test_error_scenarios(self):
        """Test various error scenarios"""
        print("\n⚠️ ERROR HANDLING TESTS")
        print("-" * 40)
        
        # Test duplicate vehicle creation
        license_data = {
            "vehicle_id": "DUPLICATE_TEST",
            "owner_name": "Test User",
            "ic_number": "111222333444",
            "expiry_date": "2025-12-31",
            "renewal_fee": 100.0
        }
        
        # First creation
        success1, data1 = self.request("POST", "/licenses/", json=license_data)
        # Second creation should fail
        success2, data2 = self.request("POST", "/licenses/", json=license_data, expected_status=400)
        
        # Cleanup
        if success1:
            self.request("DELETE", "/licenses/DUPLICATE_TEST")
        
        if success1 and success2:
            self.log("Error - Duplicate Vehicle", True, "Correctly prevented duplicate")
        else:
            self.log("Error - Duplicate Vehicle", False, "Failed to handle duplicate")
        
        # Test summons for non-existent vehicle
        bad_summons = {
            "vehicle_id": "NONEXISTENT",
            "summons_type": "Test",
            "summons_date": str(date.today()),
            "amount": 50.0
        }
        
        success, data = self.request("POST", "/summons/", json=bad_summons, expected_status=400)
        self.log("Error - Nonexistent Vehicle Summons", success, 
                "Correctly returned 400" if success else str(data))
        
        # Test updating non-existent license
        update_data = {
            "vehicle_id": "NONEXISTENT",
            "owner_name": "Test",
            "ic_number": "123",
            "expiry_date": "2025-12-31",
            "renewal_fee": 100.0
        }
        
        success, data = self.request("PUT", "/licenses/NONEXISTENT", json=update_data, expected_status=404)
        self.log("Error - Update Nonexistent License", success,
                "Correctly returned 404" if success else str(data))
        
        # Test paying non-existent summons
        success, data = self.request("PUT", "/summons/99999/pay", expected_status=404)
        self.log("Error - Pay Nonexistent Summons", success,
                "Correctly returned 404" if success else str(data))
    
    def test_performance(self):
        """Test API performance"""
        print("\n⚡ PERFORMANCE TEST")
        print("-" * 40)
        
        endpoints = [
            ("GET", "/"),
            ("GET", "/licenses/"),
            ("GET", "/summons/"),
            ("GET", "/stats/summary"),
        ]
        
        times = []
        for method, endpoint in endpoints:
            start = time.time()
            success, data = self.request(method, endpoint)
            end = time.time()
            
            if success:
                times.append(end - start)
            else:
                return self.log("Performance Test", False, f"Failed on {endpoint}")
        
        avg_time = sum(times) / len(times)
        max_time = max(times)
        
        if avg_time < 3.0 and max_time < 10.0:
            self.log("Performance Test", True, f"Avg: {avg_time:.3f}s, Max: {max_time:.3f}s")
        else:
            self.log("Performance Test", False, f"Too slow - Avg: {avg_time:.3f}s, Max: {max_time:.3f}s")
    
    def test_lifecycle(self):
        """Test complete vehicle and summons lifecycle"""
        print("\n🔄 INTEGRATION TEST - Complete Lifecycle")
        print("-" * 40)
        
        test_vehicle = "LIFECYCLE_TEST"
        test_ic = "888777666555"
        
        # Step 1: Create license
        license_data = {
            "vehicle_id": test_vehicle,
            "owner_name": "Lifecycle Test User",
            "ic_number": test_ic,
            "expiry_date": "2025-12-31",
            "renewal_fee": 100.0
        }
        
        success1, data1 = self.request("POST", "/licenses/", json=license_data)
        if not success1:
            return self.log("Lifecycle Test", False, f"Failed to create license: {data1}")
        
        # Step 2: Create summons
        summons_data = {
            "vehicle_id": test_vehicle,
            "summons_type": "Lifecycle Test",
            "summons_date": str(date.today()),
            "amount": 75.0,
            "status": "Unpaid"
        }
        
        success2, data2 = self.request("POST", "/summons/", json=summons_data)
        if not success2:
            self.request("DELETE", f"/licenses/{test_vehicle}")
            return self.log("Lifecycle Test", False, f"Failed to create summons: {data2}")
        
        summons_id = data2.get('summons_id')
        
        # Step 3: Pay summons
        success3, data3 = self.request("PUT", f"/summons/{summons_id}/pay")
        
        # Step 4: Cleanup
        self.request("DELETE", f"/summons/{summons_id}")
        self.request("DELETE", f"/licenses/{test_vehicle}")
        
        if success1 and success2 and success3:
            self.log("Complete Lifecycle Test", True, "Successfully completed full lifecycle")
        else:
            self.log("Complete Lifecycle Test", False, 
                    f"Failed at steps: Create={success1}, Summons={success2}, Pay={success3}")
    
    def run_all_tests(self):
        """Run all API tests"""
        print("🧪 GOVERNMENT VEHICLE MANAGEMENT API TEST SUITE")
        print("=" * 60)
        
        print("\n📡 CONNECTIVITY TESTS")
        print("-" * 40)
        self.test_root()
        
        print("\n🚗 VEHICLE LICENSE TESTS")
        print("-" * 40)
        self.test_get_all_licenses()
        self.test_get_license_by_vehicle("W 1234 A")
        self.test_get_license_not_found()
        self.test_get_licenses_by_ic("900101-01-1234")
        self.test_get_expiring_licenses()
        
        # CRUD operations
        self.test_create_license()
        self.test_update_license()
        
        print("\n🚨 VEHICLE SUMMONS TESTS")
        print("-" * 40)
        self.test_get_all_summons()
        self.test_get_summons_by_vehicle("W 1234 A")
        self.test_get_summons_by_status("Unpaid")
        self.test_get_summons_by_status("Paid")
        
        # Summons CRUD
        self.test_create_summons()
        self.test_pay_summons()
        self.test_delete_summons()
        
        # Cleanup test license
        self.test_delete_license()
        
        print("\n📊 UTILITY TESTS")
        print("-" * 40)
        self.test_get_stats()
        
        # Additional tests
        self.test_error_scenarios()
        self.test_performance()
        self.test_lifecycle()
        
        # Final summary
        self.print_summary()
    
    def print_summary(self):
        """Print test results summary"""
        total = self.passed + self.failed
        success_rate = (self.passed / total * 100) if total > 0 else 0
        
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        if self.failed == 0:
            print("🎉 ALL TESTS PASSED!")
        else:
            print("⚠️ SOME TESTS FAILED")
        
        print(f"\nResults:")
        print(f"  ✅ Passed: {self.passed}")
        print(f"  ❌ Failed: {self.failed}")
        print(f"  📊 Success Rate: {success_rate:.1f}%")
        
        print(f"\nEndpoints Tested:")
        print("  • GET / - Root endpoint")
        print("  • GET /licenses/ - All licenses")
        print("  • GET /licenses/{vehicle_id} - License by ID")
        print("  • GET /licenses/ic/{ic} - Licenses by IC")
        print("  • GET /licenses/expiring/{days} - Expiring licenses")
        print("  • POST /licenses/ - Create license")
        print("  • PUT /licenses/{vehicle_id} - Update license")
        print("  • DELETE /licenses/{vehicle_id} - Delete license")
        print("  • GET /summons/ - All summons")
        print("  • GET /summons/{vehicle_id} - Summons by vehicle")
        print("  • GET /summons/status/{status} - Summons by status")
        print("  • POST /summons/ - Create summons")
        print("  • PUT /summons/{id}/pay - Pay summons")
        print("  • DELETE /summons/{id} - Delete summons")
        print("  • GET /stats/summary - System statistics")
        
        print(f"\nTest Categories:")
        print("  • Basic connectivity")
        print("  • CRUD operations")
        print("  • Error handling")
        print("  • Performance testing")
        print("  • Integration testing")
        
        if self.failed == 0:
            print("\n✅ API is working correctly and ready for use!")
        else:
            print("\n⚠️ Please fix failed tests before production use")

def main():
    """Main function to run tests"""
    if len(sys.argv) > 1 and sys.argv[1] == "help":
        print("Government Vehicle Management API Test Script")
        print("=" * 50)
        print("Usage:")
        print("  python test_api.py       - Run all tests")
        print("  python test_api.py help  - Show this help")
        print()
        print("Make sure your API server is running at http://127.0.0.1:8000")
        print("Start server with: uvicorn your_api_file:app --reload")
        return
    
    print("Starting API tests...")
    print(f"Testing API at: {BASE_URL}")
    print(f"Request timeout: {TIMEOUT} seconds")
    print()
    
    tester = APITester()
    try:
        tester.run_all_tests()
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
        tester.print_summary()
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        tester.print_summary()

if __name__ == "__main__":
    main()
