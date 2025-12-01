#!/usr/bin/env python3
"""
Quick test to verify the Course Discovery API endpoints are working.
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint."""
    print("Testing health endpoint...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"✅ Health: {response.json()}\n")

def test_discover_endpoint():
    """Test course discovery endpoint (requires auth)."""
    print("Testing course discovery endpoint...")
    
    # First, try to login
    login_data = {
        "username": "admin@example.com",
        "password": "changeme123"
    }
    
    try:
        # Login
        login_response = requests.post(
            f"{BASE_URL}/api/auth/login",
            data=login_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        if login_response.status_code == 200:
            token = login_response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            
            # Test discover endpoint
            discover_response = requests.get(
                f"{BASE_URL}/api/course-discovery/discover",
                headers=headers
            )
            
            if discover_response.status_code == 200:
                data = discover_response.json()
                print(f"✅ Course Discovery API is working!")
                print(f"   Found {data.get('total_courses', 0)} courses")
                
                if data.get('courses'):
                    print("\n   Courses:")
                    for course in data['courses'][:3]:  # Show first 3
                        print(f"   - {course['display_name']} ({course['pdf_count']} PDFs)")
            else:
                print(f"❌ Discovery endpoint failed: {discover_response.status_code}")
                print(f"   Response: {discover_response.text}")
        else:
            print(f"❌ Login failed: {login_response.status_code}")
            print("   Make sure the admin user exists (run init_db)")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def check_openapi():
    """Check if course-discovery endpoints are in OpenAPI spec."""
    print("\nChecking OpenAPI spec...")
    response = requests.get(f"{BASE_URL}/openapi.json")
    
    if response.status_code == 200:
        spec = response.json()
        paths = spec.get("paths", {})
        
        course_discovery_paths = [
            path for path in paths.keys() 
            if "course-discovery" in path
        ]
        
        if course_discovery_paths:
            print(f"✅ Found {len(course_discovery_paths)} course-discovery endpoints:")
            for path in course_discovery_paths:
                print(f"   - {path}")
        else:
            print("❌ No course-discovery endpoints found in OpenAPI spec")
            print("   The router might not be registered correctly")
    else:
        print(f"❌ Failed to get OpenAPI spec: {response.status_code}")

if __name__ == "__main__":
    print("="*60)
    print("Course Discovery API Test")
    print("="*60 + "\n")
    
    test_health()
    check_openapi()
    test_discover_endpoint()
    
    print("\n" + "="*60)
    print("Test Complete!")
    print("="*60)
