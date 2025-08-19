import React, { useEffect, useRef, useState } from "react";
import "../styles/GpxUploadBtn.css";

/** 簡單 Modal 元件（含遮罩、ESC 關閉、點背景關閉、可捲動內容） */
function Modal({ open, title = "上傳報告", onClose, children }) {
    const dialogRef = useRef(null);

    // ESC 關閉
    useEffect(() => {
        if (!open) return;
        const onKey = (e) => {
            if (e.key === "Escape") onClose?.();
        };
        window.addEventListener("keydown", onKey);
        return () => window.removeEventListener("keydown", onKey);
    }, [open, onClose]);

    if (!open) return null;

    const onOverlayClick = (e) => {
        // 只在點擊遮罩時關閉（避免點擊內容誤關）
        if (e.target === e.currentTarget) onClose?.();
    };

    return (
        <div className="modal-overlay" onClick={onOverlayClick} aria-modal="true" role="dialog">
            <div className="modal-content" ref={dialogRef}>
                <div className="header">
                    <strong>{title}</strong>
                    <button type="button" className="close-modal-btn" aria-label="關閉" onClick={onClose}>
                        ×
                    </button>
                </div>
                <div className="body">{children}</div>
            </div>
        </div>
    );
}

/** 報告視圖：將物件展開為 key/value 列表，巢狀物件以 JSON 顯示 */
function ReportView({ report }) {
    if (!report) return <div>（沒有可顯示的內容）</div>;
    if (typeof report === "string") return <div style={{ whiteSpace: "pre-wrap" }}>{report}</div>;

    const isPrimitive = (v) =>
        v === null || ["string", "number", "boolean"].includes(typeof v);

    const rows = Object.entries(report).map(([k, v]) => (
        <tr key={k}>
            <td className="key">{k}</td>
            <td className="value">
                {isPrimitive(v) ? (
                    String(v)
                ) : (
                    <pre>{JSON.stringify(v, null, 2)}</pre>
                )}
            </td>
        </tr>
    ));

    return (
        <div>
            <table className="report-table">
                <tbody>{rows}</tbody>
            </table>
        </div>
    );
}

/** 主要：GPX 上傳按鈕 + Modal 顯示報告 */
export default function GpxUploadBtn({ onUpload }) {
    const inputRef = useRef(null);
    const [open, setOpen] = useState(false);
    const [report, setReport] = useState(null);
    const [fileName, setFileName] = useState("");
    const [status, setStatus] = useState("idle"); // idle | uploading | success | error
    const [errMsg, setErrMsg] = useState("");

    const openPicker = () => inputRef.current?.click();

    const handleFileChange = async (e) => {
        const file = e.target.files?.[0];
        if (!file) return;

        if (!file.name.toLowerCase().endsWith(".gpx")) {
            setStatus("error");
            setErrMsg("請選擇 .gpx 檔案");
            setReport({ error: "檔案格式錯誤，僅支援 .gpx" });
            setOpen(true);
            return;
        }

        setFileName(file.name);
        setStatus("uploading");
        setErrMsg("");
        setReport(null);

        // 模擬生成假報告
        const fakeReport = {
            message: "本次評估的路線全長約 10 公里，海拔落差約 900 公尺，整體屬於中高強度路線。前段為緩坡林道，適合熱身；中後段開始進入較長距離的陡上，體能消耗較快，對下肢耐力及心肺功能要求較高。根據模擬估算，一般具備基礎登山經驗的隊伍需時約 5 至 6 小時完成，全程需攜帶足量飲水與高熱量行動糧。路線部分區段裸露岩面，雨後恐有濕滑風險，建議攜帶登山杖以增加穩定性。若遇午後天氣變化，山區雲霧聚集迅速，視線易受影響，須提早規劃行程與迴轉點。整體而言，本路線適合體能充足、具中階登山經驗者挑戰，並需注意安全控管及行程安排。",
            exampleKey: "這邊可以吃回傳json的key-value 依序展開",
        };

        setTimeout(() => {
            setReport(fakeReport);
            setStatus("success");
            setOpen(true);
            onUpload?.(fakeReport);

            // 允許重選同名檔案
            e.target.value = "";
        }, 1000); // 模擬延遲
    };

    return (
        <>
            <button
                type="button"
                className="cta-button plan-gpx-btn"
                onClick={openPicker}
                disabled={status === "uploading"}
                aria-busy={status === "uploading"}
            >
                <i className="fa-solid fa-upload" aria-hidden="true"></i>
                {status === "uploading" ? "上傳中…" : "上傳 GPX"}
            </button>

            <input
                ref={inputRef}
                type="file"
                accept=".gpx"
                onChange={handleFileChange}
                style={{ display: "none" }}
            />

            <Modal
                open={open}
                title={status === "success" ? "LLMㄉ報告" : status === "error" ? "上傳失敗" : "上傳報告"}
                onClose={() => setOpen(false)}
            >
                {status === "uploading" && <div>處理中，請稍候…</div>}

                {status !== "uploading" && (
                    <>
                        {status === "error" && (
                            <div style={{ marginBottom: 12, color: "#c62828", fontWeight: 600 }}>{errMsg}</div>
                        )}
                        <ReportView report={report} />

                        <div style={{ marginTop: 16, textAlign: "right" }}>
                        </div>
                    </>
                )}
            </Modal>
        </>
    );
}
