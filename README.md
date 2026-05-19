# Folder-Scoped Memory Isolation & Atomic Memory for Open WebUI 📂🧠

[English](#english) | [繁體中文](#繁體中文)

---

## English

A powerful Filter extension for [Open WebUI](https://github.com/open-webui/open-webui) that provides strict **Folder-level** and **Chat-level** memory isolation, combined with intelligent, LLM-based **Atomic Memory Extraction**. 

Prevent context leakage between different projects while maintaining full access to the memory management UI and automatically refining long-term user facts into granular, concise memories.

### 🌟 Features

- **Folder Isolation**: Memories saved within a folder stay strictly within that folder.
- **LLM Atomic Memory Extraction**: Automatically analyzes dialogue turns to extract concise, long-term personal facts (e.g., job, location, habits, preferences). Ignores ephemeral/technical noise (e.g. coding requests, math, temporary plans).
- **Global Isolation**: Chats in the root directory maintain their own "global" memory pool, with optional chat-level isolation.
- **Zero-Risk Fallback**: If the API key is empty, the filter automatically falls back to raw QA pair saving mode, ensuring 100% stability.
- **Auto-Cleanup (GC)**: Automatically detects and deletes "orphaned" memories when their associated chat is deleted.
- **Bilingual Status Display**: Automatically shows status messages (`🧠 Extracting...` / `✅ Saved...` / `📘 X mems`) in Traditional Chinese or English based on the user's Open WebUI language setting.
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
- **atomic_memory_enabled**: (Default: True) Extract atomic, concise facts instead of saving raw dialog QA pairs.
- **openai_api_url**: (Default: `https://api.openai.com/v1`) OpenAI-compatible API URL.
- **openai_api_key**: (Default: `""`) API Key for the endpoint (leave empty to fallback to raw QA mode).
- **openai_model**: (Default: `gpt-4o-mini`) Model name for extraction.

### 🧪 Test Example: Verify Atomic Memory

1. **Step 1: Disable Native Personalization Memory**
   Go to **Settings -> Personalization -> Memory** and turn it **OFF**. This ensures only our filter manages memory.
   
2. **Step 2: Create Memory with Noise**
   Inside a folder chat, type:
   > **User**: *"I'm so tired today, it was raining heavily and my shoes are completely wet. By the way, I am self-learning Rust recently because I need to write system-level stuff later and my supervisor says Rust is safer than C++. Can you write a Quick Sort in Rust for me?"*
   
   *(You should see `🧠 Extracting atomic memory...` then `✅ Saved 1 atomic memories` at the bottom)*

3. **Step 3: Verify the Extracted Fact**
   Go to **Settings -> Personalization -> Manage Memories**. You will see:
   `[F_ID:xxx][C_ID:xxx] User is self-learning Rust.`
   *(Notice that wet shoes, rain, and the quick sort request were successfully filtered out!)*

---

## 繁體中文

這是一個為 [Open WebUI](https://github.com/open-webui/open-webui) 設計的強大過濾器擴充功能，結合了嚴格的 **「資料夾級別」/「對話級別」記憶隔離** 與基於大模型的 **「原子化記憶提煉 (Atomic Memory Extraction)」**。

防止不同專案之間的脈絡外洩，同時自動將對話中的長期事實與喜好精煉為簡短、獨立的記憶條目。

### 🌟 核心功能

- **資料夾隔離**：在特定資料夾中產生的記憶，僅會在該資料夾內的對話中被載入。
- **大模型原子記憶提煉**：自動分析每輪對話，提煉出關於使用者的長期事實與偏好（如工作、居住地、習慣、喜好），自動排除短期技術任務與日常廢話。
- **全域隔離**：根目錄下的對話擁有獨立的「全域記憶池」，且支援對話間的互相隔離。
- **安全回退機制**：未設定 API 金鑰時，自動無縫回退至「原始對話儲存模式」，確保 100% 穩定不報錯。
- **自動清理 (GC)**：當對話被刪除後，該對話產生的孤兒記憶會在下一次互動時自動偵測並刪除。
- **雙語狀態顯示**：根據語系設定，自動顯示繁體中文或英文的狀態提示（`🧠 正在提取...` / `✅ 已儲存...` / `📘 筆記憶`）。
- **透明標籤系統**：使用 `[F_ID:...]` 與 `[C_ID:...]` 標籤，並在傳輸前自動移除。

### 🚀 安裝步驟

1. 進入 Open WebUI 的 **Workspace** -> **Functions**。
2. 點擊 **Create** 或 **Upload**。
3. 將 `folder_memory_isolation.py` 的內容貼上。
4. 點擊 **Save** 並確保已 **Enabled**。

### ⚙️ 設定選項 (Valves)

- **enabled**: （預設：True）啟用/停用此過濾器。
- **intercept_core**: （預設：True）攔截並替換 Open WebUI 原生的全域核心記憶注入。
- **max_inject**: （預設：5）注入至當前上下文的相關記憶條數上限。
- **enable_auto_cleanup**: （預設：True）當對話被刪除時，自動清理關聯的記憶。
- **debug_mode**: （預設：True）啟用詳細日誌輸出，便於調試。
- **atomic_memory_enabled**: （預設：True）提取原子化、簡短的事實，而非儲存原始問答對。
- **openai_api_url**: （預設：`https://api.openai.com/v1`）OpenAI 相容的接口網址。
- **openai_api_key**: （預設：`""`）API 金鑰（若留空，將自動安全回退至傳統對話儲存模式）。
- **openai_model**: （預設：`gpt-4o-mini`）用於提煉事實的模型名稱。

### 🧪 測試與驗證

1. **第一步：關閉原生個人化記憶**
   進入 **設定 > 個人化 > 記憶**，將其**關閉**。這能確保只有我們的過濾器控制記憶，防止原生系統儲存無標籤的全域記憶。
   
2. **第二步：輸入含有雜訊的測試對話**
   在特定資料夾的對話中輸入：
   > **使用者**：「哎呀今天真的累死了，外面雨下得超大害我鞋子都濕透了，心情真差。對了，我最近在自學 Rust 語言，因為我之後可能要寫系統底層，主管說用 Rust 會比 C++ 安全。對了，你可以順便幫我寫一個用 Rust 寫的快速排序法嗎？我現在就要。」
   
   *（您會看到 `🧠 正在提取原子記憶...` 然後顯示 `✅ 已成功儲存 1 筆原子記憶至...`）*

3. **第三步：驗證提煉結果**
   進入 **設定 > 個人化 > 管理記憶**，您會看到一筆精準的條目：
   `[F_ID:xxx][C_ID:xxx] 使用者最近在自學 Rust 語言`
   *（鞋子濕、下雨天、寫快速排序法等短期雜訊已成功被大模型過濾！）*
