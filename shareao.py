import os
import random
import requests
import time
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from fake_useragent import UserAgent

user_agents = UserAgent()

CAU_HINH = {
    'DELAY_TOI_THIEU': 0.5,
    'DELAY_TOI_DA': 2.0,
    'SO_LAN_THU_LAI': 3,
    'THOI_GIAN_CHO_REQUEST': 30,
    'XOAY_USER_AGENT': True
}

def lay_user_agent_ngau_nhien():
    if CAU_HINH['XOAY_USER_AGENT']:
        return user_agents.random
    return "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"

def kiem_tra_cookie(cookie):
    return all(f'{truong}=' in cookie for truong in ['c_user', 'xs'])

def lay_token(cookie, so_lan_thu=0):
    if not kiem_tra_cookie(cookie):
        return None
    headers = {
        'cookie': cookie,
        'user-agent': lay_user_agent_ngau_nhien()
    }
    try:
        response = requests.get(
            'https://business.facebook.com/content_management',
            headers=headers,
            timeout=CAU_HINH['THOI_GIAN_CHO_REQUEST']
        )
        response.raise_for_status()
        import re
        ket_qua = re.search(r'EAAG\w+', response.text)
        if ket_qua:
            return f'{cookie}|{ket_qua.group(0)}'
    except Exception:
        if so_lan_thu < CAU_HINH['SO_LAN_THU_LAI']:
            time.sleep(random.uniform(1, 3))
            return lay_token(cookie, so_lan_thu + 1)
    return None

def chia_se(tach, id_chia_se, so_lan_thu=0):
    if not tach or '|' not in tach:
        print(f"Share thất bại | ID: {id_chia_se}")
        return False
    cookie, token = tach.split('|', 1)
    headers = {
        'cookie': cookie,
        'user-agent': lay_user_agent_ngau_nhien()
    }
    link = random.choice([
        f'https://m.facebook.com/{id_chia_se}',
        f'https://www.facebook.com/{id_chia_se}'
    ])
    params = {
        'link': link,
        'published': 0, 
        'access_token': token,
        'fields': 'id'
    }
    try:
        res = requests.post(
            'https://graph.facebook.com/v15.0/me/feed',
            headers=headers,
            params=params,
            timeout=CAU_HINH['THOI_GIAN_CHO_REQUEST']
        )
        if res.status_code == 200 and res.json().get('id'):
            print(f"Share thành công | ID: {id_chia_se}")
            return True
        else:
            print(f"Share thất bại | ID: {id_chia_se} | Lỗi: {res.text}")
    except Exception as e:
        if so_lan_thu < CAU_HINH['SO_LAN_THU_LAI']:
            time.sleep(random.uniform(1, 3))
            return chia_se(tach, id_chia_se, so_lan_thu + 1)
        print(f"Share thất bại | ID: {id_chia_se} | Lỗi: {str(e)}")
    return False

def chia_se_voi_cookie(cookie_token, id_chia_se, stt_cookie=None):
    """Hàm share với thông tin cookie (có thể là cookie hoặc token)"""
    if stt_cookie:
        prefix = f"[Cookie {stt_cookie}]"
    else:
        prefix = "[Cookie]"
    
    if '|' in cookie_token:
        # Nếu là token (cookie|token)
        return chia_se(cookie_token, id_chia_se)
    else:
        # Nếu chỉ là cookie, cần lấy token trước
        token = lay_token(cookie_token)
        if token:
            return chia_se(token, id_chia_se)
        else:
            print(f"{prefix} Không lấy được token | ID: {id_chia_se}")
            return False

