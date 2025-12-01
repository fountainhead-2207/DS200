import pandas as pd
import numpy as np
import warnings

# --- 1. TÊN FILE ĐẦU VÀO & ĐẦU RA ---
# FILE NÀY PHẢI CHỨA DỮ LIỆU CỦA NHIỀU CHUYẾN ĐI,
# VỚI MỘT CỘT ID (ví dụ: 'ship_id') ĐỂ PHÂN BIỆT
GPS_MULTI_TRIP_FILE = 'all_voyages_gps.csv'
MASTER_OUTPUT_FILE = 'master_iot_simulation.csv'

# --- 2. CÁC THAM SỐ CỐ ĐỊNH ---
TIMESTEP_MINUTES = 10
STEPS_PER_HOUR = 60 / TIMESTEP_MINUTES

# --- 3. HỒ SƠ "CAM" (ORANGE) & QUY TẮC CHUYÊN GIA ---
# (Lấy từ lần trước, không đổi)
SETPOINT_TEMP = 22.5
AMP_TEMP = 0.5
SETPOINT_HUMID = 92.0
CO2_BASE = 280.0
CO2_RATE_PER_HOUR = 2.5
CO2_VENT_THRESHOLD = 350.0
CO2_VENT_FREQ_STEPS = int(12 * STEPS_PER_HOUR)
LIGHT_BASE_MEAN = 7.0
LIGHT_BASE_STD = 2.0
RULE_TEMP_TRIGGER = 23.0
RULE_LIGHT_TRIGGER = 13.5
RULE_CO2_ACCEL_TRIGGER = 300.0
RULE_DURATION_STEPS_NORMAL = int(2 * STEPS_PER_HOUR) # 2 giờ
RULE_DURATION_STEPS_FAST = int(1 * STEPS_PER_HOUR)   # 1 giờ

# ======================================================================
# GIAI ĐOẠN 1: "NHÀ MÁY" - CÁC HÀM MÔ PHỎNG (TÁI SỬ DỤNG)
# ======================================================================

def simulate_baseline_scenario(num_steps):
    """Mô phỏng kịch bản 'Good' lý tưởng."""
    temp_list = np.zeros(num_steps)
    humid_list = np.zeros(num_steps)
    co2_list = np.zeros(num_steps)
    light_list = np.zeros(num_steps)

    current_co2 = CO2_BASE

    for i in range(num_steps):
        sin_temp = np.sin(i * (np.pi * 2 / (24 * STEPS_PER_HOUR))) * AMP_TEMP
        temp_list[i] = SETPOINT_TEMP + sin_temp + np.random.normal(0, 0.1)

        humid_list[i] = np.clip(SETPOINT_HUMID + np.random.normal(0, 0.5), 0, 100)

        light_list[i] = np.clip(np.random.normal(LIGHT_BASE_MEAN, LIGHT_BASE_STD), 0, None)

        current_co2 += (CO2_RATE_PER_HOUR / STEPS_PER_HOUR) + np.random.normal(0, 0.1)
        if (i > 0 and i % CO2_VENT_FREQ_STEPS == 0) or current_co2 > CO2_VENT_THRESHOLD:
            current_co2 = CO2_BASE + np.random.normal(0, 5)
        co2_list[i] = current_co2

    df_baseline = pd.DataFrame({
        'temp': temp_list, 'humid': humid_list, 'co2': co2_list, 'light': light_list
    })
    return df_baseline

def apply_expert_labeling(df, num_steps):
    """Áp dụng quy tắc gán nhãn của chuyên gia."""
    df['class'] = 'Good'
    is_temp_fail = df['temp'] > RULE_TEMP_TRIGGER
    is_light_fail = df['light'] > RULE_LIGHT_TRIGGER
    is_co2_accel = df['co2'] > RULE_CO2_ACCEL_TRIGGER
    is_fail_condition = is_temp_fail & is_light_fail

    consecutive_fail_steps = 0
    failure_triggered = False
    fail_start_index = -1

    for i in range(1, num_steps):
        if failure_triggered:
            df.loc[i, 'class'] = 'Bad'
            continue

        if is_fail_condition[i]:
            if consecutive_fail_steps == 0:
                fail_start_index = i # Ghi lại thời điểm bắt đầu vi phạm
            consecutive_fail_steps += 1
            is_accelerated = is_co2_accel[i]

            required_steps = RULE_DURATION_STEPS_FAST if is_accelerated else RULE_DURATION_STEPS_NORMAL

            if consecutive_fail_steps >= required_steps:
                failure_triggered = True
                df.loc[fail_start_index:, 'class'] = 'Bad' # Gán nhãn 'Bad' từ lúc bắt đầu
        else:
            consecutive_fail_steps = 0 # Reset bộ đếm

    return df, failure_triggered

