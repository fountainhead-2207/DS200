import pandas as pd
import numpy as np

# ======================================================================
# PHẦN 1: CÁC "HỒ SƠ" (PROFILES) CHO TỪNG LOẠI TRÁI CÂY
# =Ghi chú: Các hồ sơ 'Banana', 'Tomato', 'Pineapple' đã được
# cập nhật dựa trên ghi chú của chuyên gia.
# ======================================================================

def _get_orange_profile():
    profile = {
        'fruit_name': 'Orange',
        'setpoints': {
            'temp': 22.5, 'amp_temp': 0.5,
            'humid': 92.0, 'amp_humid': 2.0,
            'co2_base': 280.0, 'co2_rate_phour': 2.5,
            'co2_vent_thresh': 350.0, 'co2_vent_freq_steps': int(12 * 6),
            'light_mean': 7.0, 'light_std': 2.0
        },
        'failure_scenarios': [
            'GOOD', 'GOOD', 'GOOD', 'GOOD', 'DOOR_AJAR', 'TEMP_FAIL'
        ],
        'failure_rules': {
            'rule_1': {
                'conditions': ['TEMP_FAIL', 'LIGHT_FAIL'],
                'temp_trigger': 23.0,
                'light_trigger': 13.5,
                'co2_accel_trigger': 300.0,
                'duration_steps_fast': int(1 * 6), 'duration_steps_normal': int(2 * 6)
            }
        },
        'failure_injection': {
            'DOOR_AJAR': { 'light_level': (100.0, 200.0), 'temp_drift': (2.0, 5.0) },
            'TEMP_FAIL': { 'temp_drift': (4.0, 8.0) }
        }
    }
    return profile

def _get_banana_profile():
    """CẬP NHẬT: Định nghĩa logic, quy tắc, kịch bản cho 'Banana'."""
    # Quy tắc: (Humid > 94%) AND (CO2 < 270)
    # Tăng tốc: Temp <= 24°C
    # Setpoint 'Good': Humid=89 (<94), CO2=388 (>270), Temp=25 (>24)
    # (Dựa trên dữ liệu 'Good' từ Dataset.csv)
    profile = {
        'fruit_name': 'Banana',
        'setpoints': {
            'temp': 25.0, 'amp_temp': 0.5,
            'humid': 89.0, 'amp_humid': 3.0,
            'co2_base': 350.0, 'co2_rate_phour': 5.0, # Chuối hô hấp mạnh
            'co2_vent_thresh': 400.0, 'co2_vent_freq_steps': int(8 * 6),
            'light_mean': 20.0, 'light_std': 1.0 # Ánh sáng 'Good' của chuối khá cao
        },
        'failure_scenarios': [
            'GOOD', 'GOOD', 'GOOD',
            'OVER_VENTILATION' # Kịch bản gây ra Humid cao VÀ CO2 thấp
        ],
        'failure_rules': {
            'rule_1': {
                'conditions': ['HUMID_FAIL', 'CO2_LOW_FAIL'],
                'humid_trigger': 94.0,
                'co2_trigger_low': 270.0,
                'temp_accel_trigger_low': 24.0, # Yếu tố tăng tốc
                'duration_steps_fast': int(3 * 6), # 3 giờ (nếu lạnh)
                'duration_steps_normal': int(6 * 6) # 6 giờ
            }
        },
        'failure_injection': {
            # Kịch bản này mô phỏng lỗi hệ thống thông gió (luôn mở)
            # kéo không khí ẩm trên biển vào và xả hết CO2.
            'OVER_VENTILATION': {
                'humid_level': (95.0, 98.0), # Gây ra Humid > 94
                'co2_level': (250.0, 269.0), # Gây ra CO2 < 270
                'temp_drift': (-1.0, -3.0) # Gây ra Temp <= 24 (tăng tốc)
            }
        }
    }
    return profile

