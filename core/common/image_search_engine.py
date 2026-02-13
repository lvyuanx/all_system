import io
import json
import os
import re
import shutil
import logging
import threading
import uuid
from datetime import datetime
from difflib import get_close_matches
from typing import Dict, List, Optional

import clip
import faiss
import numpy as np
import torch
from PIL import Image

from core.conf import settings

logger = logging.getLogger(__name__)


class ImageSearchEngine:

    def __init__(
        self,
        gallery_dir: str = "gallery",
        data_dir: str = "data",
        deleted_dir: str = "deleted",
        chunk_size: int = 10000,
    ):
        self.gallery_dir = gallery_dir
        self.data_dir = data_dir
        self.deleted_dir = deleted_dir
        self.chunk_size = chunk_size

        os.makedirs(self.gallery_dir, exist_ok=True)
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.deleted_dir, exist_ok=True)

        # 初始化模型
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model, self.preprocess = clip.load("ViT-B/32", device=self.device)

        # 加载索引
        self.features, self.filenames = self._load_all_chunks()
        self.index = faiss.IndexFlatIP(512)
        if len(self.features) > 0:
            self.index.add(self.features)

        logger.info(f"Engine initialized with {len(self.filenames)} images.")

    # ------------------------ 基础工具 ------------------------

    def _extract_feature(self, img: Image.Image) -> np.ndarray:
        """提取图片特征"""
        image = self.preprocess(img).unsqueeze(0).to(self.device)
        with torch.no_grad():
            feature = self.model.encode_image(image)
        feature /= feature.norm(dim=-1, keepdim=True)
        return feature.cpu().numpy().astype("float32")

    def _load_all_chunks(self):
        """加载所有分块"""
        features, filenames = [], []
        for f in sorted(os.listdir(self.data_dir)):
            if not re.match(r"^features_(\d+)\.npy$", f):
                continue
            idx = f.split("_")[1].split(".")[0]
            try:
                feats = np.load(os.path.join(self.data_dir, f))
                with open(
                    os.path.join(self.data_dir, f"filenames_{idx}.json"),
                    "r",
                    encoding="utf-8",
                ) as fp:
                    fnames = json.load(fp)
                features.append(feats)
                filenames.extend(fnames)
            except Exception as e:
                logger.warning(f"跳过分块 {f}: {e}")
        if not features:
            return np.zeros((0, 512), dtype="float32"), []
        return np.vstack(features), filenames

    def _get_current_chunk_index(self):
        existing = []
        for f in os.listdir(self.data_dir):
            m = re.match(r"^features_(\d+)\.npy$", f)
            if m:
                existing.append(int(m.group(1)))
        return max(existing) if existing else 0

    def _append_to_chunk(self, new_features, new_files_info):
        idx = self._get_current_chunk_index()
        feature_path = os.path.join(self.data_dir, f"features_{idx}.npy")
        filename_path = os.path.join(self.data_dir, f"filenames_{idx}.json")

        if os.path.exists(feature_path):
            features = np.load(feature_path)
            with open(filename_path, "r", encoding="utf-8") as f:
                filenames = json.load(f)
        else:
            features = np.zeros((0, new_features.shape[1]), dtype="float32")
            filenames = []

        if len(filenames) + len(new_files_info) > self.chunk_size:
            idx += 1
            feature_path = os.path.join(self.data_dir, f"features_{idx}.npy")
            filename_path = os.path.join(self.data_dir, f"filenames_{idx}.json")
            features = np.zeros((0, new_features.shape[1]), dtype="float32")
            filenames = []

        all_features = np.vstack([features, new_features])
        all_filenames = filenames + new_files_info
        np.save(feature_path, all_features)
        with open(filename_path, "w", encoding="utf-8") as f:
            json.dump(all_filenames, f, ensure_ascii=False, indent=2)

    # ------------------------ 功能函数 ------------------------

    def rebuild_gallery(self):
        """重新初始化图库"""
        features, filenames = [], []
        for fname in os.listdir(self.gallery_dir):
            if fname.lower().endswith(("jpg", "jpeg", "png")):
                img = Image.open(os.path.join(self.gallery_dir, fname)).convert("RGB")
                features.append(self._extract_feature(img))
                filenames.append(
                    {
                        "stored_name": fname,
                        "original_name": fname,
                        "upload_time": datetime.now().strftime("%Y%m%d_%H%M%S"),
                    }
                )

        if not features:
            # 没有图片也要清空旧索引
            self.index.reset()
            self.features = np.zeros((0, 512), dtype="float32")
            self.filenames = []
            logger.info("没有找到图库图片，索引已清空。")
            return 0

        features = np.vstack(features)
        np.save(os.path.join(self.data_dir, "features_0.npy"), features)
        with open(
            os.path.join(self.data_dir, "filenames_0.json"), "w", encoding="utf-8"
        ) as f:
            json.dump(filenames, f, ensure_ascii=False, indent=2)

        self.features, self.filenames = features, filenames
        self.index.reset()
        self.index.add(features)
        logger.info(f"成功重建图库，共 {len(filenames)} 张图片。")
        return len(filenames)

    def add_images(self, files: List[tuple[str, bytes]]):
        """批量添加图片 ([(filename, file_bytes), ...])"""
        new_features = []
        new_files_info = []

        for filename, data in files:
            ext = os.path.splitext(filename)[1]
            new_name = f"{uuid.uuid4().hex[:8]}_{filename}"
            path = os.path.join(self.gallery_dir, new_name)
            with open(path, "wb") as f:
                f.write(data)
            img = Image.open(io.BytesIO(data)).convert("RGB")
            feat = self._extract_feature(img)
            new_features.append(feat)
            new_files_info.append(
                {
                    "stored_name": new_name,
                    "original_name": filename,
                    "upload_time": datetime.now().strftime("%Y%m%d_%H%M%S"),
                }
            )

        new_features = np.vstack(new_features)
        self._append_to_chunk(new_features, new_files_info)
        self.index.add(new_features)
        self.filenames.extend(new_files_info)
        return len(new_files_info)

    def search_image(self, img_bytes: bytes, top_k: int = 5):
        """以图搜图"""
        img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
        query_vec = self._extract_feature(img)
        D, I = self.index.search(query_vec, top_k)
        results = []
        for idx, score in zip(I[0], D[0]):
            info = self.filenames[idx]
            results.append(
                {
                    "stored_name": info["stored_name"],
                    "original_name": info["original_name"],
                    "score": float(score),
                }
            )
        return results

    def search_name(self, keyword: str, limit: int = 10):
        names = [f["original_name"] for f in self.filenames]
        matches = get_close_matches(keyword, names, n=limit, cutoff=0.3)
        return [f for f in self.filenames if f["original_name"] in matches]

    def list_gallery(
        self, page: int = 1, page_size: int = 20, keyword: Optional[str] = None
    ):
        items = self.filenames
        if keyword:
            keyword = keyword.lower()
            items = [f for f in items if keyword in f["original_name"].lower()]
        total = len(items)
        start = (page - 1) * page_size
        end = start + page_size
        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "results": items[start:end],
        }

    def delete_image(self, stored_name: str):
        """逻辑删除（移动到 deleted 目录）"""
        src = os.path.join(self.gallery_dir, stored_name)
        if not os.path.exists(src):
            raise FileNotFoundError(f"Image not found: {stored_name}")
        dst = os.path.join(self.deleted_dir, stored_name)
        shutil.move(src, dst)
        return {"status": "moved_to_deleted", "file": stored_name}


BASE_DIR = settings.BASE_DIR
image_search_workspace = BASE_DIR / "oss" / "media" / "image_search_workspaces"
image_search_engine: ImageSearchEngine = None


def init_image_search_engine():
    """初始化图片搜索引擎"""
    global image_search_engine
    if image_search_engine:
        return

    image_search_engine = ImageSearchEngine(
        gallery_dir=image_search_workspace / "gallery",
        data_dir=image_search_workspace / "data",
        deleted_dir=image_search_workspace / "deleted",
    )
