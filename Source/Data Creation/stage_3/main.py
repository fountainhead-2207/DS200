import pandas as pd
import numpy as np
import warnings
import os
# Nhập hàm điều phối chính từ file thư viện
from simulation_library import dispatch_simulation_by_fruit

# --- 1. TÊN FILE ĐẦU VÀO & ĐẦU RA ---
INPUT_FILE = r'Data\Bronze_layer\enriched_weather_data_part1.csv'  
MASTER_IOT_FILE = r'Data\Bronze_layer\Iot_part1.csv'

def main():
    """
    Chương trình chính: Đọc file CSV chứa dữ liệu GPS và fruit_cate,
    sau đó mô phỏng dữ liệu IoT cho từng chuyến đi dựa trên loại trái cây.
    """
    warnings.filterwarnings('ignore')
    np.random.seed(42)
    
    print("="*80)
    print("NHÀ MÁY MÔ PHỎNG DỮ LIỆU IoT - FRUIT STORAGE MONITORING")
    print("="*80)
    print()
    
    # 1. Kiểm tra và đọc file đầu vào
    if not os.path.exists(INPUT_FILE):
        print(f"❌ LỖI: Không tìm thấy file đầu vào: {INPUT_FILE}")
    
    print(f"📂 Đọc file đầu vào: {INPUT_FILE}")
    try:
        df_input = pd.read_csv(INPUT_FILE, parse_dates=['timestamp'])
        print(f"✓ Đọc thành công {len(df_input)} dòng dữ liệu")
    except Exception as e:
        print(f"❌ Lỗi khi đọc file: {e}")
        return
    
    # 2. Kiểm tra các cột bắt buộc
    required_columns = ['trip_id', 'fruit_cate', 'timestamp']
    missing_columns = [col for col in required_columns if col not in df_input.columns]
    
    if missing_columns:
        print(f"❌ LỖI: Thiếu các cột bắt buộc: {missing_columns}")
        print(f"Các cột hiện có: {list(df_input.columns)}")
        return
    
    
    
    # 3. Kiểm tra dữ liệu fruit_cate
    print()
    print("📊 Thống kê dữ liệu đầu vào:")
    print(f"  - Tổng số điểm GPS: {len(df_input)}")
    print(f"  - Số chuyến đi: {df_input['trip_id'].nunique()}")
    print(f"  - Các loại trái cây:")
    
    fruit_counts = df_input['fruit_cate'].value_counts()
    for fruit, count in fruit_counts.items():
        print(f"    • {fruit}: {count} điểm GPS")
    
    # Kiểm tra giá trị null trong fruit_cate
    if df_input['fruit_cate'].isnull().any():
        null_count = df_input['fruit_cate'].isnull().sum()
        print(f"\n⚠️  Cảnh báo: Có {null_count} dòng thiếu thông tin 'fruit_cate'")
        print("   → Sẽ loại bỏ các dòng này")
        df_input = df_input.dropna(subset=['fruit_cate'])
    
    # 4. Phân nhóm theo từng chuyến đi
    print()
    print("─"*80)
    print("BẮT ĐẦU MÔ PHỎNG DỮ LIỆU IoT")
    print("─"*80)
    
    trip_groups = df_input.groupby('trip_id')
    all_trip_ids = list(trip_groups.groups.keys())
    print(f"\n🚢 Tìm thấy {len(all_trip_ids)} chuyến đi hợp lệ")
    print(f"   Danh sách: {', '.join(all_trip_ids)}")
    print()
    
    all_simulated_data = []  # Nơi lưu trữ kết quả
    successful_trips = 0
    failed_trips = 0
    
    # 5. Vòng lặp xử lý từng chuyến đi
    for idx, (trip_id, df_gps_trip) in enumerate(trip_groups, 1):
        
        fruit_category = df_gps_trip['fruit_cate'].iloc[0]
        num_gps_points = len(df_gps_trip)
        
        
        
        try:
            # === GỌI HÀM ĐIỀU PHỐI TỪ THƯ VIỆN ===
            df_simulated_trip = dispatch_simulation_by_fruit(
                fruit_cate=fruit_category,
                df_gps_trip=df_gps_trip,
                trip_id=trip_id
            )
            
            if df_simulated_trip is not None and len(df_simulated_trip) > 0:
                all_simulated_data.append(df_simulated_trip)
                successful_trips += 1
                print(f"      ✓ Mô phỏng thành công: {len(df_simulated_trip)} điểm IoT")
            else:
                failed_trips += 1
                print(f"      ✗ Bỏ qua chuyến {trip_id} (không có dữ liệu)")
                
        except Exception as e:
            failed_trips += 1
            print(f"      ✗ LỖI khi mô phỏng chuyến {trip_id}: {e}")
        
        print()

    # 6. Ghép tất cả kết quả và lưu
    if not all_simulated_data:
        print("="*80)
        print("⚠️  KHÔNG CÓ DỮ LIỆU NÀO ĐƯỢC MÔ PHỎNG")
        print("="*80)
        return
    
    print("─"*80)
    print("TỔNG HỢP KẾT QUẢ")
    print("─"*80)
    print(f"\nĐang ghép dữ liệu từ {successful_trips} chuyến đi thành công")
    
    df_master_simulation = pd.concat(all_simulated_data, ignore_index=True)
    
    # Lưu file output
    df_master_simulation.to_csv(MASTER_IOT_FILE, index=False)
    
    

if __name__ == "__main__":
    main()