def _get_tomato_profile():
    """CẬP NHẬT: Định nghĩa logic, quy tắc, kịch bản cho 'Tomato'."""
    # Quy tắc 1: (Temp > 24) AND (Humid > 94)
    # Quy tắc 2: (Light > 20)
    # Setpoint 'Good': Temp=23 (<24), Humid=90 (<94), Light=12 (<20)
    # (Dựa trên dữ liệu 'Good' từ Dataset.csv)
    profile = {
        'fruit_name': 'Tomato',
        'setpoints': {
            'temp': 23.0, 'amp_temp': 1.0, # Biên độ cà chua rộng
            'humid': 90.0, 'amp_humid': 2.0,
            'co2_base': 320.0, 'co2_rate_phour': 3.0,
            'co2_vent_thresh': 400.0, 'co2_vent_freq_steps': int(10 * 6),
            'light_mean': 12.0, 'light_std': 3.0
        },
        'failure_scenarios': [
            'GOOD', 'GOOD', 'GOOD', 'GOOD',
            'HOT_HUMID_FAIL',  # Kịch bản cho Quy tắc 1 (Tắc thông gió)
            'LIGHT_EXPOSURE'   # Kịch bản cho Quy tắc 2 (Hở cửa)
        ],
        'failure_rules': {
            'rule_1_hot_humid': { # Quy tắc 1
                'conditions': ['TEMP_FAIL', 'HUMID_FAIL'],
                'temp_trigger': 24.0,
                'humid_trigger': 94.0,
                'duration_steps_normal': int(5 * 6) # 5 giờ
            },
            'rule_2_light': { # Quy tắc 2
                'conditions': ['LIGHT_FAIL'],
                'light_trigger': 20.0, # Hỏng nếu > 20
                'duration_steps_normal': int(3 * 6) # 3 giờ
            }
        },
        'failure_injection': {
            'HOT_HUMID_FAIL': { # Tắc thông gió -> Nóng và Ẩm
                'temp_drift': (2.0, 4.0), # Gây ra Temp > 24
                'humid_level': (95.0, 95.1) # Gây ra Humid > 94 (std=0.0)
            },
            'LIGHT_EXPOSURE': { # Hở cửa (gây ra Ánh sáng và Nóng+Ẩm)
                'light_level': (170.0, 200.0), # Gây ra Light > 20 (spike)
                'temp_drift': (2.0, 4.0),
                'humid_level': (95.0, 95.1)
            }
        }
    }
    return profile

def _get_pineapple_profile():
    """MỚI: Định nghĩa logic, quy tắc, kịch bản cho 'Pineapple'."""
    # Quy tắc: (Temp > 24) AND (Light < 12) AND (Humid = 95%)
    # Tăng tốc: CO2 > 340
    # Setpoint 'Good': Temp=22 (<24), Light=14 (>12), Humid=85 (<95)
    # (Dựa trên dữ liệu 'Good' từ Dataset.csv)
    profile = {
        'fruit_name': 'Pineapple',
        'setpoints': {
            'temp': 22.0, 'amp_temp': 0.5,
            'humid': 85.0, 'amp_humid': 2.0,
            'co2_base': 310.0, 'co2_rate_phour': 2.0,
            'co2_vent_thresh': 350.0, 'co2_vent_freq_steps': int(12 * 6),
            'light_mean': 14.0, 'light_std': 1.0 # Ánh sáng 'Good' > 12
        },
        'failure_scenarios': [
            'GOOD', 'GOOD', 'GOOD',
            'SATURATED_HEAT_FAIL' # Kịch bản gây ra hỏng hóc phức hợp này
        ],
        'failure_rules': {
            'rule_1': {
                'conditions': ['TEMP_FAIL', 'LIGHT_LOW_FAIL', 'HUMID_FAIL'],
                'temp_trigger': 24.0,
                'light_trigger_low': 12.0, # Quy tắc MỚI (Trigger nếu < 12)
                'humid_trigger': 94.9, # Quy tắc MỚI (Trigger nếu > 94.9, để bắt 95%)
                'co2_accel_trigger': 340.0, # Yếu tố tăng tốc
                'duration_steps_fast': int(3 * 6), # 3 giờ
                'duration_steps_normal': int(6 * 6) # 6 giờ
            }
        },
        'failure_injection': {
            # Kịch bản này mô phỏng (Tắc thông gió + Hỏng cảm biến ánh sáng)
            'SATURATED_HEAT_FAIL': {
                'temp_drift': (3.0, 5.0), # Gây Temp > 24 (ví dụ 22 -> 26)
                'humid_level': (95.0, 95.1), # Gây Humid = 95% (std=0.0)
                'light_level': (8.0, 11.0) # Gây Light < 12
            }
        }
    }
    return profile