def inject_failure(df_baseline, scenario, num_steps):
    """
    Tiêm kịch bản hỏng hóc với các thông số NGẪU NHIÊN.
    """
    df_fail = df_baseline.copy()

    # 1. Chọn thời điểm & thời gian hỏng hóc ngẫu nhiên
    # Bắt đầu hỏng: trong khoảng 20% - 50% chuyến đi
    fail_start_step = np.random.randint(int(num_steps * 0.2), int(num_steps * 0.5))
    # Thời gian hỏng: từ 4 đến 12 giờ
    fail_duration_hours = np.random.uniform(4.0, 12.0)
    fail_duration_steps = int(fail_duration_hours * STEPS_PER_HOUR)
    fail_end_step = min(fail_start_step + fail_duration_steps, num_steps)

    if scenario == 'DOOR_AJAR':
        # 2a. Mức độ hỏng (Ánh sáng)
        fail_light_level = np.random.uniform(100.0, 200.0) # Sáng
        df_fail.loc[fail_start_step : fail_end_step, 'light'] = fail_light_level + np.random.normal(0, 10, (fail_end_step-fail_start_step)+1)

        # 2b. Mức độ hỏng (Nhiệt độ)
        temp_drift_total = np.random.uniform(2.0, 5.0) # Tăng 2-5 độ
        temp_drift = np.linspace(0, temp_drift_total, (fail_end_step-fail_start_step)+1)
        df_fail.loc[fail_start_step : fail_end_step, 'temp'] += temp_drift

    elif scenario == 'TEMP_FAIL':
        # Máy lạnh hỏng, nhiệt độ trôi dần
        temp_drift_total = np.random.uniform(4.0, 8.0) # Tăng 4-8 độ
        temp_drift = np.linspace(0, temp_drift_total, (fail_end_step-fail_start_step)+1)
        df_fail.loc[fail_start_step : fail_end_step, 'temp'] += temp_drift

    elif scenario == 'CO2_FAIL':
        # Máy lọc hỏng, CO2 không reset
        co2_at_fail = df_fail.loc[fail_start_step, 'co2']
        co2_rate_step = (CO2_RATE_PER_HOUR / STEPS_PER_HOUR)
        # Mô phỏng CO2 tăng tuyến tính từ điểm hỏng
        for i in range(fail_start_step + 1, num_steps):
             df_fail.loc[i, 'co2'] = df_fail.loc[i-1, 'co2'] + co2_rate_step + np.random.normal(0, 0.1)

    # Các kịch bản khác (ví dụ: 'GOOD') sẽ không làm gì

    return df_fail

def simulate_single_trip(df_gps_trip, trip_id, scenario):
    """
    HÀM "NHÀ MÁY" CHÍNH.
    Mô phỏng một chuyến đi duy nhất dựa trên kịch bản đã chọn.
    """
    # 1. Tạo khung thời gian 10 phút/lần (dựa trên thời gian của chuyến GPS này)
    start_time = df_gps_trip['timestamp'].min()
    end_time = df_gps_trip['timestamp'].max()

    iot_timestamps = pd.date_range(start=start_time, end=end_time, freq='10T')
    df_sim = pd.DataFrame({'timestamp': iot_timestamps})
    num_steps = len(df_sim)

    # 2. Mô phỏng kịch bản 'Good'
    df_baseline = simulate_baseline_scenario(num_steps)

    # 3. Tiêm kịch bản hỏng hóc (với tính ngẫu nhiên)
    df_with_failure = inject_failure(df_baseline, scenario, num_steps)

    df_sim = pd.concat([df_sim, df_with_failure], axis=1)

    # 4. Áp dụng quy tắc gán nhãn
    df_sim, failure_triggered = apply_expert_labeling(df_sim, num_steps)

    # Nếu kịch bản là 'GOOD' nhưng lại bị gán nhãn 'Bad' (do ngẫu nhiên),
    # chúng ta có thể sửa lại nhãn hoặc chấp nhận là "ngẫu nhiên"
    if scenario == 'GOOD' and failure_triggered:
        df_sim['class'] = 'Good' # Ép về 'Good' nếu kịch bản là 'Good'

    # 5. Ghép (Mapping) dữ liệu GPS vào
    df_final_trip = pd.merge_asof(
        df_sim.sort_values(by='timestamp'),
        df_gps_trip.sort_values(by='timestamp'),
        on='timestamp',
        suffixes=('_iot', '_gps')
    )

    # 6. Thêm các ID
    df_final_trip['trip_id'] = trip_id # ID của chuyến
    df_final_trip['failure_scenario'] = scenario # Kịch bản đã dùng

    return df_final_trip

# ======================================================================
# GIAI ĐOẠN 2 & 3: "NGƯỜI QUẢN LÝ" - VÒNG LẶP SCALE-UP
# ======================================================================

