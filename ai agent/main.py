import os
import shutil
from typing import Optional
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from agent_engine import MinhAnSalesAgent
from generate_sample_data import build_datasets

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
STATIC_DIR = os.path.join(BASE_DIR, "static")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)

# Ensure sample data exists
if not os.path.exists(os.path.join(DATA_DIR, "yeu_cau_khach_hang_mau.csv")):
    build_datasets()

# Copy uploaded workflow diagram if present so UI can display it
UPLOADED_IMG = r"C:\Users\Admin S88\.gemini\antigravity\brain\32b68be3-af00-4839-b822-d9b25568b16b\.user_uploaded\media_1794385516748_0be91bbb.jpg"
TARGET_IMG = os.path.join(STATIC_DIR, "workflow_minh_an.jpg")
if os.path.exists(UPLOADED_IMG) and not os.path.exists(TARGET_IMG):
    try:
        shutil.copyfile(UPLOADED_IMG, TARGET_IMG)
    except Exception:
        pass

app = FastAPI(title="Minh An B2B Sales AI Agent", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

agent = MinhAnSalesAgent()


class GoogleSheetRequest(BaseModel):
    sheet_url: str
    llm_provider: Optional[str] = "gemini"
    llm_api_key: Optional[str] = ""


class CustomRequestInput(BaseModel):
    ten_khach_hang: str
    nguoi_lien_he: str
    email_kh: str
    kenh_tiep_nhan: str = "Email"
    noi_dung_yeu_cau: str
    ngan_sach_vnd: float = 0
    thoi_han_yeu_cau_ngay: int = 0
    de_nghi_chiet_khau_pct: float = 0.0
    llm_provider: Optional[str] = "gemini"
    llm_api_key: Optional[str] = ""


class AnalyzeAllParams(BaseModel):
    llm_provider: Optional[str] = "gemini"
    llm_api_key: Optional[str] = ""


class ApprovalActionInput(BaseModel):
    ma_yeu_cau: str
    action: str  # "approve", "request_revision", "mark_sent"
    approver_note: Optional[str] = ""
    approved_discount_pct: Optional[float] = None


class ClarifyRequestInput(BaseModel):
    ma_yeu_cau: str
    bo_sung_noi_dung: str
    ngan_sach_vnd: float = 0
    thoi_han_yeu_cau_ngay: int = 0
    de_nghi_chiet_khau_pct: float = 0.0
    llm_provider: Optional[str] = "gemini"
    llm_api_key: Optional[str] = ""


approval_overrides = {}


def apply_overrides(data: dict) -> dict:
    for r in data.get("results", []):
        yc = r["ma_yeu_cau"]
        if yc in approval_overrides:
            ov = approval_overrides[yc]
            if ov.get("approved_discount_pct") is not None and r["is_info_complete"]:
                new_disc = float(ov["approved_discount_pct"])
                tong_ny = r["financials"]["tong_gia_niem_yet"]
                tien_ck = round(tong_ny * (new_disc / 100.0))
                tong_sau = tong_ny - tien_ck
                r["financials"]["ap_dung_chiet_khau_pct"] = new_disc
                r["financials"]["tien_chiet_khau"] = tien_ck
                r["financials"]["tong_sau_chiet_khau"] = tong_sau
                if r["financials"]["ngan_sach_khach_hang"] > 0:
                    r["financials"]["chenh_lech_ngan_sach"] = r["financials"]["ngan_sach_khach_hang"] - tong_sau
                    r["financials"]["is_within_budget"] = r["financials"]["chenh_lech_ngan_sach"] >= 0

            act = ov.get("action")
            note = ov.get("approver_note", "")
            if act == "approve":
                r["final_status"] = "Đã Phê duyệt — Sẵn sàng gửi KH"
                r["status_color"] = "emerald"
                r["approval"]["requires_manager_approval"] = False
                r["approval"]["approved_by_manager"] = True
                r["approval"]["manager_note"] = note or "Trưởng phòng / BGĐ đã phê duyệt đề xuất & chiết khấu."
                r["draft_email"] = r["draft_email"].replace(
                    "[BẢN NHÁP TRÌNH DUYỆT NỘI BỘ - Cần " + r["approval"]["approval_level"] + " phê duyệt trước khi gửi KH]",
                    f"[ĐÃ ĐƯỢC PHÊ DUYỆT BỞI: {r['approval']['approver_name']} — SẴN SÀNG GỬI KHÁCH HÀNG]",
                )
            elif act == "mark_sent":
                r["final_status"] = "Đã gửi phản hồi KH & Đang theo dõi"
                r["status_color"] = "emerald"
                r["approval"]["manager_note"] = note or "Đã gửi email đề xuất/phản hồi cho khách hàng."
    return data


@app.get("/api/analyze-all")
def analyze_all():
    return apply_overrides(agent.process_all_requests())


@app.post("/api/analyze-all")
def analyze_all_with_llm(params: AnalyzeAllParams):
    llm_cfg = {"provider": params.llm_provider or "gemini", "api_key": params.llm_api_key or ""}
    return apply_overrides(agent.process_all_requests(llm_config=llm_cfg))


@app.post("/api/approve-action")
def approve_action(payload: ApprovalActionInput):
    approval_overrides[payload.ma_yeu_cau] = {
        "action": payload.action,
        "approver_note": payload.approver_note,
        "approved_discount_pct": payload.approved_discount_pct,
    }
    return apply_overrides(agent.process_all_requests())


@app.post("/api/clarify-request")
def clarify_request(payload: ClarifyRequestInput):
    mask = agent.df_requests["ma_yeu_cau"] == payload.ma_yeu_cau
    if not mask.any():
        raise HTTPException(status_code=404, detail="Không tìm thấy mã yêu cầu")

    idx = agent.df_requests[mask].index[0]
    old_text = str(agent.df_requests.loc[idx, "noi_dung_yeu_cau"])
    if payload.bo_sung_noi_dung.strip():
        agent.df_requests.loc[idx, "noi_dung_yeu_cau"] = (
            f"{old_text} [KH Bổ sung thông tin: {payload.bo_sung_noi_dung.strip()}]"
        )
    if payload.ngan_sach_vnd > 0:
        agent.df_requests.loc[idx, "ngan_sach_vnd"] = payload.ngan_sach_vnd
    if payload.thoi_han_yeu_cau_ngay > 0:
        agent.df_requests.loc[idx, "thoi_han_yeu_cau_ngay"] = payload.thoi_han_yeu_cau_ngay
    if payload.de_nghi_chiet_khau_pct > 0:
        agent.df_requests.loc[idx, "de_nghi_chiet_khau_pct"] = payload.de_nghi_chiet_khau_pct

    llm_cfg = {"provider": payload.llm_provider or "gemini", "api_key": payload.llm_api_key or ""}
    return apply_overrides(agent.process_all_requests(llm_config=llm_cfg))


@app.get("/api/export-report-xlsx")
def export_report_xlsx():
    import io
    import pandas as pd
    from fastapi.responses import StreamingResponse

    data = apply_overrides(agent.process_all_requests())
    rows = []
    item_rows = []
    for r in data["results"]:
        f = r["financials"]
        op = r["operations"]
        ap = r["approval"]
        rows.append(
            {
                "Mã Yêu cầu": r["ma_yeu_cau"],
                "Mã Hồ sơ Cơ hội": r["ma_ho_so_co_hoi"],
                "Ngày tiếp nhận": r["ngay_nhan"],
                "Kênh": r["kenh_tiep_nhan"],
                "Khách hàng": r["ten_khach_hang"],
                "Người liên hệ": r["nguoi_lien_he"],
                "Đủ thông tin?": "Đủ thông tin" if r["is_info_complete"] else "Cần làm rõ / bổ sung",
                "Trạng thái Quy trình": r["final_status"],
                "NVKD Phụ trách": f"{r['assigned_rep']['ho_ten']} ({r['assigned_rep']['ma_nvkd']})",
                "Cấp Phê duyệt": ap["approval_level"],
                "Người Phê duyệt": ap["approver_name"],
                "Ngân sách KH (VNĐ)": f["ngan_sach_khach_hang"],
                "Tổng Giá Niêm yết 2026 (VNĐ)": f["tong_gia_niem_yet"],
                "Chiết khấu Áp dụng (%)": f["ap_dung_chiet_khau_pct"],
                "Tổng Sau Chiết khấu (VNĐ)": f["tong_sau_chiet_khau"],
                "Đáp ứng Ngân sách?": "Đạt" if f["is_within_budget"] else "Vượt ngân sách / Chưa rõ",
                "Thời hạn KH yêu cầu (Ngày)": op["thoi_han_khach_yeu_cau_ngay"],
                "Thời gian đáp ứng thực tế (Ngày)": op["thoi_gian_dap_ung_thuc_te_ngay"],
                "Số hạng mục thiếu tồn": op["so_hang_muc_thieu_ton"],
                "Đề xuất Kinh doanh chính": " | ".join([rec["noi_dung"] for rec in r["recommendations"]]),
                "Bản nháp Phản hồi KH": r["draft_email"],
            }
        )
        for li in r["line_items"]:
            item_rows.append(
                {
                    "Mã Hồ sơ Cơ hội": r["ma_ho_so_co_hoi"],
                    "Khách hàng": r["ten_khach_hang"],
                    "Mã SP": li["ma_sp"],
                    "Tên Sản phẩm / Dịch vụ": li["ten_sp"],
                    "ĐVT": li["don_vi"],
                    "Số lượng": li["so_luong"],
                    "Đơn giá 2026 (VNĐ)": li["don_gia_niem_yet"],
                    "Thành tiền (VNĐ)": li["thanh_tien"],
                    "Tồn khả dụng": li["ton_kha_dung"],
                    "Đủ tồn kho?": "Đủ" if li["du_ton_kho"] else f"Thiếu {li['so_luong_thieu']}",
                    "Thời gian đáp ứng (Ngày)": li["tg_dap_ung_ngay"],
                }
            )

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        pd.DataFrame(rows).to_excel(writer, sheet_name="TongHop_HoSoCoHoi", index=False)
        pd.DataFrame(item_rows).to_excel(writer, sheet_name="ChiTiet_BaoGia_TonKho", index=False)
    output.seek(0)

    headers = {"Content-Disposition": 'attachment; filename="BaoCao_HoSoCoHoi_MinhAn_B2B.xlsx"'}
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=headers,
    )