# ======================================================================
# PHẦN 2: "CỖ MÁY" MÔ PHỎNG CHUNG (ĐÃ NÂNG CẤP)
# ======================================================================

def _create_time_backbone(start_time, end_time, freq_min=10):
    """Tạo khung thời gian 10 phút/lần."""
    iot_timestamps = pd.date_range(start=start_time, end=end_time, freq=f'{freq_min}T')
    df_sim = pd.DataFrame({'timestamp': iot_timestamps})
    return df_sim

def _simulate_baseline(num_steps, p):
    """Mô phỏng kịch bản 'Good' dựa trên HỒ SƠ (p) đã cho."""
    s = p['setpoints']
    temp_list = np.zeros(num_steps)
    humid_list = np.zeros(num_steps)
    co2_list = np.zeros(num_steps)
    light_list = np.zeros(num_steps)

    current_co2 = s['co2_base']
    steps_per_hour = 6 # 60 / 10

    for i in range(num_steps):
        sin_temp = np.sin(i * (np.pi * 2 / (24 * steps_per_hour))) * s['amp_temp']
        temp_list[i] = s['temp'] + sin_temp + np.random.normal(0, 0.1)

        humid_list[i] = np.clip(s['humid'] + np.random.normal(0, 0.5), 0, 100)

        light_list[i] = np.clip(np.random.normal(s['light_mean'], s['light_std']), 0, None)

        current_co2 += (s['co2_rate_phour'] / steps_per_hour) + np.random.normal(0, 0.1)
        if (i > 0 and i % s['co2_vent_freq_steps'] == 0) or current_co2 > s['co2_vent_thresh']:
            current_co2 = s['co2_base'] + np.random.normal(0, 5)
        co2_list[i] = current_co2

    return pd.DataFrame({
        'temp': temp_list, 'humid': humid_list, 'co2': co2_list, 'light': light_list
    })

