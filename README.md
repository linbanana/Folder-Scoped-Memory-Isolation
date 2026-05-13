# Folder-Scoped Memory Isolation for Open WebUI 📂

[English](#english) | [繁體中文](#繁體中文)

---

## English

A powerful Filter extension for [Open WebUI](https://github.com/open-webui/open-webui) that provides strict **Folder-level** and **Chat-level** memory isolation. Prevent context leakage between different projects while maintaining full access to the memory management UI.

### 🌟 Features

- **Folder Isolation**: Memories saved within a folder stay within that folder.
- **Global Isolation**: Chats in the root directory maintain their own "global" memory pool, with optional chat-level isolation.
- **Auto-Cleanup (GC)**: Automatically detects and deletes "orphaned" memories when their associated chat is deleted (triggered on the next interaction).
- **Smart Duplicate Prevention**: Automatically detects if the AI is reciting existing memories and skips saving to prevent database redundancy.
- **Bilingual Status Display**: Automatically shows status messages (✅ Saved / 📘 Mems) in Traditional Chinese or English based on the user's Open WebUI settings.
- **Transparent Tagging**: Uses internal `[F_ID:...]` and `[C_ID:...]` tags that are automatically stripped before reaching the AI or User.

### 🚀 Installation

1. Go to **Workspace** -> **Functions** in your Open WebUI.
2. Click **Create** or **Upload**.
3. Paste the content of `folder_memory_isolation.py`.
4. Click **Save** and ensure the filter is **Enabled**.

### ⚙️ Configuration (Valves)

- **enabled**: (Default: True) Enable/disable the filter.
- **intercept_core**: (Default: True) Block and replace Open WebUI's global core memory injection.
- **max_inject**: (Default: 5) Number of relevant memories to inject into the context.
- **enable_auto_cleanup**: (Default: True) Automatically delete memories when their parent chat is deleted.
- **debug_mode**: (Default: True) Enable verbose logging for troubleshooting.

### 🧪 Test Example: Verify Memory Function

1. **Step 1: Create Memory**
   In a chat, type:
   > **User**: "I ate pizza today."
   > 
   > **AI**: "Sounds great! I'll remember that you had pizza today."
   > 
   > *(You should see `✅ Saved to [Folder]` at the bottom)*

2. **Step 2: Load Memory in New Chat**
   Click **New Chat** in the same folder/global and type:
   > **User**: "What did I eat yesterday?"
   > 
   > **AI**: "You ate pizza yesterday."
   > 
   > *(You should see `📘 1 mems` at the bottom, indicating successful retrieval)*

3. **Step 3: Test Auto-Cleanup (Optional)**
   1. Delete the "pizza" chat.
   2. Type anything in a new chat.
   3. Check **Settings -> Personalization -> Memory**. The memory with that Chat ID should be gone.

---

## 繁體中文

這是一個為 [Open WebUI](https://github.com/open-webui/open-webui) 設計的強大過濾器擴充功能，為記憶提供嚴格的 **「資料夾級別」** 與 **「對話級別」** 隔離。

### 🌟 核心功能

- **資料夾隔離**：在特定資料夾中產生的記憶，僅會在該資料夾內的對話中被載入。
- **全域隔離**：根目錄下的對話擁有獨立的「全域記憶池」，且支援對話間的互相隔離。
- **自動清理 (GC)**：當對話被刪除後，該對話產生的孤兒記憶會在下一次互動時自動偵測並刪除。
- **智慧防重複**：自動偵測 AI 是否正在讀取舊記憶，防止將已知的資訊重複存入資料庫。
- **雙語狀態顯示**：根據語系設定，自動顯示繁體中文或英文的狀態提示（✅ 已儲存 / 📘 筆記憶）。
- **透明標籤系統**：使用 `[F_ID:...]` 與 `[C_ID:...]` 標籤，並在傳輸前自動移除。

### 🚀 安裝步驟

1. 進入 Open WebUI 的 **Workspace** -> **Functions**。
2. 點擊 **Create** 或 **Upload**。
3. 將 `folder_memory_isolation.py` 的內容貼上。
4. 點擊 **Save** 並確保已 **Enabled**。

### 🧪 測試範例

1. **第一步：建立記憶**
   輸入：「我今天吃披薩。」（應看到 ✅ 已儲存）
2. **第二步：驗證載入**
   在新對話中問：「我昨天吃什麼？」（應看到 📘 1 筆記憶，AI 回答披薩）
3. **第三步：測試清理**
   刪除對話後，在下一個對話發言，檢查記憶管理介面，該筆記憶應已自動消失。