@app.post("/api/upload-file")
async def upload_file(
    file: UploadFile = File(...),
    llm_provider: str = Form("gemini"),
    llm_api_key: str = Form(""),
):
    try:
        content = await file.read()
        meta = agent.load_from_uploaded_bytes(file.filename, content)
        llm_cfg = {"provider": llm_provider, "api_key": llm_api_key}
        data = agent.process_all_requests(llm_config=llm_cfg)
        data["upload_meta"] = meta
        return data
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/load-google-sheet")
def load_google_sheet(payload: GoogleSheetRequest):
    try:
        meta = agent.load_from_google_sheet_url(payload.sheet_url)
        llm_cfg = {"provider": payload.llm_provider or "gemini", "api_key": payload.llm_api_key or ""}
        data = agent.process_all_requests(llm_config=llm_cfg)
        data["upload_meta"] = meta
        return data
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/analyze-single")
def analyze_single(payload: CustomRequestInput):
    import pandas as pd

    new_id = f"YC-2026-{len(agent.df_requests) + 1:03d}"
    new_row = {
        "ma_yeu_cau": new_id,
        "ngay_nhan": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
        "kenh_tiep_nhan": payload.kenh_tiep_nhan,
        "ten_khach_hang": payload.ten_khach_hang,
        "nguoi_lien_he": payload.nguoi_lien_he,
        "email_kh": payload.email_kh,
        "noi_dung_yeu_cau": payload.noi_dung_yeu_cau,
        "ngan_sach_vnd": payload.ngan_sach_vnd,
        "thoi_han_yeu_cau_ngay": payload.thoi_han_yeu_cau_ngay,
        "de_nghi_chiet_khau_pct": payload.de_nghi_chiet_khau_pct,
        "nvkd_phu_trach_goi_y": "",
    }
    agent.df_requests = pd.concat([pd.DataFrame([new_row]), agent.df_requests], ignore_index=True)
    llm_cfg = {"provider": payload.llm_provider or "gemini", "api_key": payload.llm_api_key or ""}
    data = agent.process_all_requests(llm_config=llm_cfg)
    data["created_id"] = new_id
    return data


@app.post("/api/reset-sample")
def reset_sample():
    agent.reload_default_data()
    return agent.process_all_requests()


@app.get("/api/download-sample/{file_type}")
def download_sample(file_type: str):
    mapping = {
        "full_xlsx": ("du_lieu_minh_an_b2b_full.xlsx", "du_lieu_minh_an_b2b_full.xlsx"),
        "requests_xlsx": ("yeu_cau_khach_hang_mau.xlsx", "yeu_cau_khach_hang_mau.xlsx"),
        "requests_csv": ("yeu_cau_khach_hang_mau.csv", "yeu_cau_khach_hang_mau.csv"),
        "products_csv": ("danh_muc_san_pham_ton_kho.csv", "danh_muc_san_pham_ton_kho.csv"),
        "policies_csv": ("chinh_sach_chiet_khau_duyet.csv", "chinh_sach_chiet_khau_duyet.csv"),
    }
    if file_type not in mapping:
        raise HTTPException(status_code=404, detail="Không tìm thấy file mẫu")
    fname, dl_name = mapping[file_type]
    fpath = os.path.join(DATA_DIR, fname)
    return FileResponse(fpath, filename=dl_name)


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
def serve_index():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))

