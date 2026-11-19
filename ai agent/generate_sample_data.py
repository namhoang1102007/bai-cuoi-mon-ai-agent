import os
import pandas as pd

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(DATA_DIR, exist_ok=True)


def build_datasets():
    # 1. Danh mục sản phẩm, giá niêm yết mới nhất, tồn kho khả dụng & thời gian triển khai
    products = [
        {
            "ma_sp": "MA-SRV-01",
            "ten_sp": "Máy chủ Dell PowerEdge R760xs (2x Xeon Silver, 64GB RAM, 2x 960GB SSD)",
            "tu_khoa": "máy chủ, server, dell r760, r760xs, dell poweredge",
            "nhom_sp": "Hạ tầng Server",
            "don_vi": "Bộ",
            "don_gia_niem_yet": 145000000,
            "gia_cu_tham_chieu": 138000000,
            "ton_kha_dung": 4,
            "tg_trien_khai_co_san_ngay": 5,
            "tg_nhap_them_ngay": 18,
            "chiet_khau_nv_toi_da_pct": 5.0,
            "chiet_khau_tp_toi_da_pct": 10.0,
            "bao_hanh": "36 tháng ProSupport",
        },
        {
            "ma_sp": "MA-SW-01",
            "ten_sp": "Thiết bị chuyển mạch Cisco Catalyst C9200L-24P-4G (24 Port PoE+)",
            "tu_khoa": "switch, cisco, c9200, c9200l, chuyển mạch, switch 24 port, switch poe",
            "nhom_sp": "Thiết bị Mạng",
            "don_vi": "Chiếc",
            "don_gia_niem_yet": 42000000,
            "gia_cu_tham_chieu": 39500000,
            "ton_kha_dung": 12,
            "tg_trien_khai_co_san_ngay": 3,
            "tg_nhap_them_ngay": 14,
            "chiet_khau_nv_toi_da_pct": 6.0,
            "chiet_khau_tp_toi_da_pct": 12.0,
            "bao_hanh": "36 tháng chính hãng",
        },
        {
            "ma_sp": "MA-FW-01",
            "ten_sp": "Thiết bị tường lửa Fortinet FortiGate 100F kèm License bảo mật 1 năm",
            "tu_khoa": "firewall, tường lửa, fortigate, 100f, fortinet, bảo mật mạng",
            "nhom_sp": "Bảo mật & An toàn thông tin",
            "don_vi": "Bộ",
            "don_gia_niem_yet": 68000000,
            "gia_cu_tham_chieu": 65000000,
            "ton_kha_dung": 3,
            "tg_trien_khai_co_san_ngay": 4,
            "tg_nhap_them_ngay": 15,
            "chiet_khau_nv_toi_da_pct": 5.0,
            "chiet_khau_tp_toi_da_pct": 10.0,
            "bao_hanh": "24 tháng FortiCare",
        },
        {
            "ma_sp": "MA-WIFI-01",
            "ten_sp": "Bộ phát Wifi doanh nghiệp Aruba Instant On AP22 (Wi-Fi 6)",
            "tu_khoa": "wifi, access point, ap22, aruba, bộ phát wifi, wifi 6",
            "nhom_sp": "Thiết bị Mạng",
            "don_vi": "Chiếc",
            "don_gia_niem_yet": 5800000,
            "gia_cu_tham_chieu": 5500000,
            "ton_kha_dung": 35,
            "tg_trien_khai_co_san_ngay": 2,
            "tg_nhap_them_ngay": 10,
            "chiet_khau_nv_toi_da_pct": 7.0,
            "chiet_khau_tp_toi_da_pct": 12.0,
            "bao_hanh": "24 tháng",
        },
        {
            "ma_sp": "MA-LAP-01",
            "ten_sp": "Laptop doanh nghiệp Dell Latitude 5440 (Core i7, 16GB RAM, 512GB SSD)",
            "tu_khoa": "laptop, máy tính xách tay, dell latitude, latitude 5440, laptop văn phòng",
            "nhom_sp": "Thiết bị Đầu cuối",
            "don_vi": "Chiếc",
            "don_gia_niem_yet": 26500000,
            "gia_cu_tham_chieu": 25000000,
            "ton_kha_dung": 20,
            "tg_trien_khai_co_san_ngay": 3,
            "tg_nhap_them_ngay": 12,
            "chiet_khau_nv_toi_da_pct": 5.0,
            "chiet_khau_tp_toi_da_pct": 9.0,
            "bao_hanh": "36 tháng Onsite",
        },
        {
            "ma_sp": "MA-PC-01",
            "ten_sp": "Máy tính để bàn HP Pro Tower 400 G9 (Core i5, 16GB RAM, 512GB SSD + Màn 24 inch)",
            "tu_khoa": "pc, máy tính bàn, desktop, hp pro tower, hp 400 g9, máy bộ",
            "nhom_sp": "Thiết bị Đầu cuối",
            "don_vi": "Bộ",
            "don_gia_niem_yet": 18200000,
            "gia_cu_tham_chieu": 17500000,
            "ton_kha_dung": 25,
            "tg_trien_khai_co_san_ngay": 3,
            "tg_nhap_them_ngay": 10,
            "chiet_khau_nv_toi_da_pct": 5.0,
            "chiet_khau_tp_toi_da_pct": 9.0,
            "bao_hanh": "24 tháng",
        },
        {
            "ma_sp": "MA-NAS-01",
            "ten_sp": "Hệ thống lưu trữ mạng Synology NAS RS1221+ (8-Bay Rackmount, kèm 4x 8TB Enterprise)",
            "tu_khoa": "nas, lưu trữ, synology, rs1221+, thiết bị lưu trữ",
            "nhom_sp": "Hạ tầng Server",
            "don_vi": "Bộ",
            "don_gia_niem_yet": 74000000,
            "gia_cu_tham_chieu": 71000000,
            "ton_kha_dung": 2,
            "tg_trien_khai_co_san_ngay": 4,
            "tg_nhap_them_ngay": 14,
            "chiet_khau_nv_toi_da_pct": 5.0,
            "chiet_khau_tp_toi_da_pct": 10.0,
            "bao_hanh": "36 tháng",
        },
        {
            "ma_sp": "MA-VC-01",
            "ten_sp": "Hệ thống Hội nghị truyền hình Logitech Rally Bar (Phòng họp 15-25 người)",
            "tu_khoa": "hội nghị truyền hình, logitech, rally bar, camera phòng họp, thiết bị họp trực tuyến",
            "nhom_sp": "Thiết bị Phòng họp",
            "don_vi": "Bộ",
            "don_gia_niem_yet": 89000000,
            "gia_cu_tham_chieu": 85000000,
            "ton_kha_dung": 5,
            "tg_trien_khai_co_san_ngay": 4,
            "tg_nhap_them_ngay": 14,
            "chiet_khau_nv_toi_da_pct": 6.0,
            "chiet_khau_tp_toi_da_pct": 11.0,
            "bao_hanh": "24 tháng",
        },
        {
            "ma_sp": "MA-SVC-01",
            "ten_sp": "Gói dịch vụ Triển khai, Cấu hình hạ tầng mạng & Chuyển đổi hệ thống tận nơi",
            "tu_khoa": "dịch vụ triển khai, lắp đặt, cấu hình mạng, thi công, cài đặt hệ thống",
            "nhom_sp": "Dịch vụ Kỹ thuật",
            "don_vi": "Gói",
            "don_gia_niem_yet": 25000000,
            "gia_cu_tham_chieu": 20000000,
            "ton_kha_dung": 99,
            "tg_trien_khai_co_san_ngay": 5,
            "tg_nhap_them_ngay": 5,
            "chiet_khau_nv_toi_da_pct": 8.0,
            "chiet_khau_tp_toi_da_pct": 15.0,
            "bao_hanh": "12 tháng hỗ trợ kỹ thuật",
        },
        {
            "ma_sp": "MA-SVC-02",
            "ten_sp": "Gói dịch vụ Bảo trì & Quản trị vận hành CNTT định kỳ 24/7 (Managed IT 1 năm)",
            "tu_khoa": "bảo trì, quản trị vận hành, managed it, dịch vụ bảo trì, hỗ trợ 24/7",
            "nhom_sp": "Dịch vụ Kỹ thuật",
            "don_vi": "Gói/Năm",
            "don_gia_niem_yet": 48000000,
            "gia_cu_tham_chieu": 45000000,
            "ton_kha_dung": 99,
            "tg_trien_khai_co_san_ngay": 3,
            "tg_nhap_them_ngay": 3,
            "chiet_khau_nv_toi_da_pct": 8.0,
            "chiet_khau_tp_toi_da_pct": 15.0,
            "bao_hanh": "SLA cam kết 99.9%",
        },
    ]

    # 2. Chính sách chiết khấu & phân quyền phê duyệt của Công ty Minh An
    policies = [
        {
            "ma_chinh_sach": "CS-01",
            "cap_phe_duyet": "Nhân viên Kinh doanh (NVKD)",
            "nguoi_phu_trach_duyet": "NVKD Phụ trách trực tiếp",
            "gia_tri_don_tu_vnd": 0,
            "gia_tri_don_den_vnd": 300000000,
            "chiet_khau_toi_da_pct": 5.0,
            "dieu_kien_ap_dung": "Đơn hàng <= 300 triệu VNĐ, chiết khấu <= 5%, đủ tồn kho và kịp tiến độ",
            "sla_phan_hoi_gio": 2,
        },
        {
            "ma_chinh_sach": "CS-02",
            "cap_phe_duyet": "Trưởng phòng Kinh doanh",
            "nguoi_phu_trach_duyet": "Ông Trần Quốc Tuấn - Trưởng phòng KD",
            "gia_tri_don_tu_vnd": 300000001,
            "gia_tri_don_den_vnd": 1000000000,
            "chiet_khau_toi_da_pct": 10.0,
            "dieu_kien_ap_dung": "Đơn hàng > 300 triệu đến 1 tỷ VNĐ, hoặc chiết khấu từ > 5% đến 10%, hoặc cần điều phối tồn kho/tiến độ gấp",
            "sla_phan_hoi_gio": 4,
        },
        {
            "ma_chinh_sach": "CS-03",
            "cap_phe_duyet": "Ban Giám đốc (Giám đốc Kinh doanh / TGĐ)",
            "nguoi_phu_trach_duyet": "Bà Nguyễn Minh An - Phó TGĐ Phụ trách KD",
            "gia_tri_don_tu_vnd": 1000000001,
            "gia_tri_don_den_vnd": 99999999999,
            "chiet_khau_toi_da_pct": 15.0,
            "dieu_kien_ap_dung": "Đơn hàng > 1 tỷ VNĐ, hoặc khách đề nghị chiết khấu đặc biệt > 10%, hoặc cam kết SLA phạt hợp đồng",
            "sla_phan_hoi_gio": 8,
        },
    ]

    # 3. Danh sách 6 Nhân viên Kinh doanh (NVKD)
    sales_reps = [
        {"ma_nvkd": "NVKD-01", "ho_ten": "Nguyễn Hoàng Nam", "email": "nam.nh@minhan.vn", "chuyen_mon": "Hạ tầng Server & Bảo mật", "so_co_hoi_dang_xu_ly": 12},
        {"ma_nvkd": "NVKD-02", "ho_ten": "Lê Thị Thu Hà", "email": "ha.ltt@minhan.vn", "chuyen_mon": "Thiết bị Đầu cuối & Phòng họp", "so_co_hoi_dang_xu_ly": 10},
        {"ma_nvkd": "NVKD-03", "ho_ten": "Phạm Minh Đức", "email": "duc.pm@minhan.vn", "chuyen_mon": "Thiết bị Mạng & Dịch vụ Kỹ thuật", "so_co_hoi_dang_xu_ly": 14},
        {"ma_nvkd": "NVKD-04", "ho_ten": "Vũ Ngọc Ánh", "email": "anh.vn@minhan.vn", "chuyen_mon": "Khách hàng Doanh nghiệp FDI & Sản xuất", "so_co_hoi_dang_xu_ly": 9},
        {"ma_nvkd": "NVKD-05", "ho_ten": "Đỗ Quang Huy", "email": "huy.dq@minhan.vn", "chuyen_mon": "Hạ tầng Server & Lưu trữ NAS", "so_co_hoi_dang_xu_ly": 11},
        {"ma_nvkd": "NVKD-06", "ho_ten": "Trương Mỹ Linh", "email": "linh.tm@minhan.vn", "chuyen_mon": "Giải pháp Tổng thể & Dịch vụ Managed IT", "so_co_hoi_dang_xu_ly": 8},
    ]

    # 4. Danh sách Yêu cầu Khách hàng B2B thực tế (bao phủ tất cả kịch bản trong quy trình)
    customer_requests = [
        {
            "ma_yeu_cau": "YC-2026-001",
            "ngay_nhan": "2026-11-11 08:30",
            "kenh_tiep_nhan": "Email",
            "ten_khach_hang": "Công ty Cổ phần Logistics Đông Á",
            "nguoi_lien_he": "Anh Lê Văn Khoa - Trưởng phòng IT",
            "email_kh": "khoa.lv@dongalogistics.vn",
            "noi_dung_yeu_cau": (
                "Chào Minh An, bên mình chuẩn bị mở thêm trung tâm điều phối tại Hải Phòng nên cần báo giá gấp: "
                "02 bộ Máy chủ Dell PowerEdge R760xs, 04 chiếc Switch Cisco C9200L 24 port PoE+, "
                "01 thiết bị tường lửa Fortinet FortiGate 100F và 01 gói dịch vụ triển khai cấu hình hạ tầng mạng tận nơi. "
                "Ngân sách tổng bên mình được duyệt tối đa là 520.000.000 VNĐ. "
                "Đề nghị mức chiết khấu thương mại 8% trên tổng đơn. Thời hạn triển khai bàn giao hoàn tất trong vòng 7 ngày."
            ),
            "ngan_sach_vnd": 520000000,
            "thoi_han_yeu_cau_ngay": 7,
            "de_nghi_chiet_khau_pct": 8.0,
            "nvkd_phu_trach_goi_y": "NVKD-01",
        },
        {
            "ma_yeu_cau": "YC-2026-002",
            "ngay_nhan": "2026-11-11 09:05",
            "kenh_tiep_nhan": "Biểu mẫu Web",
            "ten_khach_hang": "Công ty TNHH Giải pháp Phần mềm Sao Khuê",
            "nguoi_lien_he": "Chị Nguyễn Thanh Tâm - Bộ phận Mua hàng",
            "email_kh": "tam.nt@saokhuesoft.com",
            "noi_dung_yeu_cau": (
                "Gửi công ty Minh An, Sao Khuê cần mua bổ sung 15 chiếc Laptop doanh nghiệp Dell Latitude 5440 "
                "và 10 bộ phát Wifi doanh nghiệp Aruba Instant On AP22 cho nhân sự mới. "
                "Ngân sách dự kiến khoảng 450.000.000 VNĐ, bên mình mong muốn chiết khấu 4% và giao hàng trong 5 ngày làm việc."
            ),
            "ngan_sach_vnd": 450000000,
            "thoi_han_yeu_cau_ngay": 5,
            "de_nghi_chiet_khau_pct": 4.0,
            "nvkd_phu_trach_goi_y": "NVKD-02",
        },
        {
            "ma_yeu_cau": "YC-2026-003",
            "ngay_nhan": "2026-11-11 09:40",
            "kenh_tiep_nhan": "Email",
            "ten_khach_hang": "Tập đoàn Sản xuất Công nghiệp Hòa Bình Xanh",
            "nguoi_lien_he": "Anh Trần Đình Trọng - Giám đốc CNTT",
            "email_kh": "trong.td@hoabinhxanh.vn",
            "noi_dung_yeu_cau": (
                "Chào Minh An, nhà máy số 2 của chúng tôi cần nâng cấp toàn diện hệ thống lưu trữ và máy chủ. "
                "Yêu cầu báo giá: 06 bộ Máy chủ Dell PowerEdge R760xs, 04 bộ thiết bị lưu trữ Synology NAS RS1221+, "
                "03 bộ tường lửa FortiGate 100F, 01 gói dịch vụ triển khai cấu hình mạng và 01 gói dịch vụ bảo trì Managed IT 1 năm. "
                "Ngân sách phê duyệt là 1.250.000.000 VNĐ, đề nghị chiết khấu đặc biệt 12%. "
                "Yêu cầu phải bàn giao và nghiệm thu toàn bộ trong 6 ngày tới để kịp lịch chạy thử nhà máy!"
            ),
            "ngan_sach_vnd": 1250000000,
            "thoi_han_yeu_cau_ngay": 6,
            "de_nghi_chiet_khau_pct": 12.0,
            "nvkd_phu_trach_goi_y": "NVKD-05",
        },
        {
            "ma_yeu_cau": "YC-2026-004",
            "ngay_nhan": "2026-11-11 10:15",
            "kenh_tiep_nhan": "Email",
            "ten_khach_hang": "Công ty Cổ phần Thương mại Quốc tế Á Châu",
            "nguoi_lien_he": "Chị Hoàng Mai Hương - Hành chính Nhân sự",
            "email_kh": "huong.hm@achautrade.vn",
            "noi_dung_yeu_cau": (
                "Chào bạn, văn phòng mới của Á Châu tại Quận 1 đang cần trang bị một số máy tính để bàn HP Pro Tower, "
                "hệ thống hội nghị truyền hình Logitech cho phòng họp lớn và lắp đặt hệ thống Wifi Aruba. "
                "Nhờ Minh An gửi báo giá sớm giúp mình kèm mức chiết khấu tốt nhất nhé, bên mình chưa chốt ngân sách cụ thể."
            ),
            "ngan_sach_vnd": 0,
            "thoi_han_yeu_cau_ngay": 0,
            "de_nghi_chiet_khau_pct": 0.0,
            "nvkd_phu_trach_goi_y": "NVKD-04",
        },
        {
            "ma_yeu_cau": "YC-2026-005",
            "ngay_nhan": "2026-11-11 11:00",
            "kenh_tiep_nhan": "Biểu mẫu Web",
            "ten_khach_hang": "Ngân hàng số FinNext Việt Nam (Chi nhánh Miền Bắc)",
            "nguoi_lien_he": "Anh Ngô Gia Bảo - Trưởng bộ phận Mua sắm CNTT",
            "email_kh": "bao.ng@finnext.vn",
            "noi_dung_yeu_cau": (
                "Đề nghị Minh An chào giá gói trang bị phòng họp & làm việc gồm: "
                "03 bộ Hội nghị truyền hình Logitech Rally Bar, 20 bộ máy tính để bàn HP Pro Tower 400 G9, "
                "06 chiếc Switch Cisco C9200L 24P và 01 gói dịch vụ triển khai lắp đặt. "
                "Theo báo giá cũ năm ngoái của Minh An thì đơn giá khá thấp nên ngân sách chúng tôi chỉ để 800.000.000 VNĐ "
                "và đề nghị chiết khấu 9%. Thời hạn triển khai trong 10 ngày."
            ),
            "ngan_sach_vnd": 800000000,
            "thoi_han_yeu_cau_ngay": 10,
            "de_nghi_chiet_khau_pct": 9.0,
            "nvkd_phu_trach_goi_y": "NVKD-06",
        },
        {
            "ma_yeu_cau": "YC-2026-006",
            "ngay_nhan": "2026-11-11 13:20",
            "kenh_tiep_nhan": "Email",
            "ten_khach_hang": "Bệnh viện Đa khoa Quốc tế Tâm Đức",
            "nguoi_lien_he": "Anh Đặng Quốc Việt - Phụ trách Hạ tầng",
            "email_kh": "viet.dq@bvquoctetamduc.vn",
            "noi_dung_yeu_cau": (
                "Kính gửi Công ty Minh An, Bệnh viện đang cần nâng cấp hệ thống mạng nội bộ và máy trạm cho khu khám bệnh mới, "
                "bao gồm khoảng 25 bộ phát Wifi Aruba AP22 và một số Switch Cisco C9200L cùng gói bảo trì 24/7. "
                "Tuy nhiên chúng tôi chưa xác định số lượng Switch chính xác và thời hạn bàn giao. "
                "Ngân sách tạm tính khoảng 320.000.000 VNĐ, đề nghị chiết khấu 6%. Nhờ tư vấn và báo giá."
            ),
            "ngan_sach_vnd": 320000000,
            "thoi_han_yeu_cau_ngay": 0,
            "de_nghi_chiet_khau_pct": 6.0,
            "nvkd_phu_trach_goi_y": "NVKD-03",
        },
    ]

    df_products = pd.DataFrame(products)
    df_policies = pd.DataFrame(policies)
    df_reps = pd.DataFrame(sales_reps)
    df_requests = pd.DataFrame(customer_requests)

    # Save CSV files
    df_products.to_csv(os.path.join(DATA_DIR, "danh_muc_san_pham_ton_kho.csv"), index=False, encoding="utf-8-sig")
    df_policies.to_csv(os.path.join(DATA_DIR, "chinh_sach_chiet_khau_duyet.csv"), index=False, encoding="utf-8-sig")
    df_reps.to_csv(os.path.join(DATA_DIR, "danh_sach_nvkd.csv"), index=False, encoding="utf-8-sig")
    df_requests.to_csv(os.path.join(DATA_DIR, "yeu_cau_khach_hang_mau.csv"), index=False, encoding="utf-8-sig")

    # Save combined Excel file (Multi-sheet) + Individual Excel file for requests
    excel_all_path = os.path.join(DATA_DIR, "du_lieu_minh_an_b2b_full.xlsx")
    with pd.ExcelWriter(excel_all_path, engine="openpyxl") as writer:
        df_requests.to_excel(writer, sheet_name="YeuCauKhachHang", index=False)
        df_products.to_excel(writer, sheet_name="SanPham_Gia_TonKho", index=False)
        df_policies.to_excel(writer, sheet_name="ChinhSachPhapDuyet", index=False)
        df_reps.to_excel(writer, sheet_name="NhanVienKinhDoanh", index=False)

    excel_req_path = os.path.join(DATA_DIR, "yeu_cau_khach_hang_mau.xlsx")
    df_requests.to_excel(excel_req_path, index=False)

    print("Sample datasets created successfully in:", DATA_DIR)


if __name__ == "__main__":
    build_datasets()