def run_tool_nhieu_cookie_sole(danh_sach_cookie, danh_sach_post_id, share_moi_bai=1, delay=1.0, threads_per_cookie=3):
    """
    Chạy tool với nhiều cookie và nhiều bài viết theo kiểu sole
    
    Args:
        danh_sach_cookie: Danh sách cookie Facebook
        danh_sach_post_id: Danh sách ID bài viết cần share
        share_moi_bai: Số lần share cho mỗi bài viết
        delay: Thời gian delay giữa các request
        threads_per_cookie: Số thread cho mỗi cookie
    """
    print(f"Đang xử lý {len(danh_sach_cookie)} cookie và {len(danh_sach_post_id)} bài viết...")
    
    # Lấy token cho tất cả cookie
    tokens = []
    cookie_hop_le = []
    
    with ThreadPoolExecutor(max_workers=min(5, len(danh_sach_cookie))) as executor:
        future_to_cookie = {executor.submit(lay_token, cookie): cookie for cookie in danh_sach_cookie}
        for future in as_completed(future_to_cookie):
            cookie = future_to_cookie[future]
            try:
                token = future.result()
                if token:
                    tokens.append(token)
                    cookie_hop_le.append(cookie)
                    print(f"✓ Cookie {len(cookie_hop_le)}: Lấy token thành công")
                else:
                    print(f"✗ Cookie: Không lấy được token")
            except Exception as e:
                print(f"✗ Cookie: Lỗi khi lấy token - {str(e)}")
    
    if not tokens:
        print("Không có cookie nào hợp lệ!")
        return
    
    print(f"\nĐã lấy token thành công cho {len(tokens)}/{len(danh_sach_cookie)} cookie")
    
    # Tạo danh sách tasks theo kiểu sole cho nhiều cookie
    tasks = []
    for lap in range(share_moi_bai):
        for post_id in danh_sach_post_id:
            for token in tokens:
                tasks.append((token, post_id))
    
    # Xáo trộn tasks để các cookie share ngẫu nhiên
    random.shuffle(tasks)
    
    print(f"Tổng số lượt share sẽ thực hiện: {len(tasks)}")
    print(f"Số cookie hoạt động: {len(tokens)}")
    print(f"Số bài viết: {len(danh_sach_post_id)}")
    print(f"Kiểu: SOLE đa cookie (luân phiên)")
    print("\nBắt đầu share...\n")
    
    thanh_cong = 0
    that_bai = 0
    bai_thanh_cong = set()
    cookie_hoat_dong = set()
    
    def worker(task):
        token, post_id = task
        cookie_index = tokens.index(token) + 1
        return chia_se_voi_cookie(token, post_id, cookie_index), post_id, cookie_index
    
    with ThreadPoolExecutor(max_workers=threads_per_cookie * len(tokens)) as executor:
        futures = {executor.submit(worker, task): task for task in tasks}
        
        # Xử lý kết quả
        for i, future in enumerate(as_completed(futures)):
            try:
                result, post_id, cookie_index = future.result()
                if result:
                    thanh_cong += 1
                    bai_thanh_cong.add(post_id)
                    cookie_hoat_dong.add(cookie_index)
                else:
                    that_bai += 1
                
                # Progress
                if (i + 1) % 10 == 0 or (i + 1) == len(tasks):
                    print(f"Đã xử lý: {i + 1}/{len(tasks)} | Thành công: {thanh_cong} | Thất bại: {that_bai}")
                    
            except Exception as e:
                that_bai += 1
                print(f"Lỗi khi xử lý task: {str(e)}")
            
            # Delay giữa các request
            if i < len(tasks) - 1:
                time.sleep(delay * random.uniform(0.8, 1.2))
    
    # Hiển thị tổng kết chi tiết
    print("\n" + "="*60)
    print("TỔNG KẾT CHI TIẾT - ĐA COOKIE SOLE")
    print("="*60)
    print(f"Tổng cookie: {len(danh_sach_cookie)}")
    print(f"Cookie hợp lệ: {len(tokens)}")
    print(f"Cookie hoạt động: {len(cookie_hoat_dong)}")
    print(f"Tổng bài viết: {len(danh_sach_post_id)}")
    print(f"Tổng lượt share: {thanh_cong + that_bai}")
    print(f"Share thành công: {thanh_cong}")
    print(f"Share thất bại: {that_bai}")
    print(f"Tỷ lệ thành công: {(thanh_cong/(thanh_cong+that_bai)*100 if (thanh_cong+that_bai) > 0 else 0):.1f}%")
    print(f"Bài viết được share thành công: {len(bai_thanh_cong)}")
    
    if bai_thanh_cong:
        print(f"\nDanh sách bài share thành công:")
        for post_id in sorted(bai_thanh_cong):
            print(f"  - {post_id}")

