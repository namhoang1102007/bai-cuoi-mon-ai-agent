import io
import json
import os
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd
import requests

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


def format_vnd(amount: float) -> str:
    if amount is None or pd.isna(amount):
        return "0 VNĐ"
    return f"{int(round(amount)):,} VNĐ".replace(",", ".")


class MinhAnSalesAgent:
    def __init__(self):
        self.reload_default_data()

    def reload_default_data(self):
        prod_path = os.path.join(DATA_DIR, "danh_muc_san_pham_ton_kho.csv")
        pol_path = os.path.join(DATA_DIR, "chinh_sach_chiet_khau_duyet.csv")
        rep_path = os.path.join(DATA_DIR, "danh_sach_nvkd.csv")
        req_path = os.path.join(DATA_DIR, "yeu_cau_khach_hang_mau.csv")

        self.df_products = pd.read_csv(prod_path)
        self.df_policies = pd.read_csv(pol_path)
        self.df_reps = pd.read_csv(rep_path)
        self.df_requests = pd.read_csv(req_path)

    def load_from_uploaded_bytes(self, filename: str, content: bytes) -> Dict[str, Any]:
        """
        Reads uploaded CSV or XLSX file.
        Supports:
        1. Multi-sheet Excel containing YeuCauKhachHang, SanPham_Gia_TonKho, ChinhSachPhapDuyet, NhanVienKinhDoanh
        2. Single-sheet CSV/XLSX containing Customer Requests (or Product Catalog if columns match)
        """
        lower_name = filename.lower()
        updated_tables = []

        if lower_name.endswith(".csv"):
            try:
                df = pd.read_csv(io.BytesIO(content), encoding="utf-8-sig")
            except UnicodeDecodeError:
                df = pd.read_csv(io.BytesIO(content), encoding="latin1")
            table_type = self._apply_dataframe(df)
            updated_tables.append(table_type)
        elif lower_name.endswith(".xlsx") or lower_name.endswith(".xls"):
            xls = pd.ExcelFile(io.BytesIO(content))
            for sheet in xls.sheet_names:
                df = pd.read_excel(xls, sheet_name=sheet)
                table_type = self._apply_dataframe(df, sheet_hint=sheet)
                if table_type:
                    updated_tables.append(f"{sheet} -> {table_type}")
        else:
            raise ValueError("Định dạng file không hỗ trợ. Vui lòng tải lên file .csv hoặc .xlsx")

        return {
            "filename": filename,
            "updated_tables": updated_tables,
            "requests_count": len(self.df_requests),
            "products_count": len(self.df_products),
        }

    def load_from_google_sheet_url(self, sheet_url: str) -> Dict[str, Any]:
        """
        Converts a public Google Sheets link to an export URL and loads all sheets/data.
        """
        match = re.search(r"/spreadsheets/d/([a-zA-Z0-9-_]+)", sheet_url)
        if not match:
            raise ValueError("Link Google Sheet không hợp lệ. Vui lòng dán đúng đường dẫn Google Sheets.")

        sheet_id = match.group(1)
        gid_match = re.search(r"[#&?]gid=([0-9]+)", sheet_url)
        gid = gid_match.group(1) if gid_match else "0"

        # Try downloading as multi-sheet xlsx first so we get all tabs if present
        xlsx_export_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=xlsx"
        resp = requests.get(xlsx_export_url, timeout=15)
        if resp.status_code == 200 and len(resp.content) > 100:
            return self.load_from_uploaded_bytes(f"google_sheet_{sheet_id}.xlsx", resp.content)

        # Fallback to single sheet CSV export
        csv_export_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"
        resp_csv = requests.get(csv_export_url, timeout=15)
        if resp_csv.status_code == 200:
            return self.load_from_uploaded_bytes(f"google_sheet_{sheet_id}.csv", resp_csv.content)

        raise ValueError(
            "Không thể truy cập Google Sheet. Vui lòng đảm bảo quyền chia sẻ là 'Bất kỳ ai có đường liên kết đều có thể xem'."
        )

    def _apply_dataframe(self, df: pd.DataFrame, sheet_hint: str = "") -> str:
        cols = [str(c).strip().lower() for c in df.columns]
        hint = sheet_hint.lower()

        if "noi_dung_yeu_cau" in cols or "ma_yeu_cau" in cols or "yeucau" in hint or "request" in hint:
            self.df_requests = self._normalize_requests_df(df)
            return "Danh sách Yêu cầu Khách hàng"
        elif "don_gia_niem_yet" in cols or "ton_kha_dung" in cols or "ma_sp" in cols or "sanpham" in hint:
            self.df_products = df.copy()
            return "Danh mục Sản phẩm & Tồn kho"
        elif "cap_phe_duyet" in cols or "ma_chinh_sach" in cols or "chinhsach" in hint:
            self.df_policies = df.copy()
            return "Chính sách Chiết khấu & Phê duyệt"
        elif "ma_nvkd" in cols or "chuyen_mon" in cols or "nvkd" in hint:
            self.df_reps = df.copy()
            return "Danh sách Nhân viên Kinh doanh"
        else:
            # Treat generic text table as customer requests if it has any text column
            self.df_requests = self._normalize_requests_df(df)
            return "Danh sách Yêu cầu Khách hàng (Tự động nhận diện)"

    def _normalize_requests_df(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        col_map = {}
        for c in df.columns:
            cl = str(c).strip().lower()
            if cl in ["mã yêu cầu", "ma_yeu_cau", "id", "request_id"]:
                col_map[c] = "ma_yeu_cau"
            elif cl in ["ngày nhận", "ngay_nhan", "date", "created_at"]:
                col_map[c] = "ngay_nhan"
            elif cl in ["kênh", "kênh tiếp nhận", "kenh_tiep_nhan", "channel", "source"]:
                col_map[c] = "kenh_tiep_nhan"
            elif cl in ["tên khách hàng", "khách hàng", "ten_khach_hang", "customer", "company"]:
                col_map[c] = "ten_khach_hang"
            elif cl in ["người liên hệ", "nguoi_lien_he", "contact"]:
                col_map[c] = "nguoi_lien_he"
            elif cl in ["email", "email_kh"]:
                col_map[c] = "email_kh"
            elif cl in ["nội dung", "nội dung yêu cầu", "noi_dung_yeu_cau", "yeu_cau", "content", "description"]:
                col_map[c] = "noi_dung_yeu_cau"
            elif cl in ["ngân sách", "ngan_sach_vnd", "ngan_sach", "budget"]:
                col_map[c] = "ngan_sach_vnd"
            elif cl in ["thời hạn", "thời hạn triển khai", "thoi_han_yeu_cau_ngay", "deadline", "lead_time"]:
                col_map[c] = "thoi_han_yeu_cau_ngay"
            elif cl in ["chiết khấu", "đề nghị chiết khấu", "de_nghi_chiet_khau_pct", "discount"]:
                col_map[c] = "de_nghi_chiet_khau_pct"

        df = df.rename(columns=col_map)

        for idx in range(len(df)):
            if "ma_yeu_cau" not in df.columns or pd.isna(df.loc[idx, "ma_yeu_cau"]):
                df.loc[idx, "ma_yeu_cau"] = f"YC-2026-{idx + 1:03d}"
        if "ngay_nhan" not in df.columns:
            df["ngay_nhan"] = datetime.now().strftime("%Y-%m-%d %H:%M")
        if "kenh_tiep_nhan" not in df.columns:
            df["kenh_tiep_nhan"] = "Email / File Upload"
        if "ten_khach_hang" not in df.columns:
            df["ten_khach_hang"] = "Khách hàng Doanh nghiệp"
        if "nguoi_lien_he" not in df.columns:
            df["nguoi_lien_he"] = "Đại diện Mua hàng"
        if "email_kh" not in df.columns:
            df["email_kh"] = "contact@khachhang.vn"
        if "noi_dung_yeu_cau" not in df.columns:
            # Join all columns as text if content column wasn't explicitly named
            df["noi_dung_yeu_cau"] = df.astype(str).agg(" | ".join, axis=1)
        if "ngan_sach_vnd" not in df.columns:
            df["ngan_sach_vnd"] = 0
        if "thoi_han_yeu_cau_ngay" not in df.columns:
            df["thoi_han_yeu_cau_ngay"] = 0
        if "de_nghi_chiet_khau_pct" not in df.columns:
            df["de_nghi_chiet_khau_pct"] = 0.0

        df["ngan_sach_vnd"] = pd.to_numeric(df["ngan_sach_vnd"], errors="coerce").fillna(0)
        df["thoi_han_yeu_cau_ngay"] = pd.to_numeric(df["thoi_han_yeu_cau_ngay"], errors="coerce").fillna(0)
        df["de_nghi_chiet_khau_pct"] = pd.to_numeric(df["de_nghi_chiet_khau_pct"], errors="coerce").fillna(0.0)
        return df

    # -------------------------------------------------------------------------
    # NLP EXTRACTION FROM VIETNAMESE B2B CUSTOMER REQUEST TEXT
    # -------------------------------------------------------------------------
    def extract_items_and_params_from_text(
        self, text: str, given_budget: float = 0, given_deadline: int = 0, given_discount: float = 0.0
    ) -> Dict[str, Any]:
        text_lower = text.lower()

        # 1. Extract products & quantities from natural Vietnamese text
        extracted_items = []
        ambiguous_qty_items = []

        # Patterns for each product in catalog
        for _, prod in self.df_products.iterrows():
            ma_sp = prod["ma_sp"]
            keywords = [k.strip().lower() for k in str(prod["tu_khoa"]).split(",") if k.strip()]
            matched_kw = None
            match_pos = -1

            for kw in sorted(keywords, key=len, reverse=True):
                pos = text_lower.find(kw)
                if pos != -1:
                    matched_kw = kw
                    match_pos = pos
                    break

            if matched_kw is not None:
                # Look in the window before match_pos (up to 45 chars) and after match_pos (up to 35 chars) for quantity
                prefix = text_lower[max(0, match_pos - 45) : match_pos]
                suffix = text_lower[match_pos : min(len(text_lower), match_pos + len(matched_kw) + 35)]

                qty = None
                # Check if vague quantifier is directly before keyword
                vague_match = re.search(r"(một số|vài|nhiều|các|hệ thống)\s+[^0-9]*$", prefix)

                # Look for explicit number + unit before the keyword, e.g., "02 bộ", "15 chiếc", "01 gói", "khoảng 25 bộ"
                num_before = re.findall(
                    r"(\d+)\s*(?:bộ|chiếc|cái|gói|máy|thiết bị|license|bản|he thong|hệ thống)?\s*[^0-9,.;:]{0,25}$",
                    prefix,
                )
                if num_before:
                    candidate = int(num_before[-1])
                    if 0 < candidate < 5000:
                        qty = candidate

                if qty is None:
                    # Check suffix like "số lượng: 5" or "x 4 bộ"
                    num_after = re.search(r"(?:số lượng|sl|x|gồm)\s*[:=]?\s*(\d+)", suffix)
                    if num_after:
                        qty = int(num_after.group(1))

                if qty is None or (vague_match and not num_before):
                    extracted_items.append(
                        {
                            "ma_sp": ma_sp,
                            "ten_sp": prod["ten_sp"],
                            "nhom_sp": prod["nhom_sp"],
                            "don_vi": prod["don_vi"],
                            "so_luong": 0,
                            "ro_so_luong": False,
                            "tu_khoa_khop": matched_kw,
                            "prod_row": prod.to_dict(),
                        }
                    )
                    ambiguous_qty_items.append(prod["ten_sp"])
                else:
                    extracted_items.append(
                        {
                            "ma_sp": ma_sp,
                            "ten_sp": prod["ten_sp"],
                            "nhom_sp": prod["nhom_sp"],
                            "don_vi": prod["don_vi"],
                            "so_luong": qty,
                            "ro_so_luong": True,
                            "tu_khoa_khop": matched_kw,
                            "prod_row": prod.to_dict(),
                        }
                    )

        # 2. Extract Budget if not explicitly passed or 0
        budget = float(given_budget or 0)
        if budget <= 0:
            # Match patterns like "520.000.000 VNĐ", "1.250.000.000", "450 triệu", "1,25 tỷ"
            m_full = re.search(r"(\d{1,3}(?:[.,]\d{3}){2,3})\s*(?:vnđ|vnd|đồng|đ)?", text_lower)
            if m_full:
                raw_num = re.sub(r"[.,]", "", m_full.group(1))
                budget = float(raw_num)
            else:
                m_ty = re.search(r"(\d+(?:[.,]\d+)?)\s*tỷ", text_lower)
                m_tr = re.search(r"(\d+(?:[.,]\d+)?)\s*triệu", text_lower)
                if m_ty:
                    budget = float(m_ty.group(1).replace(",", ".")) * 1_000_000_000
                elif m_tr:
                    budget = float(m_tr.group(1).replace(",", ".")) * 1_000_000

        # 3. Extract Deadline (days) if not explicitly passed or 0
        deadline = int(given_deadline or 0)
        if deadline <= 0:
            m_days = re.search(r"(?:trong vòng|trong|thời hạn|bàn giao|giao hàng)[^0-9]{0,25}(\d+)\s*ngày", text_lower)
            if m_days:
                deadline = int(m_days.group(1))
            else:
                m_weeks = re.search(r"(?:trong vòng|trong|thời hạn)[^0-9]{0,25}(\d+)\s*tuần", text_lower)
                if m_weeks:
                    deadline = int(m_weeks.group(1)) * 7

        # 4. Extract Discount % if not explicitly passed or 0
        discount = float(given_discount or 0.0)
        if discount <= 0:
            m_disc = re.search(r"chiết khấu[^0-9]{0,25}(\d+(?:[.,]\d+)?)\s*%", text_lower)
            if m_disc:
                discount = float(m_disc.group(1).replace(",", "."))

        # 5. Check if customer mentions outdated quote / old price
        mentions_old_price = any(
            phrase in text_lower
            for phrase in ["báo giá cũ", "giá cũ", "năm ngoái", "đợt trước", "giá năm trước"]
        )

        return {
            "extracted_items": extracted_items,
            "ambiguous_qty_items": ambiguous_qty_items,
            "budget": budget,
            "deadline": deadline,
            "discount": discount,
            "mentions_old_price": mentions_old_price,
        }

    # -------------------------------------------------------------------------
    # ASSIGN BEST SALES REP (NVKD)
    # -------------------------------------------------------------------------
    def select_sales_rep(self, req_row: Dict[str, Any], extracted_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        hint_id = str(req_row.get("nvkd_phu_trach_goi_y", "")).strip()
        if hint_id:
            matched = self.df_reps[self.df_reps["ma_nvkd"] == hint_id]
            if not matched.empty:
                return matched.iloc[0].to_dict()

        # Match by category specialization and lowest workload
        categories = {item["nhom_sp"] for item in extracted_items}
        best_rep = None
        best_score = -999
        for _, rep in self.df_reps.iterrows():
            score = -int(rep.get("so_co_hoi_dang_xu_ly", 10))
            chuyen_mon = str(rep.get("chuyen_mon", "")).lower()
            for cat in categories:
                if any(w in chuyen_mon for w in cat.lower().split()):
                    score += 15
            if score > best_score:
                best_score = score
                best_rep = rep.to_dict()

        return best_rep or self.df_reps.iloc[0].to_dict()

    # -------------------------------------------------------------------------
    # FULL WORKFLOW EXECUTION FOR A SINGLE REQUEST
    # -------------------------------------------------------------------------
    def process_request(
        self,
        req_row: Dict[str, Any],
        llm_config: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        ma_yc = str(req_row.get("ma_yeu_cau", "YC-2026-NEW"))
        ten_kh = str(req_row.get("ten_khach_hang", "Khách hàng Doanh nghiệp"))
        nguoi_lh = str(req_row.get("nguoi_lien_he", "Quý Khách hàng"))
        email_kh = str(req_row.get("email_kh", "contact@company.vn"))
        kenh = str(req_row.get("kenh_tiep_nhan", "Email"))
        ngay_nhan = str(req_row.get("ngay_nhan", datetime.now().strftime("%Y-%m-%d %H:%M")))
        noi_dung = str(req_row.get("noi_dung_yeu_cau", ""))

        parsed = self.extract_items_and_params_from_text(
            noi_dung,
            given_budget=req_row.get("ngan_sach_vnd", 0),
            given_deadline=req_row.get("thoi_han_yeu_cau_ngay", 0),
            given_discount=req_row.get("de_nghi_chiet_khau_pct", 0.0),
        )

        items = parsed["extracted_items"]
        ambiguous_items = parsed["ambiguous_qty_items"]
        budget = parsed["budget"]
        deadline = parsed["deadline"]
        req_discount = parsed["discount"]
        mentions_old_price = parsed["mentions_old_price"]

        # Assign NVKD immediately so NO request is ever left without an owner
        assigned_rep = self.select_sales_rep(req_row, items)
        opp_id = ma_yc.replace("YC-", "HSCH-") if "YC-" in ma_yc else f"HSCH-{ma_yc}"

        # Check Information Completeness (Decision Node 1: "Có đủ thông tin?")
        missing_reasons = []
        if len(items) == 0:
            missing_reasons.append("Chưa xác định được danh mục sản phẩm/dịch vụ cụ thể trong yêu cầu.")
        if len(ambiguous_items) > 0:
            missing_reasons.append(
                f"Chưa rõ số lượng cụ thể cho {len(ambiguous_items)} hạng mục: {', '.join(ambiguous_items)}."
            )
        if budget <= 0:
            missing_reasons.append("Khách hàng chưa cung cấp Ngân sách tổng dự kiến.")
        if deadline <= 0:
            missing_reasons.append("Khách hàng chưa xác định Thời hạn triển khai / bàn giao mong muốn.")

        is_info_complete = len(missing_reasons) == 0

        # Evaluate Line Items (Inventory, Latest Price vs Old Price, Lead Time)
        line_items_detail = []
        tong_niem_yet = 0.0
        tong_gia_cu = 0.0
        max_lead_time_days = 0
        max_ready_days = 0
        shortage_items = []
        max_nv_discount_weighted = 0.0
        max_tp_discount_weighted = 0.0

        for idx, it in enumerate(items, start=1):
            p = it["prod_row"]
            qty = it["so_luong"] if it["ro_so_luong"] else 1  # Provisional qty=1 for reference if missing
            don_gia = float(p["don_gia_niem_yet"])
            gia_cu = float(p.get("gia_cu_tham_chieu", don_gia))
            ton_kho = int(p["ton_kha_dung"])
            tg_san = int(p["tg_trien_khai_co_san_ngay"])
            tg_nhap = int(p["tg_nhap_them_ngay"])

            thanh_tien = don_gia * qty if it["ro_so_luong"] else 0.0
            thanh_tien_cu = gia_cu * qty if it["ro_so_luong"] else 0.0

            du_ton = (qty <= ton_kho) if it["ro_so_luong"] else True
            so_luong_thieu = max(0, qty - ton_kho) if it["ro_so_luong"] else 0
            tg_dap_ung = tg_san if du_ton else tg_nhap

            if it["ro_so_luong"]:
                tong_niem_yet += thanh_tien
                tong_gia_cu += thanh_tien_cu
                max_lead_time_days = max(max_lead_time_days, tg_dap_ung)
                max_ready_days = max(max_ready_days, tg_san)
                max_nv_discount_weighted += thanh_tien * float(p.get("chiet_khau_nv_toi_da_pct", 5.0))
                max_tp_discount_weighted += thanh_tien * float(p.get("chiet_khau_tp_toi_da_pct", 10.0))

            if not du_ton and it["ro_so_luong"]:
                shortage_items.append(
                    f"{it['ten_sp']} (Yêu cầu: {qty} {it['don_vi']}, Tồn khả dụng: {ton_kho} {it['don_vi']}, Thiếu: {so_luong_thieu} {it['don_vi']} - Cần {tg_nhap} ngày nhập hàng)"
                )

            line_items_detail.append(
                {
                    "stt": idx,
                    "ma_sp": it["ma_sp"],
                    "ten_sp": it["ten_sp"],
                    "nhom_sp": it["nhom_sp"],
                    "don_vi": it["don_vi"],
                    "so_luong": it["so_luong"] if it["ro_so_luong"] else "Chưa rõ (Tạm tính 1)",
                    "ro_so_luong": it["ro_so_luong"],
                    "don_gia_niem_yet": don_gia,
                    "gia_cu_tham_chieu": gia_cu,
                    "thanh_tien": thanh_tien,
                    "ton_kha_dung": ton_kho,
                    "du_ton_kho": du_ton,
                    "so_luong_thieu": so_luong_thieu,
                    "tg_dap_ung_ngay": tg_dap_ung,
                    "tg_co_san_ngay": tg_san,
                    "bao_hanh": p.get("bao_hanh", "24 tháng"),
                }
            )

        avg_nv_max_disc = round(max_nv_discount_weighted / tong_niem_yet, 1) if tong_niem_yet > 0 else 5.0
        avg_tp_max_disc = round(max_tp_discount_weighted / tong_niem_yet, 1) if tong_niem_yet > 0 else 10.0

        # Discount & Pricing Calculation
        applied_discount_pct = req_discount if req_discount > 0 else min(3.0, avg_nv_max_disc)
        tien_chiet_khau = round(tong_niem_yet * (applied_discount_pct / 100.0))
        tong_sau_chiet_khau = tong_niem_yet - tien_chiet_khau

        # Standard NVKD ceiling quote (for comparison when customer asks for excessive discount)
        tien_ck_chuan_nvkd = round(tong_niem_yet * (5.0 / 100.0))
        tong_theo_chuan_nvkd = tong_niem_yet - tien_ck_chuan_nvkd

        # Budget & Deadline Evaluation
        budget_diff = budget - tong_sau_chiet_khau if (budget > 0 and tong_sau_chiet_khau > 0) else 0.0
        is_within_budget = (budget_diff >= 0) if (budget > 0 and tong_sau_chiet_khau > 0) else False
        discount_needed_for_budget = 0.0
        if budget > 0 and tong_niem_yet > budget:
            discount_needed_for_budget = round(((tong_niem_yet - budget) / tong_niem_yet) * 100.0, 2)

        is_deadline_met = (max_lead_time_days <= deadline) if (deadline > 0 and max_lead_time_days > 0) else False
        deadline_gap_days = max(0, max_lead_time_days - deadline) if deadline > 0 else 0

        # Decision Node 2: "Có vượt thẩm quyền / Cần chiết khấu đặc biệt?"
        escalation_reasons = []
        approval_level = "Nhân viên Kinh doanh (NVKD)"
        approver_name = f"{assigned_rep['ho_ten']} ({assigned_rep['ma_nvkd']}) - Tự quyết trong hạn mức"
        policy_code = "CS-01"
        sla_hours = 2
        requires_manager_approval = False

        if is_info_complete:
            # Check order value & discount against policies
            if tong_niem_yet > 1_000_000_000 or req_discount > 10.0:
                requires_manager_approval = True
                approval_level = "Ban Giám đốc (Phó TGĐ Phụ trách KD)"
                approver_name = "Bà Nguyễn Minh An - Phó TGĐ Phụ trách KD (Đồng duyệt: Ông Trần Quốc Tuấn - TP.KD)"
                policy_code = "CS-03"
                sla_hours = 8
                if tong_niem_yet > 1_000_000_000:
                    escalation_reasons.append(
                        f"Tổng giá trị đơn hàng niêm yết ({format_vnd(tong_niem_yet)}) vượt ngưỡng 1 tỷ VNĐ."
                    )
                if req_discount > 10.0:
                    escalation_reasons.append(
                        f"Khách hàng đề nghị chiết khấu đặc biệt ({req_discount}%) vượt trần Trưởng phòng KD (10%)."
                    )
            elif (
                tong_niem_yet > 300_000_000
                or req_discount > 5.0
                or len(shortage_items) > 0
                or not is_deadline_met
                or not is_within_budget
            ):
                requires_manager_approval = True
                approval_level = "Trưởng phòng Kinh doanh"
                approver_name = "Ông Trần Quốc Tuấn - Trưởng phòng Kinh doanh"
                policy_code = "CS-02"
                sla_hours = 4
                if tong_niem_yet > 300_000_000:
                    escalation_reasons.append(
                        f"Giá trị đơn hàng ({format_vnd(tong_niem_yet)}) vượt hạn mức tự duyệt 300 triệu VNĐ của NVKD."
                    )
                if req_discount > 5.0:
                    escalation_reasons.append(
                        f"Mức chiết khấu đề nghị ({req_discount}%) vượt trần tự quyết của NVKD (5%)."
                    )

            if len(shortage_items) > 0:
                escalation_reasons.append(
                    f"Cần phê duyệt phương án điều phối kho / giao hàng 2 đợt do thiếu tồn kho khả dụng ({len(shortage_items)} hạng mục)."
                )
            if not is_deadline_met and deadline > 0:
                escalation_reasons.append(
                    f"Thời gian đáp ứng thực tế ({max_lead_time_days} ngày) vượt thời hạn khách yêu cầu ({deadline} ngày) -> Không được tự ý hứa hẹn."
                )
            if not is_within_budget and budget > 0:
                escalation_reasons.append(
                    f"Giá trị sau chiết khấu ({format_vnd(tong_sau_chiet_khau)}) vượt ngân sách khách hàng ({format_vnd(budget)}) là {format_vnd(abs(budget_diff))}."
                )
        else:
            # Incomplete request -> Routed to Clarification Loop, tracked by assigned NVKD + supervised by TP.KD if high budget
            approval_level = "Chưa trình duyệt báo giá (Chờ KH làm rõ thông tin)"
            approver_name = f"Theo dõi chính: {assigned_rep['ho_ten']} ({assigned_rep['ma_nvkd']}) | Giám sát SLA: Ông Trần Quốc Tuấn (TP.KD)"
            policy_code = "QUY-TRINH-BO-SUNG"
            sla_hours = 2

        # Build Visual Workflow Step Statuses (matching the 7 boxes in the user's image)
        workflow_steps = [
            {
                "step_id": 1,
                "name": "Bắt đầu: Tiếp nhận yêu cầu",
                "status": "completed",
                "badge": "Hoàn tất",
                "detail": f"Tiếp nhận từ {kenh} lúc {ngay_nhan} ({ma_yc})",
            },
            {
                "step_id": 2,
                "name": "Phân loại & Kiểm tra thông tin",
                "status": "completed" if is_info_complete else "warning",
                "badge": "Đủ thông tin" if is_info_complete else "Thiếu thông tin",
                "detail": (
                    f"Đã bóc tách {len(items)} hạng mục, Ngân sách {format_vnd(budget)}, Tiến độ {deadline} ngày"
                    if is_info_complete
                    else f"Phát hiện {len(missing_reasons)} thông tin chưa rõ cần hỏi lại KH"
                ),
            },
            {
                "step_id": 3,
                "name": "Yêu cầu KH làm rõ / bổ sung",
                "status": "active_branch" if not is_info_complete else "skipped",
                "badge": "Kích hoạt nhánh hỏi lại KH" if not is_info_complete else "Bỏ qua (Đã đủ TT)",
                "detail": (
                    "Tự động tạo bản nháp Email hỏi lại KH + Gắn NVKD theo dõi tránh thất lạc"
                    if not is_info_complete
                    else "Thông tin đã đầy đủ, chuyển thẳng sang tạo Hồ sơ Cơ hội"
                ),
            },
            {
                "step_id": 4,
                "name": "Tạo Hồ sơ Cơ hội & Gắn người phụ trách",
                "status": "completed" if is_info_complete else "in_progress",
                "badge": opp_id,
                "detail": f"Phụ trách: {assigned_rep['ho_ten']} ({assigned_rep['ma_nvkd']}) - {assigned_rep['chuyen_mon']}",
            },
            {
                "step_id": 5,
                "name": "Thẩm định tồn kho & giá (NVKD & Vận hành)",
                "status": (
                    "completed"
                    if (is_info_complete and len(shortage_items) == 0 and is_deadline_met)
                    else ("warning" if is_info_complete else "pending")
                ),
                "badge": (
                    "Đủ tồn & Kịp tiến độ"
                    if (is_info_complete and len(shortage_items) == 0 and is_deadline_met)
                    else ("Cảnh báo Tồn/Tiến độ" if is_info_complete else "Tra cứu giá tham khảo")
                ),
                "detail": (
                    f"Áp dụng bảng giá mới nhất 2026. Tồn kho: {len(items) - len(shortage_items)}/{len(items)} đủ hàng. Thời gian cần: {max_lead_time_days} ngày."
                ),
            },
            {
                "step_id": 6,
                "name": "Lập Báo giá & Kiểm tra Thẩm quyền",
                "status": (
                    "warning"
                    if (is_info_complete and requires_manager_approval)
                    else ("completed" if is_info_complete else "pending")
                ),
                "badge": (
                    "Cần Trưởng phòng / BGĐ duyệt"
                    if (is_info_complete and requires_manager_approval)
                    else ("Trong thẩm quyền NVKD" if is_info_complete else "Báo giá sơ bộ")
                ),
                "detail": (
                    f"Chính sách {policy_code}: {approval_level}"
                    if is_info_complete
                    else "Gửi đơn giá niêm yết tham khảo kèm câu hỏi làm rõ"
                ),
            },
            {
                "step_id": 7,
                "name": "Kết thúc: Cập nhật & Theo dõi",
                "status": "completed",
                "badge": f"SLA theo dõi: {sla_hours}h",
                "detail": (
                    f"Trạng thái: {'Chờ ' + approval_level + ' phê duyệt' if requires_manager_approval else 'Sẵn sàng gửi báo giá chính thức'}"
                    if is_info_complete
                    else f"Trạng thái: Chờ KH phản hồi bổ sung (NVKD {assigned_rep['ho_ten']} theo dõi)"
                ),
            },
        ]

        # Quality Guardrails Audit (Preventing the 4 historical errors at Minh An)
        guardrails = [
            {
                "tieu_chi": "Chống bỏ sót hạng mục",
                "trang_thai": "ĐẠT (100%)" if len(items) > 0 else "CẦN KIỂM TRA",
                "mo_ta": f"Đã đối chiếu đầy đủ {len(items)}/{len(items)} hạng mục thiết bị & dịch vụ khách hàng đề cập trong văn bản.",
                "loai": "success" if len(items) > 0 else "warning",
            },
            {
                "tieu_chi": "Chống dùng bảng giá cũ",
                "trang_thai": "CẢNH BÁO GIÁ CŨ" if mentions_old_price else "ĐẠT (Giá mới 2026)",
                "mo_ta": (
                    f"Khách hàng đang tham chiếu báo giá cũ ({format_vnd(tong_gia_cu)}). Hệ thống đã tự động khóa đơn giá niêm yết mới nhất ({format_vnd(tong_niem_yet)}), chênh lệch +{format_vnd(tong_niem_yet - tong_gia_cu)}."
                    if mentions_old_price
                    else f"Toàn bộ {len(items)} hạng mục đều áp dụng bảng giá chuẩn hiện hành (tiết kiệm rủi ro thất thoát {format_vnd(max(0, tong_niem_yet - tong_gia_cu))} so với giá cũ)."
                ),
                "loai": "warning" if mentions_old_price else "success",
            },
            {
                "tieu_chi": "Kiểm soát cam kết tiến độ & tồn kho",
                "trang_thai": (
                    "ĐỦ TỒN & KỊP HẠN"
                    if (is_info_complete and len(shortage_items) == 0 and is_deadline_met)
                    else ("RỦI RO TRỄ HẠN / THIẾU TỒN" if is_info_complete else "CHỜ XÁC NHẬN SL & TIẾN ĐỘ")
                ),
                "mo_ta": (
                    f"Tất cả hạng mục có sẵn trong kho, triển khai hoàn tất trong {max_lead_time_days} ngày (sớm hơn yêu cầu {deadline} ngày)."
                    if (is_info_complete and len(shortage_items) == 0 and is_deadline_met)
                    else (
                        f"Cần {max_lead_time_days} ngày (KH yêu cầu {deadline} ngày). Chặn cam kết sai, đề xuất giao 2 đợt: Đợt 1 hàng có sẵn trong {max_ready_days} ngày, Đợt 2 sau {max_lead_time_days} ngày."
                        if is_info_complete
                        else "Chưa cam kết ngày bàn giao cố định cho đến khi khách hàng chốt số lượng và thời hạn mong muốn."
                    )
                ),
                "loai": (
                    "success"
                    if (is_info_complete and len(shortage_items) == 0 and is_deadline_met)
                    else "danger" if (is_info_complete and (len(shortage_items) > 0 or not is_deadline_met)) else "warning"
                ),
            },
            {
                "tieu_chi": "Kiểm soát người phụ trách & người duyệt",
                "trang_thai": "ĐÃ GẮN CHỦ SỞ HỮU",
                "mo_ta": f"Owner: {assigned_rep['ho_ten']} ({assigned_rep['ma_nvkd']}) | Cấp duyệt: {approver_name} (Cam kết xử lý trong {sla_hours}h).",
                "loai": "success",
            },
        ]

        # Build Business Recommendations & Customer Draft Response
        recommendations = self._build_business_recommendations(
            is_info_complete=is_info_complete,
            missing_reasons=missing_reasons,
            shortage_items=shortage_items,
            is_deadline_met=is_deadline_met,
            deadline=deadline,
            max_lead_time_days=max_lead_time_days,
            max_ready_days=max_ready_days,
            is_within_budget=is_within_budget,
            budget=budget,
            tong_niem_yet=tong_niem_yet,
            tong_sau_chiet_khau=tong_sau_chiet_khau,
            budget_diff=budget_diff,
            req_discount=req_discount,
            discount_needed_for_budget=discount_needed_for_budget,
            mentions_old_price=mentions_old_price,
            tong_gia_cu=tong_gia_cu,
            requires_manager_approval=requires_manager_approval,
            approval_level=approval_level,
            approver_name=approver_name,
            assigned_rep=assigned_rep,
        )

        draft_email = self._build_customer_draft(
            ma_yc=ma_yc,
            opp_id=opp_id,
            ten_kh=ten_kh,
            nguoi_lh=nguoi_lh,
            email_kh=email_kh,
            is_info_complete=is_info_complete,
            missing_reasons=missing_reasons,
            line_items=line_items_detail,
            tong_niem_yet=tong_niem_yet,
            applied_discount_pct=applied_discount_pct,
            tien_chiet_khau=tien_chiet_khau,
            tong_sau_chiet_khau=tong_sau_chiet_khau,
            budget=budget,
            is_within_budget=is_within_budget,
            deadline=deadline,
            is_deadline_met=is_deadline_met,
            max_lead_time_days=max_lead_time_days,
            max_ready_days=max_ready_days,
            shortage_items=shortage_items,
            requires_manager_approval=requires_manager_approval,
            approval_level=approval_level,
            assigned_rep=assigned_rep,
            mentions_old_price=mentions_old_price,
        )

        # Optional LLM enhancement if API key is provided
        llm_insight = None
        if llm_config and llm_config.get("api_key"):
            llm_insight = self._call_optional_llm(
                llm_config=llm_config,
                req_row=req_row,
                line_items=line_items_detail,
                recommendations=recommendations,
                draft_email=draft_email,
            )
            if llm_insight and llm_insight.get("enhanced_draft"):
                draft_email = llm_insight["enhanced_draft"]
            if llm_insight and llm_insight.get("extra_recommendations"):
                recommendations.extend(llm_insight["extra_recommendations"])

        # Overall Final Status Tag for Dashboard Table
        if not is_info_complete:
            final_status = "Cần KH làm rõ / bổ sung"
            status_color = "amber"
        elif requires_manager_approval:
            final_status = f"Chờ {approval_level} duyệt"
            status_color = "purple"
        else:
            final_status = "Đủ ĐK - Sẵn sàng gửi Báo giá"
            status_color = "emerald"

        return {
            "ma_yeu_cau": ma_yc,
            "ma_ho_so_co_hoi": opp_id,
            "ngay_nhan": ngay_nhan,
            "kenh_tiep_nhan": kenh,
            "ten_khach_hang": ten_kh,
            "nguoi_lien_he": nguoi_lh,
            "email_kh": email_kh,
            "noi_dung_yeu_cau": noi_dung,
            "is_info_complete": is_info_complete,
            "missing_reasons": missing_reasons,
            "final_status": final_status,
            "status_color": status_color,
            "assigned_rep": assigned_rep,
            "approval": {
                "requires_manager_approval": requires_manager_approval,
                "approval_level": approval_level,
                "approver_name": approver_name,
                "policy_code": policy_code,
                "sla_hours": sla_hours,
                "escalation_reasons": escalation_reasons,
            },
            "financials": {
                "ngan_sach_khach_hang": budget,
                "tong_gia_niem_yet": tong_niem_yet,
                "tong_gia_cu_tham_chieu": tong_gia_cu,
                "de_nghi_chiet_khau_pct": req_discount,
                "ap_dung_chiet_khau_pct": applied_discount_pct,
                "tien_chiet_khau": tien_chiet_khau,
                "tong_sau_chiet_khau": tong_sau_chiet_khau,
                "tong_theo_chuan_nvkd": tong_theo_chuan_nvkd,
                "chenh_lech_ngan_sach": budget_diff,
                "is_within_budget": is_within_budget,
                "discount_needed_for_budget": discount_needed_for_budget,
                "mentions_old_price": mentions_old_price,
            },
            "operations": {
                "thoi_han_khach_yeu_cau_ngay": deadline,
                "thoi_gian_dap_ung_thuc_te_ngay": max_lead_time_days,
                "thoi_gian_giao_dot_1_co_san_ngay": max_ready_days,
                "is_deadline_met": is_deadline_met,
                "deadline_gap_days": deadline_gap_days,
                "so_hang_muc": len(line_items_detail),
                "so_hang_muc_thieu_ton": len(shortage_items),
                "shortage_items": shortage_items,
            },
            "line_items": line_items_detail,
            "workflow_steps": workflow_steps,
            "guardrails": guardrails,
            "recommendations": recommendations,
            "draft_email": draft_email,
            "llm_used": bool(llm_insight),
        }

    def _build_business_recommendations(
        self,
        is_info_complete: bool,
        missing_reasons: List[str],
        shortage_items: List[str],
        is_deadline_met: bool,
        deadline: int,
        max_lead_time_days: int,
        max_ready_days: int,
        is_within_budget: bool,
        budget: float,
        tong_niem_yet: float,
        tong_sau_chiet_khau: float,
        budget_diff: float,
        req_discount: float,
        discount_needed_for_budget: float,
        mentions_old_price: bool,
        tong_gia_cu: float,
        requires_manager_approval: bool,
        approval_level: str,
        approver_name: str,
        assigned_rep: Dict[str, Any],
    ) -> List[Dict[str, str]]:
        recs = []

        if not is_info_complete:
            recs.append(
                {
                    "nhom": "Quy trình Làm rõ Thông tin (Tránh bỏ trôi yêu cầu)",
                    "muc_do": "Khẩn cấp (SLA 2 giờ)",
                    "noi_dung": (
                        f"Giao NVKD {assigned_rep['ho_ten']} ({assigned_rep['ma_nvkd']}) gửi ngay bản nháp yêu cầu bổ sung thông tin ({'; '.join(missing_reasons)}) "
                        "kèm Bảng đơn giá niêm yết tham khảo để giữ nhiệt khách hàng. Hệ thống khóa trạng thái 'Chờ KH phản hồi' và nhắc lịch sau 24h."
                    ),
                }
            )
            return recs

        # 1. Pricing & Old Price Recommendation
        if mentions_old_price:
            recs.append(
                {
                    "nhom": "Xử lý Chênh lệch Bảng giá Cũ vs Mới",
                    "muc_do": "Quan trọng",
                    "noi_dung": (
                        f"Khách hàng đang tính ngân sách theo bảng giá cũ ({format_vnd(tong_gia_cu)}), thấp hơn giá niêm yết 2026 ({format_vnd(tong_niem_yet)}) là {format_vnd(tong_niem_yet - tong_gia_cu)}. "
                        "NVKD cần giải thích rõ cấu hình/chính sách bảo hành nâng cấp của dòng sản phẩm mới và tuyệt đối không tự ý áp giá cũ."
                    ),
                }
            )

        # 2. Budget & Discount Strategy
        if not is_within_budget and budget > 0:
            recs.append(
                {
                    "nhom": "Phương án Cân đối Ngân sách & Chiết khấu",
                    "muc_do": "Cần quyết định",
                    "noi_dung": (
                        f"Giá sau chiết khấu đề nghị ({req_discount}% -> {format_vnd(tong_sau_chiet_khau)}) vẫn vượt ngân sách khách hàng ({format_vnd(budget)}) là {format_vnd(abs(budget_diff))}. "
                        f"Để khớp đúng ngân sách {format_vnd(budget)}, mức chiết khấu cần tới {discount_needed_for_budget}% (vượt trần cho phép). "
                        "Đề xuất 2 phương án cho Khách hàng: (Phương án A) Giữ nguyên cấu hình với mức chiết khấu tối đa được duyệt và đề nghị KH bổ sung ngân sách; "
                        "(Phương án B) Tối ưu giảm số lượng thiết bị giai đoạn 1 hoặc tách gói Dịch vụ bảo trì sang kỳ ngân sách tiếp theo."
                    ),
                }
            )
        else:
            recs.append(
                {
                    "nhom": "Đánh giá Hiệu quả Tài chính & Ngân sách",
                    "muc_do": "Tối ưu",
                    "noi_dung": (
                        f"Tổng giá trị sau chiết khấu ({format_vnd(tong_sau_chiet_khau)}) nằm trong ngân sách phê duyệt của khách hàng ({format_vnd(budget)}), "
                        f"còn dư địa ngân sách {format_vnd(budget_diff)}. Khuyến nghị NVKD tư vấn bán chéo (upsell) thêm gói Dịch vụ Bảo trì 24/7 hoặc gia hạn bảo hành."
                    ),
                }
            )

        # 3. Inventory & Lead Time Strategy
        if len(shortage_items) > 0 or not is_deadline_met:
            recs.append(
                {
                    "nhom": "Giải pháp Tồn kho & Tiến độ Triển khai (Chống hứa quá khả năng)",
                    "muc_do": "Cảnh báo Vận hành",
                    "noi_dung": (
                        f"Khách yêu cầu hoàn tất trong {deadline} ngày nhưng có {len(shortage_items)} hạng mục vượt tồn kho khả dụng (cần {max_lead_time_days} ngày để nhập thêm và triển khai). "
                        f"Đề xuất đàm phán **Giao hàng & Triển khai 2 Giai đoạn**: "
                        f"Giai đoạn 1 bàn giao ngay toàn bộ số lượng có sẵn trong kho trong vòng {max_ready_days} ngày để khách hàng kịp vận hành cốt lõi; "
                        f"Giai đoạn 2 bàn giao phần còn lại vào ngày thứ {max_lead_time_days}."
                    ),
                }
            )
        else:
            recs.append(
                {
                    "nhom": "Xác nhận Tồn kho & Lịch Triển khai",
                    "muc_do": "Sẵn sàng",
                    "noi_dung": (
                        f"100% hạng mục đều đủ tồn kho khả dụng tại kho Minh An. Bộ phận Vận hành có thể giữ hàng (lock stock) trong 48h và triển khai hoàn tất trong {max_lead_time_days} ngày "
                        f"(đáp ứng tốt yêu cầu {deadline} ngày của khách hàng)."
                    ),
                }
            )

        # 4. Approval & Escalation Action
        if requires_manager_approval:
            recs.append(
                {
                    "nhom": "Hành động Phê duyệt Nội bộ",
                    "muc_do": f"SLA Duyệt: {approval_level}",
                    "noi_dung": (
                        f"Hồ sơ đã tự động định tuyến đến **{approver_name}**. NVKD {assigned_rep['ho_ten']} cần xác nhận khóa tồn kho tạm thời với Vận hành trước khi gửi báo giá chính thức."
                    ),
                }
            )
        else:
            recs.append(
                {
                    "nhom": "Hành động Phê duyệt Nội bộ",
                    "muc_do": "Tự động duyệt (CS-01)",
                    "noi_dung": (
                        f"Đơn hàng nằm trong hạn mức phê duyệt của NVKD ({assigned_rep['ho_ten']}). Có thể xuất bản nháp báo giá gửi khách hàng ngay trong vòng 2 giờ."
                    ),
                }
            )

        return recs

    def _build_customer_draft(
        self,
        ma_yc: str,
        opp_id: str,
        ten_kh: str,
        nguoi_lh: str,
        email_kh: str,
        is_info_complete: bool,
        missing_reasons: List[str],
        line_items: List[Dict[str, Any]],
        tong_niem_yet: float,
        applied_discount_pct: float,
        tien_chiet_khau: float,
        tong_sau_chiet_khau: float,
        budget: float,
        is_within_budget: bool,
        deadline: int,
        is_deadline_met: bool,
        max_lead_time_days: int,
        max_ready_days: int,
        shortage_items: List[str],
        requires_manager_approval: bool,
        approval_level: str,
        assigned_rep: Dict[str, Any],
        mentions_old_price: bool,
    ) -> str:
        lines_text = []
        for item in line_items:
            qty_str = f"{item['so_luong']} {item['don_vi']}"
            price_str = format_vnd(item["don_gia_niem_yet"])
            total_str = format_vnd(item["thanh_tien"]) if item["ro_so_luong"] else "Tạm tính theo SL thực tế"
            stock_note = (
                f"Có sẵn ({item['tg_co_san_ngay']} ngày)"
                if item["du_ton_kho"]
                else f"Có sẵn {item['ton_kha_dung']} {item['don_vi']} ({item['tg_co_san_ngay']} ngày) | Đặt thêm {item['so_luong_thieu']} {item['don_vi']} ({item['tg_dap_ung_ngay']} ngày)"
            )
            lines_text.append(
                f"  {item['stt']}. [{item['ma_sp']}] {item['ten_sp']}\n"
                f"     - Số lượng: {qty_str} | Đơn giá niêm yết 2026: {price_str} | Thành tiền: {total_str}\n"
                f"     - Tình trạng đáp ứng: {stock_note} | Bảo hành: {item['bao_hanh']}"
            )
        items_block = "\n".join(lines_text) if lines_text else "  (Chưa có danh mục thiết bị cụ thể)"

        if not is_info_complete:
            missing_bullets = "\n".join([f"  - {r}" for r in missing_reasons])
            return (
                f"Tiêu đề: [MINH AN TECH - {opp_id}] Phản hồi yêu cầu báo giá & Đề nghị làm rõ thông tin triển khai - {ten_kh}\n"
                f"Kính gửi: {nguoi_lh} - {ten_kh} ({email_kh})\n\n"
                f"Lời đầu tiên, Công ty Công nghệ Minh An xin chân thành cảm ơn Quý Công ty đã tin tưởng gửi yêu cầu hợp tác ({ma_yc}).\n"
                f"Tôi là {assigned_rep['ho_ten']} ({assigned_rep['chuyen_mon']}), Nhân viên Kinh doanh được phân công phụ trách trực tiếp Hồ sơ Cơ hội {opp_id} của Quý Công ty.\n\n"
                f"Qua rà soát yêu cầu ban đầu, Minh An xin gửi tới Quý Công ty **Bảng đơn giá niêm yết hiện hành (năm 2026)** của các hạng mục thiết bị/dịch vụ đã nhận diện:\n"
                f"{items_block}\n\n"
                f"Để Minh An có thể lập Đề xuất Kỹ thuật - Thương mại chính xác nhất, áp mức chiết khấu tối ưu và cam kết đúng tiến độ bàn giao, kính mong Anh/Chị phản hồi bổ sung giúp chúng tôi một số thông tin sau:\n"
                f"{missing_bullets}\n\n"
                f"Ngay khi nhận được thông tin xác nhận từ Anh/Chị, Minh An cam kết sẽ hoàn thiện Báo giá chính thức kèm lịch biểu triển khai trong vòng 02 giờ làm việc.\n\n"
                f"Trân trọng cảm ơn và mong sớm nhận được phản hồi từ Quý Công ty!\n"
                f"--------------------------------------------------\n"
                f"Người phụ trách hồ sơ: {assigned_rep['ho_ten']} ({assigned_rep['ma_nvkd']})\n"
                f"Email: {assigned_rep['email']} | Công ty Thiết bị & Dịch vụ Công nghệ Minh An"
            )

        # Complete Info -> Full Commercial Proposal & Schedule Commitment Draft
        old_price_note = ""
        if mentions_old_price:
            old_price_note = (
                "\n*Lưu ý về đơn giá:* Bảng giá dưới đây được áp dụng theo Biểu giá chuẩn năm 2026 mới nhất của hãng và Minh An "
                "(đã bao gồm thế hệ phần cứng nâng cấp và gói bảo hành chính hãng tiêu chuẩn mới nhất).\n"
            )

        schedule_clause = (
            f"- **Cam kết Tiến độ Triển khai:** Toàn bộ thiết bị hiện có sẵn 100% tại kho Minh An. "
            f"Chúng tôi cam kết bàn giao, lắp đặt và nghiệm thu hoàn tất trong vòng **{max_lead_time_days} ngày làm việc** "
            f"(đáp ứng hoàn toàn tiến độ {deadline} ngày của Quý Công ty)."
            if is_deadline_met and len(shortage_items) == 0
            else (
                f"- **Phương án Tiến độ & Giao hàng Khả thi (Đề xuất 2 Giai đoạn):** Do yêu cầu tiến độ gấp ({deadline} ngày) "
                f"và một số hạng mục cần nhập bổ sung từ hãng ({len(shortage_items)} hạng mục), để đảm bảo trung thực và không làm ảnh hưởng kế hoạch vận hành của Quý Công ty, Minh An đề xuất:\n"
                f"  + **Giai đoạn 1 (Trong vòng {max_ready_days} ngày):** Bàn giao và kích hoạt ngay toàn bộ số lượng thiết bị đang có sẵn tại kho Minh An để hệ thống đi vào hoạt động.\n"
                f"  + **Giai đoạn 2 (Hoàn tất vào ngày thứ {max_lead_time_days}):** Bàn giao và cấu hình bổ sung phần thiết bị còn lại."
            )
        )

        budget_clause = (
            f"- **Đánh giá Ngân sách:** Tổng giá trị đề xuất sau chiết khấu ({format_vnd(tong_sau_chiet_khau)}) hoàn toàn đáp ứng trong phạm vi ngân sách phê duyệt ({format_vnd(budget)}) của Quý Công ty."
            if is_within_budget
            else (
                f"- **Tối ưu Ngân sách:** Tổng giá trị sau chiết khấu đề nghị ({format_vnd(tong_sau_chiet_khau)}) hiện chênh lệch {format_vnd(abs(budget - tong_sau_chiet_khau))} so với ngân sách dự kiến ({format_vnd(budget)}). "
                f"Minh An sẵn sàng phối hợp cùng Quý Công ty điều chỉnh phân kỳ đầu tư hoặc cấu hình tương đương nếu cần khống chế cứng trong trần ngân sách {format_vnd(budget)}."
            )
        )

        approval_banner = (
            f"[BẢN NHÁP TRÌNH DUYỆT NỘI BỘ - Cần {approval_level} phê duyệt trước khi gửi KH]\n\n"
            if requires_manager_approval
            else "[BẢN NHÁP SẴN SÀNG GỬI KHÁCH HÀNG - Trong thẩm quyền NVKD]\n\n"
        )

        return (
            f"{approval_banner}"
            f"Tiêu đề: [MINH AN TECH - {opp_id}] Đề xuất Kỹ thuật & Báo giá Thương mại - {ten_kh}\n"
            f"Kính gửi: {nguoi_lh} - {ten_kh} ({email_kh})\n\n"
            f"Công ty Công nghệ Minh An xin gửi lời chào trân trọng và cảm ơn Quý Công ty đã gửi yêu cầu báo giá ({ma_yc}).\n"
            f"Dựa trên nhu cầu triển khai thực tế của {ten_kh}, chúng tôi xin trân trọng gửi **Đề xuất Giải pháp & Báo giá Chi tiết (Mã Hồ sơ Cơ hội: {opp_id})** như sau:\n"
            f"{old_price_note}\n"
            f"1. CHI TIẾT HẠNG MỤC SẢN PHẨM & DỊCH VỤ (Đầy đủ {len(line_items)} hạng mục):\n"
            f"{items_block}\n\n"
            f"2. TỔNG HỢP GIÁ TRỊ THƯƠNG MẠI & CHIẾT KHẤU:\n"
            f"  - Tổng giá trị theo đơn giá niêm yết hiện hành: {format_vnd(tong_niem_yet)}\n"
            f"  - Mức chiết khấu thương mại đề xuất ({applied_discount_pct}%): -{format_vnd(tien_chiet_khau)}\n"
            f"  - **TỔNG GIÁ TRỊ THANH TOÁN (Sau chiết khấu):** **{format_vnd(tong_sau_chiet_khau)}**\n\n"
            f"3. PHƯƠNG ÁN TRIỂN KHAI & CAM KẾT DỊCH VỤ:\n"
            f"{schedule_clause}\n"
            f"{budget_clause}\n"
            f"- **Hiệu lực báo giá & Giữ kho:** Báo giá có hiệu lực trong 15 ngày. Bộ phận Vận hành Minh An đã ưu tiên giữ chỗ (lock tồn kho khả dụng) cho đơn hàng của Quý Công ty.\n\n"
            f"Rất mong nhận được sự chấp thuận từ Quý Công ty để chúng tôi tiến hành các bước triển khai tiếp theo.\n\n"
            f"Trân trọng,\n"
            f"--------------------------------------------------\n"
            f"Người phụ trách: {assigned_rep['ho_ten']} ({assigned_rep['ma_nvkd']}) - {assigned_rep['chuyen_mon']}\n"
            f"Email: {assigned_rep['email']} | Phê duyệt kiểm soát: {approval_level}"
        )

    def _call_optional_llm(
        self,
        llm_config: Dict[str, str],
        req_row: Dict[str, Any],
        line_items: List[Dict[str, Any]],
        recommendations: List[Dict[str, str]],
        draft_email: str,
    ) -> Optional[Dict[str, Any]]:
        provider = llm_config.get("provider", "gemini").lower()
        api_key = llm_config.get("api_key", "").strip()
        if not api_key:
            return None

        prompt = (
            "Bạn là Chuyên gia AI Quản trị Kinh doanh B2B của Công ty Công nghệ Minh An.\n"
            "Dựa trên dữ liệu thẩm định chính xác dưới đây, hãy bổ sung 1 đề xuất đàm phán chiến lược ngắn gọn (dưới 60 từ) "
            "và tinh chỉnh câu chữ bản nháp email cho chuyên nghiệp hơn (nhưng TUYỆT ĐỐI giữ nguyên 100% các con số, mã sản phẩm, giá tiền và thời gian).\n"
            f"Yêu cầu KH: {json.dumps(req_row, ensure_ascii=False)}\n"
            f"Bản nháp hiện tại:\n{draft_email}\n"
            "Trả về JSON có đúng 2 trường: {\"strategic_tip\": \"...\", \"enhanced_draft\": \"...\"}"
        )

        try:
            if provider == "gemini":
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
                payload = {
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {"responseMimeType": "application/json"},
                }
                r = requests.post(url, json=payload, timeout=15)
                if r.status_code == 200:
                    data = r.json()
                    txt = data["candidates"][0]["content"]["parts"][0]["text"]
                    parsed = json.loads(txt)
                    return {
                        "enhanced_draft": parsed.get("enhanced_draft", draft_email),
                        "extra_recommendations": [
                            {
                                "nhom": "Gợi ý Đàm phán Chuyên sâu (Gemini AI)",
                                "muc_do": "AI Insight",
                                "noi_dung": parsed.get("strategic_tip", ""),
                            }
                        ]
                        if parsed.get("strategic_tip")
                        else [],
                    }
            elif provider == "openai":
                url = "https://api.openai.com/v1/chat/completions"
                headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
                payload = {
                    "model": "gpt-4o-mini",
                    "response_format": {"type": "json_object"},
                    "messages": [{"role": "user", "content": prompt}],
                }
                r = requests.post(url, headers=headers, json=payload, timeout=15)
                if r.status_code == 200:
                    data = r.json()
                    txt = data["choices"][0]["message"]["content"]
                    parsed = json.loads(txt)
                    return {
                        "enhanced_draft": parsed.get("enhanced_draft", draft_email),
                        "extra_recommendations": [
                            {
                                "nhom": "Gợi ý Đàm phán Chuyên sâu (OpenAI)",
                                "muc_do": "AI Insight",
                                "noi_dung": parsed.get("strategic_tip", ""),
                            }
                        ]
                        if parsed.get("strategic_tip")
                        else [],
                    }
        except Exception:
            return None
        return None

    # -------------------------------------------------------------------------
    # PROCESS ALL REQUESTS & COMPUTE PORTFOLIO SUMMARY
    # -------------------------------------------------------------------------
    def process_all_requests(self, llm_config: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        results = []
        for _, row in self.df_requests.iterrows():
            res = self.process_request(row.to_dict(), llm_config=llm_config)
            results.append(res)

        total_reqs = len(results)
        complete_count = sum(1 for r in results if r["is_info_complete"])
        need_clarify_count = total_reqs - complete_count
        need_manager_count = sum(1 for r in results if r["is_info_complete"] and r["approval"]["requires_manager_approval"])
        ready_auto_count = sum(
            1 for r in results if r["is_info_complete"] and not r["approval"]["requires_manager_approval"]
        )
        stock_alert_count = sum(
            1
            for r in results
            if r["is_info_complete"]
            and (r["operations"]["so_hang_muc_thieu_ton"] > 0 or not r["operations"]["is_deadline_met"])
        )
        total_pipeline_value = sum(r["financials"]["tong_sau_chiet_khau"] for r in results if r["is_info_complete"])

        return {
            "summary": {
                "total_requests": total_reqs,
                "complete_count": complete_count,
                "need_clarify_count": need_clarify_count,
                "need_manager_count": need_manager_count,
                "ready_auto_count": ready_auto_count,
                "stock_alert_count": stock_alert_count,
                "total_pipeline_value": total_pipeline_value,
                "total_pipeline_formatted": format_vnd(total_pipeline_value),
            },
            "results": results,
            "catalog": self.df_products.to_dict(orient="records"),
            "policies": self.df_policies.to_dict(orient="records"),
            "sales_reps": self.df_reps.to_dict(orient="records"),
        }

