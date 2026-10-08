# 對話紀錄在哪裡

挖題目的原料。全部是本機檔案，讀的時候只取需要的欄位，不要把整份紀錄貼進對話或傳到外部服務。

## Claude Code

- 位置：`~/.claude/projects/<專案路徑轉成的資料夾名>/<session-id>.jsonl`，一行一個事件。
- subagent 派工：`type` 為 `assistant` 的事件裡，`message.content[]` 中 `type: tool_use` 且 `name` 為 `Agent`（舊版為 `Task`）的區塊。`input` 有 `model`、`subagent_type`、`description`、`prompt`。`scripts/mine_dispatches.py` 已經做好這件事。
- 使用者自己下的指令：`type` 為 `user` 且 `message.content` 是字串的事件。
- subagent 自己的完整過程：同一個專案資料夾下的 `<session-id>/subagents/`。
- 受測模型自己的紀錄：用 `claude -p` 跑 benchmark 時，每次執行也會在 `~/.claude/projects/` 留一份，資料夾名稱由執行時的工作目錄轉換而來。評分要讀完整過程時從這裡找（`scripts/grade.py` 的 `full_text`）。

## Codex CLI

- 位置：`~/.codex/sessions/<年>/<月>/<日>/rollout-*.jsonl`。
- 工具呼叫在 `type: response_item` 的事件裡，`payload.type` 為 `function_call` 或 `custom_tool_call`，`payload.name` 是工具名。派子代理的是 `spawn_agent`（後續追問是 `send_message`、`followup_task`），參數在 `payload.arguments`。不同版本欄位可能改名，先用 `jq -r '.payload.name'` 掃一次確認再寫解析程式。
- `~/.codex/memories/` 若存在，裡面的摘要可以當線索，但不是原文，出題前要回到 session 檔確認。

## ChatGPT 或其他網頁版聊天工具

- 從設定頁申請資料匯出，解壓後的 `conversations.json` 每則對話是一棵訊息樹。
- 網頁版沒有 subagent，挖的是「使用者反覆交代的工作類型」：把使用者訊息依開頭動詞與名詞分群（例如「幫我整理…」「核對…」「改寫成…」）。

## 沒有紀錄可挖時

請使用者口述最近兩週交代給 AI 的工作，每件寫一句。你再從中挑出能做成固定素材、能算出標準答案的。

## 挖的時候要記下什麼

每個任務家族記：派工次數、目前用的模型、2–3 則代表性的原始 prompt、有沒有失敗或重做的紀錄（重派、使用者糾正、主對話接手）。有失敗紀錄的那一則，最適合拿來當題目。