def run_tool_mot_cookie_sole(cookie, danh_sach_post_id, share_moi_bai=1, delay=1.0, threads=5):
    """Chạy tool với 1 cookie và nhiều bài viết theo kiểu sole"""
    token = lay_token(cookie)
    if not token:
        print("Cookie không hợp lệ hoặc không lấy được token")
        return
    
    print(f"Đã lấy token thành công! Sẽ share {len(danh_sach_post_id)} bài viết")
    print(f"Kiểu share: SOLE (luân phiên)")
    
    thanh_cong = 0
    that_bai = 0
    bai_thanh_cong = set()
    
    # Tạo danh sách tasks theo kiểu sole
    tasks = []
    for lap in range(share_moi_bai):
        for post_id in danh_sach_post_id:
            tasks.append(post_id)
    
    print(f"Tổng số lượt share sẽ thực hiện: {len(tasks)}")
    print(f"Thứ tự share: {' -> '.join(tasks[:min(10, len(tasks))])}{'...' if len(tasks) > 10 else ''}")
    print("\nBắt đầu share...\n")
    
    with ThreadPoolExecutor(max_workers=threads) as executor:
        futures = []
        
        # Gửi requests theo thứ tự sole
        for i, post_id in enumerate(tasks):
            future = executor.submit(chia_se, token, post_id)
            futures.append((future, post_id))
            
            # Delay giữa các request
            if i < len(tasks) - 1:
                time.sleep(delay * random.uniform(0.8, 1.2))
        
        # Xử lý kết quả
        for future, post_id in futures:
            try:
                if future.result():
                    thanh_cong += 1
                    bai_thanh_cong.add(post_id)
                else:
                    that_bai += 1
            except Exception as e:
                that_bai += 1
                print(f"Lỗi khi xử lý kết quả cho {post_id}: {str(e)}")
    
    # Hiển thị tổng kết
    print("\n" + "="*50)
    print("TỔNG KẾT CHI TIẾT - 1 COOKIE SOLE")
    print("="*50)
    print(f"Tổng số bài viết: {len(danh_sach_post_id)}")
    print(f"Tổng số lượt share: {thanh_cong + that_bai}")
    print(f"Share thành công: {thanh_cong}")
    print(f"Share thất bại: {that_bai}")
    print(f"Bài viết được share thành công: {len(bai_thanh_cong)}")

def nhap_danh_sach_cookie():
    """Hàm nhập danh sách cookie từ người dùng"""
    print("\nCÁCH NHẬP DANH SÁCH COOKIE:")
    print("1. Nhập nhiều cookie, cách nhau bằng dấu |")
    print("2. Nhập từng cookie trên mỗi dòng (kết thúc bằng dòng trống)")
    print("3. Nhập từ file .txt (mỗi dòng 1 cookie)")
    
    choice = input("Chọn cách nhập (1/2/3): ").strip()
    
    danh_sach_cookie = []
    
    if choice == "1":
        cookies = input("Nhập các cookie (cách nhau bằng dấu |): ").strip()
        danh_sach_cookie = [cookie.strip() for cookie in cookies.split('|') if cookie.strip()]
    
    elif choice == "2":
        print("Nhập từng cookie (kết thúc bằng dòng trống):")
        while True:
            cookie = input().strip()
            if not cookie:
                break
            danh_sach_cookie.append(cookie)
    
    elif choice == "3":
        ten_file = input("Nhập tên file .txt: ").strip()
        try:
            with open(ten_file, 'r', encoding='utf-8') as f:
                danh_sach_cookie = [line.strip() for line in f if line.strip()]
        except FileNotFoundError:
            print("Không tìm thấy file!")
            return []
    
    else:
        print("Lựa chọn không hợp lệ!")
        return []
    
    # Loại bỏ cookie trùng lặp
    danh_sach_cookie = list(dict.fromkeys(danh_sach_cookie))
    print(f"Đã nhập {len(danh_sach_cookie)} cookie không trùng lặp")
    return danh_sach_cookie

def nhap_danh_sach_bai_viet():
    """Hàm nhập danh sách bài viết từ người dùng"""
    print("\nCÁCH NHẬP DANH SÁCH BÀI VIẾT:")
    print("1. Nhập nhiều ID, cách nhau bằng dấu phẩy")
    print("2. Nhập từng ID trên mỗi dòng (kết thúc bằng dòng trống)")
    print("3. Nhập từ file .txt (mỗi dòng 1 ID)")
    
    choice = input("Chọn cách nhập (1/2/3): ").strip()
    
    danh_sach_id = []
    
    if choice == "1":
        ids = input("Nhập các ID bài viết (cách nhau bằng dấu phẩy): ").strip()
        danh_sach_id = [id.strip() for id in ids.split(',') if id.strip()]
    
    elif choice == "2":
        print("Nhập từng ID bài viết (kết thúc bằng dòng trống):")
        while True:
            id_bai = input().strip()
            if not id_bai:
                break
            danh_sach_id.append(id_bai)
    
    elif choice == "3":
        ten_file = input("Nhập tên file .txt: ").strip()
        try:
            with open(ten_file, 'r', encoding='utf-8') as f:
                danh_sach_id = [line.strip() for line in f if line.strip()]
        except FileNotFoundError:
            print("Không tìm thấy file!")
            return []
    
    else:
        print("Lựa chọn không hợp lệ!")
        return []
    
    # Loại bỏ ID trùng lặp
    danh_sach_id = list(dict.fromkeys(danh_sach_id))
    print(f"Đã nhập {len(danh_sach_id)} bài viết không trùng lặp")
    return danh_sach_id

