"""
title: Folder-Scoped Memory Isolation
author: linbanana
author_url: https://github.com/linbanana
version: 0.0.2
required_open_webui_version: >= 0.9.5
license: MIT
description: 
    Strict folder isolation for Open WebUI memories. 
    It intercepts the global "Core Memory" leakage while maintaining the management UI.
    
    為 Open WebUI 記憶提供嚴格的資料夾隔離。
    在保留管理介面的同時，攔截並替換掉全域性的核心記憶外洩。
"""

import logging
import re
import threading
import inspect
from datetime import datetime
from typing import Optional, List, Any, Dict, Tuple

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

try:
    from fastapi.requests import Request
    from pydantic import BaseModel, Field
    from open_webui.routers.users import Users
    from open_webui.routers.memories import add_memory, AddMemoryForm, Memories
except ImportError:
    pass

# ──────────────────────────────────────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────────────────────────────────────
FOLDER_TAG_PREFIX = "[F_ID:"
CHAT_TAG_PREFIX = "[C_ID:"
MEMORY_HEADER = "--- FOLDER MEMORY ISOLATION ---\n"


class TTLCache:
    def __init__(self, max_size: int = 128, ttl: int = 3600):
        self._store = {}
        self._max = max_size
        self._ttl = ttl
        self._lock = threading.RLock()

    def get(self, key: str) -> Any:
        with self._lock:
            entry = self._store.get(key)
            if entry and datetime.now().timestamp() < entry['e']:
                return entry['d']
            return None

    def set(self, key: str, value: Any) -> None:
        with self._lock:
            if len(self._store) >= self._max:
                self._store.pop(next(iter(self._store)))
            self._store[key] = {'d': value, 'e': datetime.now().timestamp() + self._ttl}

    def delete(self, key: str) -> None:
        with self._lock:
            self._store.pop(key, None)


