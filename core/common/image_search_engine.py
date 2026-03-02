import io
import json
import os
import shutil
import threading
import uuid
from datetime import datetime
from typing import Dict, List, Optional

import clip
import faiss
import numpy as np
import torch
from PIL import Image

from core.conf import settings


# =========================================================
# CLIP 全局单例（解决首次加载慢 + 多 group 重复加载问题）
# =========================================================


class ClipModelSingleton:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance:
            return cls._instance

        with cls._lock:
            if cls._instance:
                return cls._instance

            instance = super().__new__(cls)

            device = "cuda" if torch.cuda.is_available() else "cpu"
            print(f"[ImageSearch] Loading CLIP model on {device} ...")

            model, preprocess = clip.load("ViT-B/32", device=device)
            model.eval()

            torch.backends.cudnn.benchmark = True

            instance.device = device
            instance.model = model
            instance.preprocess = preprocess

            cls._instance = instance
            print("[ImageSearch] CLIP model loaded.")

            return instance


# =========================================================
# 单个分组引擎
# =========================================================


class ImageSearchEngine:

    INDEX_FILE = "index.faiss"
    META_FILE = "meta.json"

    def __init__(self, gallery_dir: str, data_dir: str, deleted_dir: str):
        self.gallery_dir = str(gallery_dir)
        self.data_dir = str(data_dir)
        self.deleted_dir = str(deleted_dir)

        os.makedirs(self.gallery_dir, exist_ok=True)
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.deleted_dir, exist_ok=True)

        self._lock = threading.RLock()

        # 使用全局 CLIP 单例
        clip_model = ClipModelSingleton()
        self.device = clip_model.device
        self.model = clip_model.model
        self.preprocess = clip_model.preprocess

        self.index_path = os.path.join(self.data_dir, self.INDEX_FILE)
        self.meta_path = os.path.join(self.data_dir, self.META_FILE)

        self.index = None  # 懒加载
        self._load_meta()

    # =====================================================
    # FAISS 懒加载
    # =====================================================

    def _ensure_index(self):
        if self.index is not None:
            return

        if os.path.exists(self.index_path):
            self.index = faiss.read_index(self.index_path)
        else:
            self.index = faiss.IndexFlatIP(512)
            self._save_index()

    def _save_index(self):
        if self.index is not None:
            faiss.write_index(self.index, self.index_path)

    # =====================================================
    # meta 持久化
    # =====================================================

    def _load_meta(self):
        if os.path.exists(self.meta_path):
            with open(self.meta_path, "r", encoding="utf-8") as f:
                self.filenames = json.load(f)
        else:
            self.filenames = []

    def _save_meta(self):
        with open(self.meta_path, "w", encoding="utf-8") as f:
            json.dump(self.filenames, f, ensure_ascii=False, indent=2)

    # =====================================================
    # 特征提取
    # =====================================================

    def _extract_feature(self, img: Image.Image) -> np.ndarray:
        image = self.preprocess(img).unsqueeze(0).to(self.device)

        with torch.no_grad():
            feature = self.model.encode_image(image)

        feature /= feature.norm(dim=-1, keepdim=True)
        return feature.cpu().numpy().astype("float32")

    # =====================================================
    # 新增图片
    # =====================================================

    def add_images(self, files: List[tuple[str, bytes]]) -> int:
        new_features = []
        new_meta = []

        with self._lock:
            self._ensure_index()

            for filename, data in files:
                new_name = f"{uuid.uuid4().hex[:8]}_{filename}"
                path = os.path.join(self.gallery_dir, new_name)

                with open(path, "wb") as f:
                    f.write(data)

                img = Image.open(io.BytesIO(data)).convert("RGB")
                feat = self._extract_feature(img)

                new_features.append(feat)

                new_meta.append(
                    {
                        "stored_name": new_name,
                        "original_name": filename,
                        "upload_time": datetime.now().strftime("%Y%m%d_%H%M%S"),
                    }
                )

            if not new_features:
                return 0

            new_features = np.vstack(new_features)

            self.index.add(new_features)
            self._save_index()

            self.filenames.extend(new_meta)
            self._save_meta()

        return len(new_meta)

    # =====================================================
    # 搜索
    # =====================================================

    def search_image(self, img_bytes: bytes, top_k: int = 5):
        if not self.filenames:
            return []

        with self._lock:
            self._ensure_index()

            real_top_k = min(top_k, len(self.filenames))

            img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
            query_vec = self._extract_feature(img)

            D, I = self.index.search(query_vec, real_top_k)

            results = []
            for idx, score in zip(I[0], D[0]):
                info = self.filenames[idx]
                results.append(
                    {
                        "stored_name": info["stored_name"],
                        "original_name": info["original_name"],
                        "upload_time": info["upload_time"],
                        "score": float(score),
                    }
                )

        return results

    # =====================================================
    # 删除
    # =====================================================

    def delete_image(self, stored_name: str) -> bool:
        with self._lock:
            self._ensure_index()

            index_to_remove = None
            for i, item in enumerate(self.filenames):
                if item["stored_name"] == stored_name:
                    index_to_remove = i
                    break

            if index_to_remove is None:
                return False

            src = os.path.join(self.gallery_dir, stored_name)
            if os.path.exists(src):
                shutil.move(src, os.path.join(self.deleted_dir, stored_name))

            self.index.remove_ids(np.array([index_to_remove]))
            self._save_index()

            self.filenames.pop(index_to_remove)
            self._save_meta()

        return True

    # =====================================================
    # 分页
    # =====================================================

    def list_gallery(
        self,
        page: int = 1,
        page_size: int = 20,
        keyword: Optional[str] = None,
        order: str = "desc",
    ):
        items = self.filenames

        if keyword:
            keyword_lower = keyword.lower()
            items = [f for f in items if keyword_lower in f["original_name"].lower()]

        items = sorted(
            items,
            key=lambda x: x["upload_time"],
            reverse=(order == "desc"),
        )

        total = len(items)
        start = (page - 1) * page_size
        end = start + page_size

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "results": items[start:end],
        }