def _inject_failure(df_baseline, scenario, p, num_steps, df_env = None):
    """Tiêm kịch bản hỏng hóc (scenario) dựa trên HỒ SƠ (p)."""
    df_fail = df_baseline.copy()
    if scenario == 'GOOD' or scenario not in p['failure_injection']:
        return df_fail

    fail_start_step = np.random.randint(int(num_steps * 0.2), int(num_steps * 0.5))
    fail_duration_hours = np.random.uniform(4.0, 12.0)
    fail_duration_steps = int(fail_duration_hours * 6)
    fail_end_step = min(fail_start_step + fail_duration_steps, num_steps - 1)

    params = p['failure_injection'][scenario]

    dt_hours = 10.0 / 60.0

     # =========================
    # 1) TEMP_FAIL / DOOR_AJAR / LIGHT_EXPOSURE
    #    -> truyền nhiệt mạnh với môi trường + (với DOOR_AJAR/LIGHT_EXPOSURE) trao đổi ẩm
    # =========================
    if scenario in ['TEMP_FAIL', 'DOOR_AJAR', 'LIGHT_EXPOSURE'] and df_env is not None:
        # base k theo mức độ "mở" với môi trường
        if scenario == 'TEMP_FAIL':
            k_base = 0.5      # hỏng máy lạnh, truyền nhiệt qua vách + không làm lạnh
        elif scenario == 'DOOR_AJAR':
            k_base = 0.18     # hé cửa, trao đổi chậm hơn mở to
        else:  # 'LIGHT_EXPOSURE' ~ cửa/mái mở rộng, nắng chiếu
            k_base = 0.25

        # T_in / H_in ban đầu tại thời điểm bắt đầu sự cố
        if fail_start_step > 0:
            T_in = df_fail.loc[fail_start_step - 1, 'temp']
            H_in = df_fail.loc[fail_start_step - 1, 'humid']
        else:
            T_in = df_fail.loc[fail_start_step, 'temp']
            H_in = df_fail.loc[fail_start_step, 'humid']

        for i in range(fail_start_step, fail_end_step + 1):
            row_env = df_env.loc[i]
            T_out = row_env.get('temp_out', T_in)
            wind = max(row_env.get('wind_kmh', 0.0), 0.0)
            H_out = row_env.get('humid_out', H_in)
            dew_out = row_env.get('dew_point_out', np.nan)
            precip = max(row_env.get('precip_mm', 0.0), 0.0)

            # Gió tăng tốc truyền nhiệt: 50 km/h -> +50% tốc độ
            wind_factor = 1.0 + wind / 100.0
            k_eff = k_base * wind_factor

            # Newton cho nhiệt độ
            T_in = T_out + (T_in - T_out) * np.exp(-k_eff * dt_hours)
            df_fail.loc[i, 'temp'] = T_in + np.random.normal(0, 0.1)

            # Với DOOR_AJAR & LIGHT_EXPOSURE: không khí ngoài tràn vào -> ẩm bị kéo theo
            if scenario in ['DOOR_AJAR', 'LIGHT_EXPOSURE']:
                # mưa -> không khí ngoài ẩm hơn
                H_out_eff = min(100.0, H_out + precip * 0.5)

                # độ ẩm tiến dần về H_out_eff
                k_humid = 0.35 * wind_factor
                H_in = H_out_eff + (H_in - H_out_eff) * np.exp(-k_humid * dt_hours)

                # nếu điểm sương ngoài > T_in -> dễ ngưng tụ -> spike ẩm
                if not np.isnan(dew_out) and dew_out > T_in:
                    H_in = min(100.0, H_in + np.random.uniform(2.0, 5.0))

                df_fail.loc[i, 'humid'] = H_in + np.random.normal(0, 0.2)

        # Sau khi kết thúc phase failure, giữ ổn định quanh giá trị cuối (có nhiễu nhẹ)
        final_fail_temp = df_fail.loc[fail_end_step, 'temp']
        df_fail.loc[fail_end_step:, 'temp'] = final_fail_temp + np.random.normal(
            0, 0.2, num_steps - fail_end_step
        )
        if scenario in ['DOOR_AJAR', 'LIGHT_EXPOSURE']:
            final_fail_humid = df_fail.loc[fail_end_step, 'humid']
            df_fail.loc[fail_end_step:, 'humid'] = final_fail_humid + np.random.normal(
                0, 0.2, num_steps - fail_end_step
            )

    # =========================
    # 2) OVER_VENTILATION (Banana)
    #    -> thông gió quá mạnh, hút khí ngoài biển: nhiệt + ẩm bị kéo về môi trường,
    #       CO2 bị kéo về mức thấp cấu hình trong params.
    # =========================
    elif scenario == 'OVER_VENTILATION' and df_env is not None:
        if fail_start_step > 0:
            T_in = df_fail.loc[fail_start_step - 1, 'temp']
            H_in = df_fail.loc[fail_start_step - 1, 'humid']
            C_in = df_fail.loc[fail_start_step - 1, 'co2']
        else:
            T_in = df_fail.loc[fail_start_step, 'temp']
            H_in = df_fail.loc[fail_start_step, 'humid']
            C_in = df_fail.loc[fail_start_step, 'co2']

        # target CO2 thấp theo profile (không lấy từ ngoài, vì khí biển ~ 400ppm)
        co2_low_min, co2_low_max = params['co2_level']
        co2_target = np.random.uniform(co2_low_min, co2_low_max)

        for i in range(fail_start_step, fail_end_step + 1):
            row_env = df_env.loc[i]
            T_out = row_env.get('temp_out', T_in)
            H_out = row_env.get('humid_out', H_in)
            dew_out = row_env.get('dew_point_out', np.nan)
            wind = max(row_env.get('wind_kmh', 0.0), 0.0)
            precip = max(row_env.get('precip_mm', 0.0), 0.0)

            # gió lớn + vent mở -> trao đổi mạnh
            wind_factor = 1.0 + wind / 80.0

            # Nhiệt độ: tiến dần về T_out nhưng hệ số nhỏ hơn TEMP_FAIL
            k_temp = 0.25 * wind_factor
            T_in = T_out + (T_in - T_out) * np.exp(-k_temp * dt_hours)
            df_fail.loc[i, 'temp'] = T_in + np.random.normal(0, 0.1)

            # Độ ẩm: tiến dần về humid_out (có tăng thêm do mưa)
            H_out_eff = min(100.0, H_out + precip * 0.3)
            k_humid = 0.5 * wind_factor
            H_in = H_out_eff + (H_in - H_out_eff) * np.exp(-k_humid * dt_hours)

            # dew point cao hơn T_in -> dễ saturate
            if not np.isnan(dew_out) and dew_out > T_in:
                H_in = min(100.0, H_in + np.random.uniform(1.0, 3.0))

            df_fail.loc[i, 'humid'] = H_in + np.random.normal(0, 0.2)

            # CO2: bị hút về co2_target (thấp) với tốc độ phụ thuộc gió
            k_co2 = 0.6 * wind_factor
            C_in = co2_target + (C_in - co2_target) * np.exp(-k_co2 * dt_hours)
            df_fail.loc[i, 'co2'] = C_in + np.random.normal(0, 1.0)

        # sau failure: giữ gần mức cuối
        for col, noise_std in [('temp', 0.2), ('humid', 0.3), ('co2', 2.0)]:
            last_val = df_fail.loc[fail_end_step, col]
            df_fail.loc[fail_end_step:, col] = last_val + np.random.normal(
                0, noise_std, num_steps - fail_end_step
            )

    # =========================
    # 3) HOT_HUMID_FAIL (Tomato) & SATURATED_HEAT_FAIL (Pineapple)
    #    -> tắc thông gió / bão hoà ẩm bên trong. Môi trường ngoài ảnh hưởng
    #       chậm hơn (chủ yếu qua truyền nhiệt), nên ta dùng env để scale drift.
    # =========================
    elif scenario in ['HOT_HUMID_FAIL', 'SATURATED_HEAT_FAIL'] and df_env is not None and 'temp_drift' in params:
        drift_min, drift_max = params['temp_drift']

        # Nhiệt độ ngoài trung bình trong giai đoạn failure
        temp_out_mean = df_env.loc[fail_start_step:fail_end_step, 'temp_out'].mean()
        wind_mean = df_env.loc[fail_start_step:fail_end_step, 'wind_kmh'].mean() if 'wind_kmh' in df_env.columns else 0.0

        # setpoint bên trong (nhiệt độ "Good")
        set_temp = p['setpoints']['temp']

        # scale: nóng + gió mạnh -> drift lớn hơn
        temp_excess = max(temp_out_mean - set_temp, 0.0)
        scale = 1.0 + temp_excess / 15.0 + wind_mean / 200.0
        scale = max(0.5, min(scale, 2.5))

        temp_drift_total = np.random.uniform(drift_min, drift_max) * scale
        temp_drift = np.linspace(0, temp_drift_total, (fail_end_step - fail_start_step) + 1)

        df_fail.loc[fail_start_step:fail_end_step, 'temp'] += temp_drift

        final_fail_temp = df_fail.loc[fail_end_step, 'temp']
        df_fail.loc[fail_end_step:, 'temp'] = final_fail_temp + np.random.normal(
            0, 0.2, num_steps - fail_end_step
        )

        # humid_level của 2 kịch bản này vốn đã ~95%, có thể nhẹ nhàng
        # nâng lên nếu humid_out bên ngoài cũng rất cao:
        if 'humid_level' in params:
            base_min, base_max = params['humid_level']
            base_humid = np.random.uniform(base_min, base_max)
            humid_out_mean = df_env.loc[fail_start_step:fail_end_step, 'humid_out'].mean()
            dew_out_mean = df_env.loc[fail_start_step:fail_end_step, 'dew_point_out'].mean()

            extra = 0.0
            if humid_out_mean > 90:
                extra += 1.0
            if dew_out_mean > set_temp:
                extra += 1.5

            target_humid = min(100.0, base_humid + extra)
            df_fail.loc[fail_start_step:, 'humid'] = target_humid + np.random.normal(
                0, 0.2, num_steps - fail_start_step
            )

    # =========================
    # 4) CÁC SCENARIO KHÁC GIỮ LOGIC CŨ (temp_drift tuyến tính)
    # =========================
    elif 'temp_drift' in params:
        drift_min, drift_max = params['temp_drift']
        temp_drift_total = np.random.uniform(drift_min, drift_max)
        temp_drift = np.linspace(0, temp_drift_total, (fail_end_step - fail_start_step) + 1)
        df_fail.loc[fail_start_step:fail_end_step, 'temp'] += temp_drift
        final_fail_temp = df_fail.loc[fail_end_step, 'temp']
        df_fail.loc[fail_end_step:, 'temp'] = final_fail_temp + np.random.normal(
            0, 0.2, num_steps - fail_end_step
        )

    # =========================
    # 5) ÁNH SÁNG / CO2 / ĐỘ ẨM - vẫn dùng schema params, nhưng có thể
    #    chịu ảnh hưởng nhẹ của môi trường nếu muốn.
    # =========================
    if 'light_level' in params:
        level_min, level_max = params['light_level']
        fail_light_level = np.random.uniform(level_min, level_max)

        # nếu có mưa lớn liên tục -> giả định trời u ám hơn -> giảm bớt một chút
        if df_env is not None and 'precip_mm' in df_env.columns:
            precip_mean = df_env.loc[fail_start_step:fail_end_step, 'precip_mm'].mean()
            shade_factor = max(0.5, 1.0 - precip_mean / 50.0)  # mưa nhiều -> ít sáng bớt
            fail_light_level *= shade_factor

        df_fail.loc[fail_start_step:, 'light'] = fail_light_level + np.random.normal(
            0, 2.0, num_steps - fail_start_step
        )

    if 'co2_level' in params and scenario != 'OVER_VENTILATION':
        # OVER_VENTILATION đã cập nhật CO2 ở trên
        level_min, level_max = params['co2_level']
        fail_co2_level = np.random.uniform(level_min, level_max)
        df_fail.loc[fail_start_step:, 'co2'] = fail_co2_level + np.random.normal(
            0, 2.0, num_steps - fail_start_step
        )

    if 'humid_level' in params and scenario not in ['DOOR_AJAR', 'LIGHT_EXPOSURE', 'OVER_VENTILATION',
                                                    'HOT_HUMID_FAIL', 'SATURATED_HEAT_FAIL']:
        # các scenario này đã xử lý humid riêng ở trên
        level_min, level_max = params['humid_level']
        fail_humid_level = np.random.uniform(level_min, level_max)
        df_fail.loc[fail_start_step:, 'humid'] = fail_humid_level + np.random.normal(
            0, 0.1, num_steps - fail_start_step
        )

    return df_fail