class Filter:
    class Valves(BaseModel):
        enabled: bool = Field(default=True, description="Enable/disable the filter.")
        intercept_core: bool = Field(default=True, description="Block and replace Open WebUI's global core memory injection.")
        max_inject: int = Field(default=5, description="Maximum number of memories to inject.")
        enable_auto_cleanup: bool = Field(default=True, description="Automatically delete memories when their associated chat is deleted.")
        debug_mode: bool = Field(default=True, description="Enable verbose logging.")

    class UserValves(BaseModel):
        show_status: bool = Field(default=True, description="Show status messages in the chat.")

    def __init__(self):
        self.valves = self.Valves()
        self._cache = TTLCache()
        # 追蹤哪些 chat 在 inlet 注入了記憶 → outlet 就不重複儲存
        self._injected: Dict[str, bool] = {}

    async def _extract_folder_id(self, body: dict, metadata: Optional[dict]) -> Optional[str]:
        meta = body.get("metadata") or {}
        fid = meta.get("folder_id") or (body.get("chat") or {}).get("folder_id")
        if fid and str(fid).lower() not in ("", "none", "null"):
            return str(fid)

        chat_id = body.get("chat_id") or meta.get("chat_id") or (metadata or {}).get("chat_id")
        if chat_id:
            try:
                from open_webui.models.chats import Chats
                chat = Chats.get_chat_by_id(str(chat_id))
                if inspect.iscoroutine(chat):
                    chat = await chat
                fid = getattr(chat, "folder_id", None) or (chat.get("folder_id") if isinstance(chat, dict) else None)
                if fid and str(fid).lower() not in ("", "none", "null"):
                    return str(fid)
            except:
                pass
        return None

    def _get_chat_id(self, body: dict, metadata: Optional[dict] = None) -> str:
        """從 body 或 metadata 中取得 chat_id"""
        meta = body.get("metadata") or {}
        return str(
            body.get("chat_id")
            or meta.get("chat_id")
            or (metadata or {}).get("chat_id")
            or "unknown"
        )

    def _sanitize_messages(self, messages: List[dict], fid: Optional[str]) -> Tuple[List[dict], bool]:
        """
        雙層防護：
        1. 攔截內建記憶系統的整段注入
        2. 逐行掃描所有系統訊息，移除不屬於當前範圍的 [F_ID:] 內容

        Returns:
            Tuple[List[dict], bool]: (消毒後的訊息列表, 是否偵測到內建個人化記憶)
        """
        cleaned = []
        native_memory_detected = False

        for msg in messages:
            content = msg.get("content", "")
            role = msg.get("role")

            if role != "system":
                cleaned.append(msg)
                continue

            # 跳過我們自己注入的記憶（不要攔截自己）
            if content.startswith(MEMORY_HEADER):
                cleaned.append(msg)
                continue

            modified = False

            # Layer 1: 逐行掃描，移除含有 [F_ID:] 且不屬於當前範圍的行
            if FOLDER_TAG_PREFIX in content:
                lines = content.split('\n')
                if fid:
                    my_tag = f"{FOLDER_TAG_PREFIX}{fid}]"
                    sanitized = [l for l in lines if my_tag in l or FOLDER_TAG_PREFIX not in l]
                else:
                    # Global 模式：移除所有帶 [F_ID:] 的行
                    sanitized = [l for l in lines if FOLDER_TAG_PREFIX not in l]

                removed = len(lines) - len(sanitized)
                if removed > 0:
                    if self.valves.debug_mode:
                        logger.info(f"[Isolation] 消毒了 {removed} 行跨範圍記憶")
                    content = '\n'.join(sanitized).strip()
                    modified = True
                    if not content:
                        continue  # 整段被消毒，丟棄

            # Layer 2: 檢查是否為純記憶注入區塊（移除沒有 [F_ID:] 但仍是內建注入的）
            first_line = content.strip().split('\n')[0] if content.strip() else ""
            
            # 廣泛偵測記憶標頭（英文、繁中、簡中）
            memory_patterns = [
                r"Memory:", r"Prior memories", r"You have the following memories",
                r"記憶：", r"记忆：", r"先前記憶", r"先前记忆"
            ]
            
            is_native_memory = any(re.search(p, first_line, re.IGNORECASE) for p in memory_patterns)
            
            if is_native_memory:
                if self.valves.debug_mode:
                    logger.info(f"[Isolation] 偵測到內建記憶標頭: {first_line}")
                native_memory_detected = True
                continue

            if modified:
                msg = {**msg, "content": content}

            cleaned.append(msg)
        return cleaned, native_memory_detected

    async def _get_scoped_raw(self, uid: str, fid: Optional[str], chat_id: str = None) -> Tuple[List[Any], int]:
        cache_key = f"r:{uid}"
        all_raw = self._cache.get(cache_key)
        if all_raw is None:
            res = Memories.get_memories_by_user_id(user_id=uid)
            all_raw = await res if inspect.iscoroutine(res) else res
            self._cache.set(cache_key, all_raw or [])
        
        if self.valves.debug_mode:
            logger.info(f"[Isolation] 獲取記憶：fid={fid}, chat_id={chat_id}, 原始總數={len(all_raw)}")

        # ── 自動清理已刪除對話的孤兒記憶 ──
        if self.valves.enable_auto_cleanup:
            cleaned_raw = []
            try:
                from open_webui.models.chats import Chats
                for m in all_raw:
                    content = getattr(m, "content", None) or (m.get("content") if isinstance(m, dict) else str(m))
                    c_match = re.search(r"\[C_ID:([^\]]+)\]", content)
                    if c_match:
                        cid = c_match.group(1)
                        chat = Chats.get_chat_by_id(cid)
                        if inspect.iscoroutine(chat): chat = await chat
                        
                        if not chat:
                            mid = getattr(m, "id", None)
                            if mid is None and isinstance(m, dict): mid = m.get("id") or m.get("_id")
                            if mid:
                                if self.valves.debug_mode: logger.info(f"[Isolation] 清理孤兒記憶: id={mid}, cid={cid}")
                                res = Memories.delete_memory_by_id(mid)
                                if inspect.iscoroutine(res): await res
                                continue
                    cleaned_raw.append(m)
                all_raw = cleaned_raw
            except Exception as e:
                if self.valves.debug_mode: logger.warning(f"[Isolation] Cleanup Error: {e}")

        # ── 解析標籤與過濾 ──
        f_pattern = re.compile(r"\[F_ID:([^\]]+)\]")
        c_pattern = re.compile(r"\[C_ID:([^\]]+)\]")
        
        scoped = []
        excluded = 0
        
        for m in all_raw:
            content = (getattr(m, "content", None) or (m.get("content") if isinstance(m, dict) else str(m))).lstrip()
            
            f_match = f_pattern.search(content)
            c_match = c_pattern.search(content)
            
            mem_fid = f_match.group(1) if f_match else None
            mem_cid = c_match.group(1) if c_match else None
            
            if fid:
                # 1. 資料夾模式：F_ID 必須匹配 (同資料夾內跨對話共享)
                if mem_fid == fid:
                    scoped.append(m)
                else:
                    excluded += 1
            else:
                # 2. 全域模式
                if mem_fid:
                    # 排除所有屬於特定資料夾的記憶
                    excluded += 1
                elif mem_cid:
                    # 全域對話隔離：若有 C_ID，則必須屬於當前對話
                    if chat_id and mem_cid == chat_id:
                        scoped.append(m)
                    else:
                        excluded += 1
                else:
                    # 無標籤的舊全域記憶，對所有人開放
                    scoped.append(m)
        
        if self.valves.debug_mode:
            logger.info(f"[Isolation] 過濾結果：scoped={len(scoped)}, excluded={excluded}")
        return scoped, excluded

    def _strip_tag(self, c: str) -> str:
        """移除隔離標記，支援 [F_ID:...] 與 [C_ID:...]（單獨或組合）"""
        return re.sub(r"^(\[F_ID:[^\]]*\])?(\[C_ID:[^\]]*\])?\s*", "", c)

    async def _get_user_obj(self, uid: str):
        """獲取使用者物件並處理非同步"""
        try:
            user = Users.get_user_by_id(uid)
            return await user if inspect.iscoroutine(user) else user
        except: return None

    async def _get_folder_name(self, fid: str) -> str:
        """獲取資料夾名稱，失敗則回傳 fid"""
        if not fid: return None
        try:
            from open_webui.models.folders import Folders
            folder = Folders.get_folder_by_id(fid)
            if inspect.iscoroutine(folder): folder = await folder
            return getattr(folder, "name", fid) or folder.get("name", fid)
        except: return fid

    async def _emit_status(self, emitter, description: str, id: str = None, done: bool = True):
        """統一發送狀態訊息"""
        if not emitter: return
        try:
            data = {"description": description, "done": done}
            if id: data["id"] = id
            await emitter({"type": "status", "data": data})
        except: pass

    async def _check_personal_memory_enabled(self, uid: str) -> bool:
        """檢查使用者是否啟用了 Open WebUI 的原生個人化記憶功能"""
        def recursive_check(d):
            if not isinstance(d, dict): return False
            for k, v in d.items():
                if ("memor" in str(k).lower() or "personal" in str(k).lower()) and v is True: return True
                if isinstance(v, dict) and recursive_check(v): return True
            return False
        try:
            user = await self._get_user_obj(uid)
            if user and hasattr(user, "settings") and user.settings:
                s = user.settings.model_dump() if hasattr(user.settings, "model_dump") else user.settings
                return recursive_check(s)
        except: pass
        return False

    async def _get_language(self, uid: str, body: dict, request: Optional[Request]) -> str:
        """偵測語系，優先從 Body 掃描，其次從 Header 判斷"""
        def find_lang(d):
            if not isinstance(d, dict): return None
            ui = d.get("ui", {}) or {}
            res = ui.get("language") or ui.get("locale")
            if res: return res
            for k, v in d.items():
                if k.lower() in ["language", "locale", "lang"] and v: return v
                if isinstance(v, dict):
                    r = find_lang(v)
                    if r: return r
            return None

        lang = find_lang(body)
        if lang and self.valves.debug_mode: logger.info(f"[Isolation] Body Lang: {lang}")

        if (not lang or lang == "en-us") and request:
            h = request.headers.get("Accept-Language", "").lower()
            if h:
                lang = "zh-tw" if "zh" in h else h.split(",")[0].split(";")[0]
                if self.valves.debug_mode: logger.info(f"[Isolation] Header Lang: {lang}")
        
        return str(lang or "en-us").lower()

    async def inlet(self, body: dict, __user__: Optional[dict] = None, __event_emitter__=None, __metadata__: Optional[dict] = None, __request__: Optional[Request] = None) -> dict:
        if not self.valves.enabled or not __user__: return body
        uid, chat_id = __user__["id"], self._get_chat_id(body, __metadata__)
        fid = await self._extract_folder_id(body, __metadata__)
        lang = await self._get_language(uid, body, __request__)
        is_zh = "zh" in lang

        if self.valves.debug_mode: logger.info(f"[Isolation] Inlet start: {chat_id}, lang: {lang}")

        # ── Step 0 & 1: 檢查與消毒 ──
        meta = body.get("metadata", {}) or {}
        p_mem_on = meta.get("memories") is True or meta.get("memory") is True
        if not p_mem_on: p_mem_on = await self._check_personal_memory_enabled(uid)
        
        n_mem_detected = False
        if self.valves.intercept_core:
            body["messages"], n_mem_detected = self._sanitize_messages(body.get("messages", []), fid)

        # ── Step 2: 禁用內建 ──
        if "metadata" not in body: body["metadata"] = {}
        body["metadata"]["memories"] = body["metadata"]["memory"] = False

        # ── Step 3: 注入隔離記憶 ──
        scoped, _ = await self._get_scoped_raw(uid, fid, chat_id)
        f_name = await self._get_folder_name(fid)
        scope_label = f_name if fid else ("全域" if is_zh else "global")
        
        injected = False
        if scoped:
            mems = [self._strip_tag(getattr(m, "content", None) or (m.get("content") if isinstance(m, dict) else str(m))) for m in scoped[-self.valves.max_inject:]]
            header = f"{MEMORY_HEADER}[Scope: {scope_label}]\n"
            body["messages"] = [{"role": "system", "content": header + "\n".join(mems)}] + body.get("messages", [])
            injected = True
            status = f"📘 {len(mems)} {'筆記憶' if is_zh else 'mems'} ({scope_label})"
        else:
            status = f"ℹ️ {'無記憶' if is_zh else 'No mems'} ({scope_label})"

        # ── Step 4: 發送狀態 ──
        if __event_emitter__:
            if p_mem_on or n_mem_detected:
                msg = "⚠️ 偵測到個人化記憶已開啟，請至設定 > 個人化關閉" if is_zh else "⚠️ Personal Memory is ON, please disable in Settings > Personalization"
                await self._emit_status(__event_emitter__, msg, id="warning")
            await self._emit_status(__event_emitter__, status, id="memory")

        self._injected[chat_id] = injected
        return body

    async def outlet(self, body: dict, __user__: Optional[dict] = None, __event_emitter__=None, __metadata__: Optional[dict] = None, __request__: Optional[Request] = None) -> dict:
        if not self.valves.enabled or not __user__: return body
        messages = body.get("messages", [])
        asst = [m for m in messages if m.get("role") == "assistant" and m.get("content")]
        user = [m for m in messages if m.get("role") == "user" and m.get("content")]
        if not asst or not user: return body

        uid, fid, chat_id = __user__["id"], await self._extract_folder_id(body, __metadata__), self._get_chat_id(body, __metadata__)
        
        # ── 防重複儲存邏輯 ──
        # 1. 檢查 inlet 是否有注入過記憶
        was_injected = self._injected.pop(chat_id, False)
        # 2. 檢查訊息中是否帶有隔離標頭
        has_header = any(MEMORY_HEADER in (m.get("content") or "") for m in messages if m.get("role") == "system")
        
        if was_injected or has_header:
            if self.valves.debug_mode: 
                logger.info(f"[Isolation] Skip save: Injected={was_injected}, Header={has_header} (chat={chat_id})")
            return body

        lang = await self._get_language(uid, body, __request__)
        is_zh = "zh" in lang
        
        # 標籤組合：[F_ID:xxx][C_ID:xxx]
        f_tag = f"{FOLDER_TAG_PREFIX}{fid}]" if fid else ""
        c_tag = f"{CHAT_TAG_PREFIX}{chat_id}]" if chat_id != "unknown" else ""
        
        raw_pair = f"User: {user[-1]['content'].strip()}\nAssistant: {asst[-1]['content'].strip()}"
        tagged = f"{f_tag}{c_tag} {raw_pair}" if (f_tag or c_tag) else raw_pair

        try:
            user_obj = await self._get_user_obj(uid)
            await add_memory(request=__request__, form_data=AddMemoryForm(content=tagged), user=user_obj)
            self._cache.delete(f"r:{uid}")
            
            f_name = await self._get_folder_name(fid)
            display = f_name if fid else ("全域" if is_zh else "global")
            if self.valves.debug_mode: logger.info(f"[Isolation] Saved to {display}")
            
            msg = f"✅ 已儲存至 {display}" if is_zh else f"✅ Saved to {display}"
            await self._emit_status(__event_emitter__, msg)
        except Exception as e:
            if self.valves.debug_mode: logger.error(f"[Isolation] Save failed: {e}")
        return body