# =========================================================
# 分组管理器
# =========================================================


class ImageSearchManager:

    def __init__(self, base_workspace: str):
        self.base_workspace = str(base_workspace)
        self.groups_dir = os.path.join(self.base_workspace, "groups")
        os.makedirs(self.groups_dir, exist_ok=True)

        self._engines: Dict[str, ImageSearchEngine] = {}
        self._lock = threading.Lock()

    def _get_group_paths(self, group: str):
        group_dir = os.path.join(self.groups_dir, group)
        return {
            "gallery": os.path.join(group_dir, "gallery"),
            "data": os.path.join(group_dir, "data"),
            "deleted": os.path.join(group_dir, "deleted"),
        }

    def get_engine(self, group: str = "default") -> ImageSearchEngine:
        with self._lock:
            if group in self._engines:
                return self._engines[group]

            paths = self._get_group_paths(group)

            engine = ImageSearchEngine(
                gallery_dir=paths["gallery"],
                data_dir=paths["data"],
                deleted_dir=paths["deleted"],
            )

            self._engines[group] = engine
            return engine

    def list_groups(self):
        return os.listdir(self.groups_dir)
    
    def add_images(
        self,
        files: List[tuple[str, bytes]],
        group: str = "default",
    ) -> int:
        """
        files: [(filename, bytes), ...]
        group: 分组名称
        """

        engine = self.get_engine(group)
        return engine.add_images(files)

    def delete_image(self, stored_name: str, group: Optional[str] = None):
        if group:
            return self.get_engine(group).delete_image(stored_name)

        for g in self.list_groups():
            if self.get_engine(g).delete_image(stored_name):
                return True

        return False

    def search(self, img_bytes: bytes, group: Optional[str] = None, top_k: int = 5):
        results = []

        if group:
            group_results = self.get_engine(group).search_image(img_bytes, top_k)
            for r in group_results:
                r["group"] = group
            return group_results

        for g in self.list_groups():
            group_results = self.get_engine(g).search_image(img_bytes, top_k)
            for r in group_results:
                r["group"] = g
                results.append(r)

        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

        # =====================================================
    # 分页（支持单组 / 全局）
    # =====================================================

    def list_gallery(
        self,
        group: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
        keyword: Optional[str] = None,
        order: str = "desc",
    ):
        # 单组查询
        if group:
            engine = self.get_engine(group)
            result = engine.list_gallery(
                page=page,
                page_size=page_size,
                keyword=keyword,
                order=order,
            )

            # 补充 group 字段
            for item in result["results"]:
                item["group"] = group

            return result

        # ============================
        # 全局查询（合并所有 group）
        # ============================

        all_items = []

        for g in self.list_groups():
            engine = self.get_engine(g)

            # 取全部数据（再统一分页）
            items = engine.list_gallery(
                page=1,
                page_size=10**9,
                keyword=keyword,
                order=order,
            )["results"]

            for item in items:
                item["group"] = g
                all_items.append(item)

        # 全局排序
        all_items = sorted(
            all_items,
            key=lambda x: x["upload_time"],
            reverse=(order == "desc"),
        )

        total = len(all_items)
        start = (page - 1) * page_size
        end = start + page_size

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "results": all_items[start:end],
        }


# =========================================================
# 单例入口
# =========================================================

BASE_DIR = settings.BASE_DIR
_workspace = BASE_DIR / "oss" / "media" / "image_search_workspaces"

_manager: ImageSearchManager = None
_manager_lock = threading.Lock()


def get_image_search_manager():
    global _manager

    with _manager_lock:
        if _manager:
            return _manager

        # 启动时预热模型（解决首次慢）
        ClipModelSingleton()

        _manager = ImageSearchManager(base_workspace=_workspace)
        return _manager


# =========================================================
# 预热
# =========================================================

def warm_up_image_search():
    """
    启动时预热：
    - 加载 CLIP
    - 初始化 CUDA
    - 跑一次 dummy forward
    """

    clip_model = ClipModelSingleton()

    # 构造一个假的 224x224 图片
    dummy = Image.new("RGB", (224, 224), (255, 255, 255))

    image = clip_model.preprocess(dummy).unsqueeze(0).to(clip_model.device)

    with torch.no_grad():
        _ = clip_model.model.encode_image(image)

    print("[ImageSearch] Warm up finished.")
