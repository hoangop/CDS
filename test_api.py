#!/usr/bin/env python3
"""
Script test nhanh API endpoints
"""
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def test_api():
    print("=" * 60)
    print("🧪 TESTING CDS ANALYTICS API")
    print("=" * 60)
    
    # Test 1: Health check
    print("\n1️⃣ Testing root endpoint...")
    try:
        response = requests.get("http://localhost:8000/")
        print(f"   ✅ Status: {response.status_code}")
        print(f"   📄 Response: {response.json()}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return
    
    # Test 2: Get schools list
    print("\n2️⃣ Testing GET /schools (limit=5)...")
    try:
        response = requests.get(f"{BASE_URL}/schools?limit=5")
        data = response.json()
        print(f"   ✅ Status: {response.status_code}")
        print(f"   📊 Found {len(data)} schools")
        if data:
            print(f"   📝 First school: {data[0]['name']}")
            print(f"      - Total Applicants: {data[0].get('total_applicants', 'N/A')}")
            print(f"      - International Applicants: {data[0].get('applicants_international', 'N/A')}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 3: Search schools
    print("\n3️⃣ Testing search (q=Harvard)...")
    try:
        response = requests.get(f"{BASE_URL}/schools?q=Harvard")
        data = response.json()
        print(f"   ✅ Status: {response.status_code}")
        print(f"   📊 Found {len(data)} schools matching 'Harvard'")
        if data:
            for school in data[:3]:
                print(f"      - {school['name']}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 4: Get school detail
    print("\n4️⃣ Testing GET /schools/{id}...")
    try:
        # Lấy ID của school đầu tiên
        response = requests.get(f"{BASE_URL}/schools?limit=1")
        if response.json():
            school_id = response.json()[0]['institution_id']
            response = requests.get(f"{BASE_URL}/schools/{school_id}")
            data = response.json()
            print(f"   ✅ Status: {response.status_code}")
            print(f"   🏫 School: {data['name']}")
            print(f"   📚 Admission Data: {len(data.get('admission_data', []))} records")
            if data.get('admission_data'):
                adm = data['admission_data'][0]
                print(f"      - Total Applicants: {adm.get('total_applicants', 'N/A')}")
                print(f"      - Total Admitted: {adm.get('total_admitted', 'N/A')}")
                print(f"      - International: {adm.get('applicants_international', 'N/A')} applicants")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 5: Filter by letter
    print("\n5️⃣ Testing filter by letter (A)...")
    try:
        response = requests.get(f"{BASE_URL}/schools?letter=A&limit=3")
        data = response.json()
        print(f"   ✅ Status: {response.status_code}")
        print(f"   📊 Found {len(data)} schools starting with 'A'")
        if data:
            for school in data:
                print(f"      - {school['name']}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n" + "=" * 60)
    print("✅ TEST COMPLETED!")
    print("=" * 60)
    print("\n🌐 Frontend: http://localhost:3000")
    print("📡 API Docs: http://localhost:8000/docs")
    print("=" * 60)

if __name__ == "__main__":
    test_api()