def _apply_labeling(df, p, num_steps):
    """NÂNG CẤP: Áp dụng gán nhãn chung dựa trên HỒ SƠ (p)."""
    df['class'] = 'Good'
    failure_triggered = False

    consecutive_steps_counters = {rule_name: 0 for rule_name in p['failure_rules']}

    for i in range(1, num_steps):
        if failure_triggered:
            df.loc[i, 'class'] = 'Bad'
            continue

        for rule_name, rule_params in p['failure_rules'].items():

            is_condition_met = True # Giả định quy tắc được đáp ứng

            # --- Kiểm tra tất cả các điều kiện trong quy tắc --- ( check dk and)
            if 'TEMP_FAIL' in rule_params['conditions']:
                if not (df.loc[i, 'temp'] > rule_params['temp_trigger']): is_condition_met = False

            if 'TEMP_LOW_FAIL' in rule_params['conditions']:
                if not (df.loc[i, 'temp'] < rule_params['temp_trigger_low']): is_condition_met = False

            if 'LIGHT_FAIL' in rule_params['conditions']:
                if not (df.loc[i, 'light'] > rule_params['light_trigger']): is_condition_met = False

            if 'LIGHT_LOW_FAIL' in rule_params['conditions']:
                if not (df.loc[i, 'light'] < rule_params['light_trigger_low']): is_condition_met = False

            if 'HUMID_FAIL' in rule_params['conditions']:
                if not (df.loc[i, 'humid'] > rule_params['humid_trigger']): is_condition_met = False

            if 'CO2_LOW_FAIL' in rule_params['conditions']:
                if not (df.loc[i, 'co2'] < rule_params['co2_trigger_low']): is_condition_met = False

            # --- Xử lý bộ đếm ---
            if is_condition_met:
                consecutive_steps_counters[rule_name] += 1

                # Kiểm tra yếu tố tăng tốc
                is_accelerated = False
                if 'co2_accel_trigger' in rule_params and (df.loc[i, 'co2'] > rule_params['co2_accel_trigger']):
                    is_accelerated = True
                if 'temp_accel_trigger_low' in rule_params and (df.loc[i, 'temp'] <= rule_params['temp_accel_trigger_low']):
                    is_accelerated = True

                required_steps = rule_params.get('duration_steps_fast', 99999) if is_accelerated else rule_params.get('duration_steps_normal', 99999)

                if consecutive_steps_counters[rule_name] >= required_steps:
                    failure_triggered = True
                    fail_start_index = i - consecutive_steps_counters[rule_name] + 1
                    df.loc[fail_start_index:, 'class'] = 'Bad'
                    break # Dừng kiểm tra các quy tắc khác
            else:
                consecutive_steps_counters[rule_name] = 0 # Reset bộ đếm

        if failure_triggered: break # Dừng vòng lặp i

    return df, failure_triggered

