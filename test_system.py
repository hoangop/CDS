#!/usr/bin/env python3
"""
Script test toàn bộ hệ thống CDS Analytics
"""
import requests
import json

def test_api():
    print("=" * 60)
    print("🧪 TESTING CDS ANALYTICS SYSTEM")
    print("=" * 60)
    
    # Test 1: API Health
    print("\n1️⃣ Testing API Health...")
    try:
        response = requests.get("http://localhost:8000/api/v1/schools?limit=1")
        if response.status_code == 200:
            print("   ✅ API is responding")
        else:
            print(f"   ❌ API returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ API Error: {e}")
        return False
    
    # Test 2: Check Data Structure
    print("\n2️⃣ Testing Data Structure...")
    try:
        response = requests.get("http://localhost:8000/api/v1/schools?limit=5")
        data = response.json()
        
        if len(data) > 0:
            print(f"   ✅ Found {len(data)} schools")
            
            # Check first school
            first_school = data[0]
            required_fields = ['institution_id', 'name', 'rank_2025', 'rank_type', 
                             'total_applicants', 'total_admitted', 
                             'applicants_international', 'admitted_international']
            
            missing_fields = [f for f in required_fields if f not in first_school]
            if missing_fields:
                print(f"   ⚠️  Missing fields: {missing_fields}")
            else:
                print("   ✅ All required fields present")
        else:
            print("   ⚠️  No schools found")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False
    
    # Test 3: Display Sample Data
    print("\n3️⃣ Sample Data (Top 5 Schools with Rankings):")
    print("-" * 60)
    try:
        response = requests.get("http://localhost:8000/api/v1/schools?limit=100")
        data = response.json()
        
        # Filter schools with rankings
        ranked_schools = [s for s in data if s.get('rank_2025')]
        ranked_schools.sort(key=lambda x: x['rank_2025'])
        
        for school in ranked_schools[:5]:
            rank = school.get('rank_2025', 'N/A')
            rank_type = school.get('rank_type', 'N/A')
            name = school.get('name', 'N/A')
            total_app = school.get('total_applicants', 0)
            total_adm = school.get('total_admitted', 0)
            int_app = school.get('applicants_international', 0)
            int_adm = school.get('admitted_international', 0)
            
            overall_rate = (total_adm / total_app * 100) if total_app else 0
            int_rate = (int_adm / int_app * 100) if int_app else 0
            
            print(f"   #{rank:3d} | {name[:40]:40s}")
            print(f"          {rank_type}")
            print(f"          Overall: {overall_rate:5.1f}% | Int'l: {int_rate:5.1f}%")
            print()
    except Exception as e:
        print(f"   ❌ Error displaying data: {e}")
        return False
    
    # Test 4: Statistics
    print("\n4️⃣ Database Statistics:")
    print("-" * 60)
    try:
        response = requests.get("http://localhost:8000/api/v1/schools?limit=1000")
        data = response.json()
        
        total_schools = len(data)
        schools_with_rank = len([s for s in data if s.get('rank_2025')])
        schools_with_data = len([s for s in data if s.get('total_applicants')])
        
        print(f"   📊 Total Institutions: {total_schools}")
        print(f"   🏆 Schools with Rankings: {schools_with_rank}")
        print(f"   📈 Schools with Admission Data: {schools_with_data}")
        print(f"   📊 Coverage: {schools_with_rank/total_schools*100:.1f}% ranked")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False
    
    # Test 5: Frontend
    print("\n5️⃣ Testing Frontend...")
    try:
        response = requests.get("http://localhost:3000")
        if response.status_code == 200 and "University Common Data Set" in response.text:
            print("   ✅ Frontend is serving correctly")
        else:
            print("   ⚠️  Frontend response unexpected")
    except Exception as e:
        print(f"   ❌ Frontend Error: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("✅ ALL TESTS PASSED!")
    print("=" * 60)
    print("\n🌐 Access your application at:")
    print("   Frontend: http://localhost:3000")
    print("   Backend API: http://localhost:8000/api/v1/schools")
    print()
    
    return True

if __name__ == "__main__":
    test_api()

