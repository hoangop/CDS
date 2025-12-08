import requests
import psycopg2
import os
import time

# --- CẤU HÌNH ---
API_KEY = os.getenv("SCORECARD_API_KEY","ZZHbmha80usrekSnZXgJTiphPXZ15WLd1jB9obyN") # Thay bằng key thật của anh nếu DEMO_KEY bị giới hạn
DB_CONFIG = {
    "dbname": "cds_db",
    "user": "postgres",
    "password": "postgres",
    "host": "localhost",
    "port": "5432"
}

# Mapping giữa DB Schema và API Field
# Cấu trúc: Table -> Column -> API Field
FIELD_MAPPING = {
    "Institution_Master": {
        "Institution_ID": "id",
        "Name": "school.name",
        "City_State_Zip": ["school.city", "school.state", "school.zip"], # Sẽ gộp lại
        "Website_URL": "school.school_url",
        "Control": "school.ownership", # 1=Public, 2=Private nonprofit...
    },
    "Enrollment_B": {
        "Total_UG_Students": "latest.student.size",
        "Total_White": "latest.student.demographics.race_ethnicity.white", # Dạng %
        "Total_Black": "latest.student.demographics.race_ethnicity.black",
        "Total_Hispanic_Latino": "latest.student.demographics.race_ethnicity.hispanic",
        "Total_Asian": "latest.student.demographics.race_ethnicity.asian",
    },
    "Admission_C": {
        "Admission_Rate": "latest.admissions.admission_rate.overall",
        "SAT_Avg": "latest.admissions.sat_scores.average.overall",
        "ACT_Midpoint": "latest.admissions.act_scores.midpoint.cumulative",
    },
    "FinancialAid_H": {
        "Tuition_In_State": "latest.cost.tuition.in_state",
        "Tuition_Out_Of_State": "latest.cost.tuition.out_of_state",
        "Cost_Attendance": "latest.cost.attendance.academic_year",
    }
}

def get_scorecard_data(page=0, per_page=100):
    """Lấy dữ liệu từ API."""
    base_url = "https://api.data.gov/ed/collegescorecard/v1/schools.json"
    
    # Các trường cần lấy
    fields = [
        "id", "school.name", "school.city", "school.state", "school.zip", 
        "school.school_url", "school.ownership",
        "latest.student.size", 
        "latest.student.demographics.race_ethnicity.white",
        "latest.student.demographics.race_ethnicity.black",
        "latest.student.demographics.race_ethnicity.hispanic",
        "latest.student.demographics.race_ethnicity.asian",
        "latest.admissions.admission_rate.overall",
        "latest.admissions.sat_scores.average.overall",
        "latest.admissions.act_scores.midpoint.cumulative",
        "latest.cost.tuition.in_state",
        "latest.cost.tuition.out_of_state",
        "latest.cost.attendance.academic_year"
    ]
    
    params = {
        "api_key": API_KEY,
        "fields": ",".join(fields),
        "page": page,
        "per_page": per_page,
        "school.degrees_awarded.predominant": "3", # Chỉ lấy trường cấp bằng cử nhân (Bachelor)
        "latest.student.size__range": "1000..",    # Chỉ lấy trường > 1000 SV
    }
    
    response = requests.get(base_url, params=params)
    if response.status_code != 200:
        print(f"Lỗi API: {response.status_code} - {response.text}")
        return None
    return response.json()

def transform_and_load(data, academic_year="2022-2023"):
    """Chuyển đổi dữ liệu và lưu vào DB."""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    results = data.get('results', [])
    print(f"Đang xử lý {len(results)} trường...")
    
    for school in results:
        try:
            inst_id = str(school['id'])
            name = school['school.name']
            
            # 1. Insert Institution_Master
            city = school.get('school.city', '')
            state = school.get('school.state', '')
            zip_code = school.get('school.zip', '')
            full_address = f"{city}, {state} {zip_code}"
            
            ownership_map = {1: "Public", 2: "Private nonprofit", 3: "Private for-profit"}
            control = ownership_map.get(school.get('school.ownership'), "Unknown")
            
            cur.execute("""
                INSERT INTO Institution_Master (Institution_ID, Name, City_State_Zip, Control, Website_URL)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (Institution_ID) DO UPDATE 
                SET Name = EXCLUDED.Name, Website_URL = EXCLUDED.Website_URL;
            """, (inst_id, name, full_address, control, school.get('school.school_url')))
            
            # 2. Insert Enrollment_B
            ug_size = school.get('latest.student.size')
            
            # API trả về %, cần nhân với tổng số để ra số lượng người (ước lượng)
            def calc_count(percent):
                return int(percent * ug_size) if percent and ug_size else None

            cur.execute("""
                INSERT INTO Enrollment_B (
                    Institution_ID, Academic_Year, Total_UG_Students, 
                    Total_White, Total_Black, Total_Hispanic_Latino, Total_Asian
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (Institution_ID, Academic_Year) DO NOTHING;
            """, (
                inst_id, academic_year, ug_size,
                calc_count(school.get('latest.student.demographics.race_ethnicity.white')),
                calc_count(school.get('latest.student.demographics.race_ethnicity.black')),
                calc_count(school.get('latest.student.demographics.race_ethnicity.hispanic')),
                calc_count(school.get('latest.student.demographics.race_ethnicity.asian'))
            ))
            
            # 3. Insert Admission_C
            cur.execute("""
                INSERT INTO Admission_C (
                    Institution_ID, Academic_Year, Acceptance_Rate, SAT_Comp_25th, ACT_Comp_25th
                )
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (Institution_ID, Academic_Year) DO NOTHING;
            """, (
                inst_id, academic_year, 
                school.get('latest.admissions.admission_rate.overall'),
                # Lưu ý: API Scorecard trả về Avg chứ không phải 25th/75th cho SAT tổng.
                # Tạm dùng cột này để chứa Avg cho demo
                school.get('latest.admissions.sat_scores.average.overall'), 
                school.get('latest.admissions.act_scores.midpoint.cumulative')
            ))

            # 4. Insert FinancialAid_H (Dùng bảng này để lưu học phí)
            cur.execute("""
                INSERT INTO FinancialAid_H (
                    Institution_ID, Academic_Year, Tuition_FullTime_UG, Food_Housing_OnCampus
                )
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (Institution_ID, Academic_Year) DO NOTHING;
            """, (
                inst_id, academic_year,
                school.get('latest.cost.tuition.in_state'), # Lấy In-state làm mặc định
                None # Scorecard API tách riêng cost, cần query thêm field nếu muốn
            ))
            
        except Exception as e:
            print(f"Lỗi khi xử lý trường {name}: {e}")
            conn.rollback()
            continue
            
    conn.commit()
    cur.close()
    conn.close()
    print("Hoàn thành batch.")

def main():
    print("Bắt đầu import dữ liệu từ College Scorecard...")
    
    # Lấy 5 trang đầu (500 trường) để test
    for page in range(5):
        print(f"Đang tải trang {page}...")
        data = get_scorecard_data(page=page)
        if data:
            transform_and_load(data)
        else:
            break
        time.sleep(1) # Rate limit friendly

if __name__ == "__main__":
    main()

