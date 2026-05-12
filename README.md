# Folder-Scoped Memory Isolation for Open WebUI 📂

A powerful Filter extension for [Open WebUI](https://github.com/open-webui/open-webui) that provides strict memory isolation based on folders. It prevents context leakage between different projects while maintaining full access to the memory management UI.

## 🌟 Features

- **Folder Isolation**: Memories saved within a folder stay within that folder.
- **Global Scope**: Chats in the root directory maintain their own separate "global" memory pool.
- **Core Interceptor**: Allows you to keep Open WebUI's built-in "Memory" feature **ON** (to use the management UI) while blocking its global injection leakage in the background.
- **Transparent Tagging**: Uses internal `[F_ID:...]` tags that are automatically stripped before reaching the AI or User.
- **Async Compatible**: Works with both sync and async Open WebUI database drivers.

---

## 🚀 How to Install

1. Go to **Workspace** -> **Filters** in your Open WebUI.
2. Click **Create Filter** or **Upload**.
3. Copy and paste the content of `folder_memory_isolation.py`.
4. Click **Save**.

## ⚙️ Configuration (Valves)

- **intercept_core**: (Default: True) Automatically removes the global memories injected by Open WebUI's core system and replaces them with isolated ones.
- **max_inject**: (Default: 5) Number of relevant memories to inject into the context.
- **show_status**: (User Valve) Toggle the visibility of memory status messages (📘/✅) in the chat.

## 💡 Why use this?

By default, Open WebUI's memory system is global. If you discuss coding in "Folder A" and then have a casual chat in "Folder B", the AI might retrieve coding snippets into your casual chat, causing context contamination. This filter solves that by ensuring each folder has its own "brain."

---

# Open WebUI 資料夾記憶隔離過濾器 📂

這是一個為 Open WebUI 設計的強力過濾器，提供基於資料夾的嚴格記憶隔離。它能防止不同專案間的上下文洩漏，同時讓你保留記憶管理介面的存取權。

## 🌟 功能特色

- **資料夾隔離**：在資料夾內產生的記憶僅會在該資料夾中生效。
- **全域範圍**：根目錄下的對話擁有獨立的「全域」記憶池。
- **核心攔截器**：允許你保持內建「記憶」功能**開啟**（以使用管理介面），同時在背景攔截其產生的全域注入洩漏。
- **透明標籤**：使用內部 `[F_ID:...]` 標籤，發送給 AI 或顯示給使用者前會自動移除。
- **非同步相容**：支援同步與非同步的 Open WebUI 資料庫驅動。

## 🚀 如何安裝

1. 進入 Open WebUI 的 **Workspace** -> **Filters**。
2. 點擊 **建立過濾器** 或 **上傳**。
3. 貼上 `folder_memory_isolation.py` 的內容。
4. 點擊 **儲存**。

## 💡 為什麼需要這個？

預設情況下，Open WebUI 的記憶是全域共享的。如果你在「資料夾 A」討論程式碼，然後在「資料夾 B」進行閒聊，AI 可能會把程式碼片段帶入閒聊中，造成上下文污染。此過濾器確保每個資料夾都擁有獨立的「大腦」。

---
**Author**: linbanana  
**License**: MIT