def _run_single_trip(df_gps_trip, trip_id, p):
    """Hàm lõi: Chạy mô phỏng cho 1 chuyến đi với 1 HỒ SƠ (p)"""
    start_time = df_gps_trip['timestamp'].min()
    end_time = df_gps_trip['timestamp'].max()

    df_sim = _create_time_backbone(start_time, end_time)
    num_steps = len(df_sim)
    if num_steps < 1: return None


    # GHÉP ĐẦY ĐỦ CÁC YẾU TỐ THỜI TIẾT BÊN NGOÀI
    df_env = pd.merge_asof(
        df_sim.sort_values('timestamp'),
        df_gps_trip[[
            'timestamp',
            'temperature_C',
            'humidity_%',
            'dew_point_C',
            'pressure_hPa',
            'wind_speed_kmh',
            'precipitation_mm'
        ]].sort_values('timestamp'),
        on='timestamp',
        direction='nearest'
    )

    # Đổi tên cho rõ ràng
    df_env = df_env.rename(columns={
        'temperature_C': 'temp_out',
        'humidity_%': 'humid_out',
        'dew_point_C': 'dew_point_out',
        'pressure_hPa': 'pressure_out',
        'wind_speed_kmh': 'wind_kmh',
        'precipitation_mm': 'precip_mm'
    })




    chosen_scenario = np.random.choice(p['failure_scenarios'])
    df_baseline = _simulate_baseline(num_steps, p)
    df_with_failure = _inject_failure(df_baseline, chosen_scenario, p, num_steps, df_env = df_env)
    df_sim = pd.concat([df_sim, df_with_failure], axis=1)
    df_sim, failure_triggered = _apply_labeling(df_sim, p, num_steps)

    if chosen_scenario == 'GOOD' and failure_triggered:
        df_sim['class'] = 'Good'

    df_final_trip = pd.merge_asof(
        df_sim.sort_values(by='timestamp'),
        df_gps_trip.sort_values(by='timestamp'),
        on='timestamp'
    )

    df_final_trip['trip_id'] = trip_id
    df_final_trip['failure_scenario'] = chosen_scenario
    df_final_trip['fruit_cate'] = p['fruit_name']

    print(f"    > Hoàn tất: {trip_id} ({p['fruit_name']}). Kịch bản: {chosen_scenario}. Steps: {num_steps}.")
    return df_final_trip


# ======================================================================
# PHẦN 3: HÀM "ĐIỀU PHỐI" (DISPATCHER) CHÍNH (ĐÃ NÂNG CẤP)
# ======================================================================

def dispatch_simulation_by_fruit(fruit_cate, df_gps_trip, trip_id):
    """
    Hàm điều phối chính.
    Nhận tên trái cây, chọn hồ sơ (profile) và chạy mô phỏng.
    """

    # 1. Chọn Hồ sơ (Profile)
    if fruit_cate == 'Orange':
        profile = _get_orange_profile()
    elif fruit_cate == 'Banana':
        profile = _get_banana_profile()
    elif fruit_cate == 'Tomato':
        profile = _get_tomato_profile()
    elif fruit_cate == 'Pineapple':
        profile = _get_pineapple_profile()
    else:
        print(f"    > Cảnh báo: Không tìm thấy hồ sơ cho '{fruit_cate}'. Dùng 'Orange' làm mặc định.")
        profile = _get_orange_profile()

    # 2. Chạy cỗ máy mô phỏng chung
    return _run_single_trip(df_gps_trip, trip_id, profile)