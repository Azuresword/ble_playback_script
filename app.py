#!/usr/bin/env python3
"""
BLE 数据处理 Web API
提供文件上传、处理、下载等功能
"""
import os
import subprocess
import asyncio
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import csv

app = FastAPI(title="BLE Data Processing API", version="1.0.0")

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 配置
UPLOAD_DIR = Path("uploads")
OUTPUT_DIR = Path("output")
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# 任务状态存储
tasks_status = {}


class TaskStatus(BaseModel):
    task_id: str
    status: str  # pending, processing, completed, failed
    progress: int  # 0-100
    message: str
    result: Optional[dict] = None
    error: Optional[str] = None


class ProcessRequest(BaseModel):
    filename: str
    steps: List[str]  # ["split", "align", "downsample", "convert"]


@app.get("/")
async def root():
    """API根路径"""
    return {"message": "BLE Data Processing API", "version": "1.0.0"}


@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """上传数据文件"""
    try:
        # 保存文件
        file_path = UPLOAD_DIR / file.filename
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        # 获取文件信息
        file_size = os.path.getsize(file_path)

        # 预览前几行
        preview = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                for i, row in enumerate(reader):
                    if i >= 10:  # 只读前10行
                        break
                    preview.append(row)
        except Exception:
            preview = []

        return {
            "success": True,
            "filename": file.filename,
            "size": file_size,
            "preview": preview,
            "message": f"文件上传成功: {file.filename}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/process")
async def process_data(request: ProcessRequest, background_tasks: BackgroundTasks):
    """处理数据"""
    task_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    # 初始化任务状态
    tasks_status[task_id] = {
        "task_id": task_id,
        "status": "pending",
        "progress": 0,
        "message": "任务已创建",
        "result": None,
        "error": None
    }

    # 在后台执行处理
    background_tasks.add_task(run_processing, task_id, request)

    return {"task_id": task_id, "message": "处理任务已启动"}


async def run_processing(task_id: str, request: ProcessRequest):
    """后台执行数据处理"""
    try:
        tasks_status[task_id]["status"] = "processing"
        tasks_status[task_id]["message"] = "开始处理数据"

        # 复制上传的文件到工作目录
        source = UPLOAD_DIR / request.filename
        dest = Path("data.csv")

        if source.exists():
            import shutil
            shutil.copy(source, dest)

        total_steps = len(request.steps)

        for i, step in enumerate(request.steps):
            progress = int((i / total_steps) * 100)
            tasks_status[task_id]["progress"] = progress

            if step == "split":
                tasks_status[task_id]["message"] = "正在拆分设备数据..."
                result = subprocess.run(["python3", "split_by_device.py"],
                                      capture_output=True, text=True)
                if result.returncode != 0:
                    raise Exception(f"拆分失败: {result.stderr}")

            elif step == "align":
                tasks_status[task_id]["message"] = "正在对齐气压计数据..."
                if Path("bmp/Barometer.csv").exists():
                    result = subprocess.run(["python3", "align_barometer.py"],
                                          capture_output=True, text=True)
                    if result.returncode != 0:
                        raise Exception(f"对齐失败: {result.stderr}")
                else:
                    tasks_status[task_id]["message"] = "跳过气压计对齐（文件不存在）"

            elif step == "downsample":
                tasks_status[task_id]["message"] = "正在降采样到 50Hz..."
                result = subprocess.run(["python3", "downsample_50hz.py"],
                                      capture_output=True, text=True)
                if result.returncode != 0:
                    raise Exception(f"降采样失败: {result.stderr}")

            elif step == "convert":
                tasks_status[task_id]["message"] = "正在转换为二进制格式..."
                result = subprocess.run(["python3", "csv_to_bin.py"],
                                      capture_output=True, text=True)
                if result.returncode != 0:
                    raise Exception(f"转换失败: {result.stderr}")

        # 收集输出文件
        output_files = []
        for device in ["WTR1", "WTL1", "WTB1"]:
            device_dir = Path(f"{device}_data")
            if device_dir.exists():
                for file in device_dir.glob("*.csv"):
                    output_files.append(str(file))
                for file in device_dir.glob("*.bin"):
                    output_files.append(str(file))

        tasks_status[task_id]["status"] = "completed"
        tasks_status[task_id]["progress"] = 100
        tasks_status[task_id]["message"] = "处理完成"
        tasks_status[task_id]["result"] = {
            "output_files": output_files,
            "total_files": len(output_files)
        }

    except Exception as e:
        tasks_status[task_id]["status"] = "failed"
        tasks_status[task_id]["error"] = str(e)
        tasks_status[task_id]["message"] = f"处理失败: {str(e)}"


@app.get("/api/task/{task_id}")
async def get_task_status(task_id: str):
    """获取任务状态"""
    if task_id not in tasks_status:
        raise HTTPException(status_code=404, detail="任务不存在")
    return tasks_status[task_id]


@app.get("/api/files")
async def list_files():
    """列出所有输出文件"""
    files = []

    for device in ["WTR1", "WTL1", "WTB1"]:
        device_dir = Path(f"{device}_data")
        if device_dir.exists():
            for file in device_dir.glob("*"):
                if file.is_file():
                    stat = file.stat()
                    files.append({
                        "name": file.name,
                        "path": str(file),
                        "size": stat.st_size,
                        "device": device,
                        "type": file.suffix
                    })

    return {"files": files, "total": len(files)}


@app.get("/api/download/{device}/{filename}")
async def download_file(device: str, filename: str):
    """下载文件"""
    file_path = Path(f"{device}_data") / filename

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="文件不存在")

    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="application/octet-stream"
    )


@app.get("/api/preview/{device}/{filename}")
async def preview_csv(device: str, filename: str, limit: int = 100):
    """预览CSV文件"""
    file_path = Path(f"{device}_data") / filename

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="文件不存在")

    if not filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="只能预览CSV文件")

    try:
        data = []
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = next(reader)

            for i, row in enumerate(reader):
                if i >= limit:
                    break
                data.append(row)

        return {
            "header": header,
            "data": data,
            "total_rows": len(data)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/stats/{device}/{filename}")
async def get_stats(device: str, filename: str):
    """获取CSV文件统计信息"""
    file_path = Path(f"{device}_data") / filename

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="文件不存在")

    if not filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="只能分析CSV文件")

    try:
        import pandas as pd
        df = pd.read_csv(file_path)

        stats = {
            "row_count": len(df),
            "column_count": len(df.columns),
            "columns": df.columns.tolist(),
            "numeric_stats": {}
        }

        # 获取数值列的统计
        numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
        for col in numeric_cols[:10]:  # 只取前10个数值列
            stats["numeric_stats"][col] = {
                "min": float(df[col].min()),
                "max": float(df[col].max()),
                "mean": float(df[col].mean()),
                "std": float(df[col].std())
            }

        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 挂载静态文件（前端）
if Path("web/dist").exists():
    app.mount("/", StaticFiles(directory="web/dist", html=True), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