def main():
    warnings.filterwarnings('ignore')
    np.random.seed(42) # Đảm bảo tính lặp lại

    print(f"Đang đọc file GPS tổng: {GPS_MULTI_TRIP_FILE}")
    try:
        df_all_gps = pd.read_csv(GPS_MULTI_TRIP_FILE, parse_dates=['timestamp'])
    except FileNotFoundError:
        print(f"Lỗi: Không tìm thấy file '{GPS_MULTI_TRIP_FILE}'.")
        print("Vui lòng tạo file này với cấu trúc: 'ship_id', 'timestamp', 'latitude', 'longitude', 'speed_knots'")
        print("Đoạn mã này sẽ tạo một file giả lập 'all_voyages_gps.csv' để bạn chạy thử.")

        # TẠO FILE GIẢ LẬP (NẾU KHÔNG TÌM THẤY)
        df_hcm_sh = pd.read_csv('gps_simulation_hcm_to_shanghai.csv', parse_dates=['timestamp'])
        df_trip_2 = df_hcm_sh.copy()
        df_trip_2['ship_id'] = 'VIET_SHIP_002'
        df_trip_2['timestamp'] = df_trip_2['timestamp'] + pd.Timedelta(days=5)
        # Chuyến đi ngắn hơn
        df_trip_3 = df_hcm_sh.copy().iloc[:40] # Chỉ 40 giờ
        df_trip_3['ship_id'] = 'SHORT_TRIP_003'
        df_trip_3['timestamp'] = df_trip_3['timestamp'] + pd.Timedelta(days=10)

        df_all_gps = pd.concat([df_hcm_sh, df_trip_2, df_trip_3])
        df_all_gps.to_csv(GPS_MULTI_TRIP_FILE, index=False)
        print(f"Đã tạo file giả lập: {GPS_MULTI_TRIP_FILE}")

    except Exception as e:
        print(f"Lỗi khi đọc file GPS: {e}")
        return

    # Định nghĩa cột ID. Thay 'ship_id' bằng 'trip_id' nếu file của bạn dùng 'trip_id'
    TRIP_ID_COLUMN = 'ship_id'

    # Lấy danh sách các chuyến đi
    trip_groups = df_all_gps.groupby(TRIP_ID_COLUMN)
    all_trip_ids = list(trip_groups.groups.keys())
    print(f"Tìm thấy {len(all_trip_ids)} chuyến đi: {all_trip_ids}")

    # Định nghĩa các kịch bản (Tỷ lệ 50% 'GOOD')
    scenarios = ['GOOD', 'GOOD', 'GOOD', 'GOOD',
                 'DOOR_AJAR', 'TEMP_FAIL', 'CO2_FAIL']

    all_simulated_data = [] # Nơi lưu trữ kết quả

    # Chạy vòng lặp "SCALE UP"
    for trip_id, df_gps_trip in trip_groups:

        # 1. Chọn kịch bản ngẫu nhiên
        chosen_scenario = np.random.choice(scenarios)

        print(f"\n--- Đang xử lý Chuyến: {trip_id} ---")
        print(f"    Thời lượng: {df_gps_trip['timestamp'].max() - df_gps_trip['timestamp'].min()}")
        print(f"    Kịch bản: {chosen_scenario}")

        # 2. Gọi "Nhà máy"
        try:
            df_simulated_trip = simulate_single_trip(df_gps_trip, trip_id, chosen_scenario)

            # 3. Thu thập kết quả
            all_simulated_data.append(df_simulated_trip)
            print(f"    Hoàn tất: {trip_id}. Đã tạo {len(df_simulated_trip)} điểm dữ liệu.")

        except Exception as e:
            print(f"    Lỗi khi mô phỏng chuyến {trip_id}: {e}")

    # 4. Ghép tất cả kết quả
    if not all_simulated_data:
        print("Không có dữ liệu nào được mô phỏng.")
        return

    print("\nĐang ghép tất cả các chuyến đi thành file master...")
    df_master_simulation = pd.concat(all_simulated_data, ignore_index=True)

    # 5. Lưu file tổng
    df_master_simulation.to_csv(MASTER_OUTPUT_FILE, index=False)

    print(f"\n--- TOÀN BỘ MÔ PHỎNG HOÀN TẤT ---")
    print(f"File tổng đã được lưu tại: {MASTER_OUTPUT_FILE}")
    print(f"Tổng số điểm dữ liệu IoT đã tạo: {len(df_master_simulation)}")
    print("\nKiểm tra 5 dòng đầu:")
    print(df_master_simulation.head())
    print("\nKiểm tra 5 dòng cuối:")
    print(df_master_simulation.tail())

if __name__ == "__main__":
    main()