"""
title: Folder-Scoped Memory Isolation
author: linbanana
author_url: https://github.com/linbanana
version: 0.0.1
required_open_webui_version: >= 0.3.0
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
MEMORY_HEADER = "📘 Context Memory:\n"
# Core headers used by Open WebUI to inject memories
CORE_MEMORY_HEADERS = ["Memory:", "Prior memories:", "You have the following memories:"]

class TTLCache:
    def __init__(self, max_size: int = 128, ttl: int = 3600):
        self._store = {}
        self._max = max_size
        self._ttl = ttl
        self._lock = threading.RLock()

    def get(self, key: str) -> Any:
        with self._lock:
            entry = self._store.get(key)
            if entry and datetime.now().timestamp() < entry['e']: return entry['d']
            return None

    def set(self, key: str, value: Any) -> None:
        with self._lock:
            if len(self._store) >= self._max: self._store.pop(next(iter(self._store)))
            self._store[key] = {'d': value, 'e': datetime.now().timestamp() + self._ttl}

    def delete(self, key: str) -> None:
        with self._lock: self._store.pop(key, None)

class Filter:
    class Valves(BaseModel):
        enabled: bool = Field(default=True, description="Enable/disable the filter.")
        intercept_core: bool = Field(default=True, description="Block and replace Open WebUI's global core memory injection.")
        max_inject: int = Field(default=5, description="Maximum number of memories to inject.")
        debug_mode: bool = Field(default=False, description="Enable verbose logging.")

    class UserValves(BaseModel):
        show_status: bool = Field(default=True, description="Show status messages in the chat.")

    def __init__(self):
        self.valves = self.Valves()
        self._cache = TTLCache()

    async def _extract_folder_id(self, body: dict, metadata: Optional[dict]) -> Optional[str]:
        meta = body.get("metadata") or {}
        fid = meta.get("folder_id") or (body.get("chat") or {}).get("folder_id")
        if fid and str(fid).lower() not in ("", "none", "null"): return str(fid)
        
        chat_id = body.get("chat_id") or meta.get("chat_id") or (metadata or {}).get("chat_id")
        if chat_id:
            try:
                from open_webui.models.chats import Chats
                chat = Chats.get_chat_by_id(str(chat_id))
                if inspect.iscoroutine(chat): chat = await chat
                fid = getattr(chat, "folder_id", None) or (chat.get("folder_id") if isinstance(chat, dict) else None)
                if fid and str(fid).lower() not in ("", "none", "null"): return str(fid)
            except: pass
        return None

    def _cleanup_core_memories(self, messages: List[dict]) -> List[dict]:
        """Identifies and removes global system messages injected by Open WebUI's core memory system."""
        cleaned = []
        for msg in messages:
            if msg.get("role") == "system":
                content = msg.get("content", "")
                if any(content.startswith(h) for h in CORE_MEMORY_HEADERS):
                    if self.valves.debug_mode: logger.info(f"Blocked core memory leakage: {content[:60]}...")
                    continue
            cleaned.append(msg)
        return cleaned

    async def _get_scoped_raw(self, uid: str, fid: Optional[str]) -> Tuple[List[Any], int]:
        cache_key = f"r:{uid}"
        all_raw = self._cache.get(cache_key)
        if all_raw is None:
            res = Memories.get_memories_by_user_id(user_id=uid)
            all_raw = await res if inspect.iscoroutine(res) else res
            self._cache.set(cache_key, all_raw or [])
        
        tag_prefix = f"{FOLDER_TAG_PREFIX}{fid}]" if fid else FOLDER_TAG_PREFIX
        scoped = []
        excluded = 0
        for m in all_raw:
            content = str(getattr(m, "content", m)).lstrip()
            if fid:
                if content.startswith(tag_prefix): scoped.append(m)
                else: excluded += 1
            else:
                if content.startswith(FOLDER_TAG_PREFIX): excluded += 1
                else: scoped.append(m)
        return scoped, excluded

    def _strip_tag(self, c: str) -> str:
        return re.sub(r"^\[F_ID:[^\]]*\]\s*", "", c)

    async def inlet(self, body: dict, __user__: Optional[dict] = None, __event_emitter__=None, __metadata__: Optional[dict] = None) -> dict:
        if not self.valves.enabled or not __user__: return body
        uid, fid = __user__["id"], await self._extract_folder_id(body, __metadata__)
        
        # 1. Clean Core Leakage (Keep UI on, but block injection)
        if self.valves.intercept_core:
            body["messages"] = self._cleanup_core_memories(body.get("messages", []))

        # 2. Inject Scoped Memories
        scoped, excluded = await self._get_scoped_raw(uid, fid)
        if scoped:
            memories = [self._strip_tag(str(getattr(m, "content", m))) for m in scoped[:self.valves.max_inject]]
            header = f"{MEMORY_HEADER}[Scope: {'folder:'+fid if fid else 'global'}]\n"
            body["messages"] = [{"role": "system", "content": header + "\n".join(memories)}] + body.get("messages", [])
            
            if __event_emitter__ and getattr(getattr(__user__, "valves", __user__.get("valves")), "show_status", True):
                await __event_emitter__({"type": "status", "data": {"description": f"📘 {len(memories)} isolated memories injected", "done": True}})
        return body

    async def outlet(self, body: dict, __user__: Optional[dict] = None, __event_emitter__=None, __metadata__: Optional[dict] = None, __request__: Optional[Request] = None) -> dict:
        if not self.valves.enabled or not __user__: return body
        messages = body.get("messages", [])
        asst_msgs = [m for m in messages if m.get("role") == "assistant" and m.get("content")]
        user_msgs = [m for m in messages if m.get("role") == "user" and m.get("content")]
        if not asst_msgs or not user_msgs: return body

        uid, fid = __user__["id"], await self._extract_folder_id(body, __metadata__)
        if any(MEMORY_HEADER in (m.get("content") or "") for m in messages if m.get("role") == "system"): return body

        raw = f"User: {user_msgs[-1]['content'].strip()}\nAssistant: {asst_msgs[-1]['content'].strip()}"
        tagged = f"{FOLDER_TAG_PREFIX}{fid}] {raw}" if fid else raw
        
        try:
            user_obj = Users.get_user_by_id(uid)
            if inspect.iscoroutine(user_obj): user_obj = await user_obj
            await add_memory(request=__request__, form_data=AddMemoryForm(content=tagged), user=user_obj)
            self._cache.delete(f"r:{uid}")
            if __event_emitter__ and getattr(getattr(__user__, "valves", __user__.get("valves")), "show_status", True):
                await __event_emitter__({"type": "status", "data": {"description": f"✅ Saved to {fid or 'global'}", "done": True}})
        except: pass
        return body