if __name__ == "__main__":
    os.system("cls" if os.name == "nt" else "clear")
    print("===== TOOL SHARE ẢO FACEBOOK (ĐA COOKIE + SOLE) =====")
    
    print("\nCHẾ ĐỘ CHẠY:")
    print("1. 1 Cookie + 1 Bài viết (nhiều lần)")
    print("2. 1 Cookie + Nhiều bài viết (kiểu SOLE)")
    print("3. NHIỀU Cookie + Nhiều bài viết (kiểu SOLE)")
    
    che_do = input("Chọn chế độ (1/2/3): ").strip()
    
    if che_do == "1":
        cookie = input("Nhập cookie Facebook: ").strip()
        post_id = input("Nhập ID bài viết cần share: ").strip()
        try:
            total_share = int(input("Nhập số lần share (mặc định 5): ") or 5)
            delay = float(input("Nhập delay giữa các share (giây, mặc định 1.0): ") or 1.0)
            threads = int(input("Nhập số thread chạy cùng lúc (mặc định 5): ") or 5)
        except ValueError:
            total_share, delay, threads = 5, 1.0, 5

        print("\nĐang thực hiện share ảo, vui lòng chờ...\n")
        # Gọi hàm run_tool_mot_bai cũ (cần implement lại nếu chưa có)
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        token = lay_token(cookie)
        if not token:
            print("Cookie không hợp lệ hoặc không lấy được token")
            exit()
            
        thanh_cong = 0
        that_bai = 0
        with ThreadPoolExecutor(max_workers=threads) as executor:
            futures = []
            for _ in range(total_share):
                time.sleep(delay * random.uniform(0.8, 1.2))
                futures.append(executor.submit(chia_se, token, post_id))
            for f in as_completed(futures):
                if f.result():
                    thanh_cong += 1
                else:
                    that_bai += 1
        print("\n===== TỔNG KẾT =====")
        print(f"Thành công: {thanh_cong}")
        print(f"Thất bại: {that_bai}")
    
    elif che_do == "2":
        cookie = input("Nhập cookie Facebook: ").strip()
        danh_sach_post_id = nhap_danh_sach_bai_viet()
        if not danh_sach_post_id:
            print("Không có bài viết nào để share!")
            exit()
        
        try:
            share_moi_bai = int(input("Số lượt share cho mỗi bài viết (mặc định 1): ") or 1)
            delay = float(input("Nhập delay giữa các request (giây, mặc định 1.0): ") or 1.0)
            threads = int(input("Nhập số thread chạy cùng lúc (mặc định 5): ") or 5)
        except ValueError:
            share_moi_bai, delay, threads = 1, 1.0, 5

        print(f"\nĐang thực hiện share {len(danh_sach_post_id)} bài viết...")
        run_tool_mot_cookie_sole(cookie, danh_sach_post_id, share_moi_bai, delay, threads)
    
    elif che_do == "3":
        danh_sach_cookie = nhap_danh_sach_cookie()
        if not danh_sach_cookie:
            print("Không có cookie nào để share!")
            exit()
            
        danh_sach_post_id = nhap_danh_sach_bai_viet()
        if not danh_sach_post_id:
            print("Không có bài viết nào để share!")
            exit()
        
        try:
            share_moi_bai = int(input("Số lượt share cho mỗi bài viết (mặc định 1): ") or 1)
            delay = float(input("Nhập delay giữa các request (giây, mặc định 1.0): ") or 1.0)
            threads_per_cookie = int(input("Số thread cho mỗi cookie (mặc định 3): ") or 3)
        except ValueError:
            share_moi_bai, delay, threads_per_cookie = 1, 1.0, 3

        print(f"\nĐang thực hiện share với {len(danh_sach_cookie)} cookie và {len(danh_sach_post_id)} bài viết...")
        run_tool_nhieu_cookie_sole(danh_sach_cookie, danh_sach_post_id, share_moi_bai, delay, threads_per_cookie)
    
    else:
        print("Lựa chọn không hợp lệ!")
