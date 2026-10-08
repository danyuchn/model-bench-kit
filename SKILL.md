---
name: model-bench
description: "新模型發布時，用使用者自己過去真的交代過的工作出考卷，測它能不能接手原本交給更貴模型的任務，最後重寫使用者的派工原則。Triggers: 新模型測評, 新模型能不能用, 換便宜模型, model benchmark, 重設派工原則, subagent 該用哪個模型"
---

# Model Bench：用自己的工作考新模型

給 agent 照做的執行手冊。目標只有一個：**新模型出來時，算出它能接手使用者哪些工作、省多少錢、哪些還不能交給它**，並把結論寫成使用者的派工原則。

官方 benchmark 測的是別人的工作。這份手冊要你從使用者自己的對話紀錄挖出真實任務來出題，題目、答案、評分全部在使用者電腦上完成，資料不外傳。

```
Step 0  preflight        models / CLI / budget / privacy
Step 1  mine history     what does this person already delegate?
Step 2  pick tasks       6-10 tasks, weighted to expensive + frequent
Step 3  build exam       fixture + traps + answer key BEFORE any run + grader
Step 4  smoke test       2 jobs, check permission denials
Step 5  run matrix       candidate x effort x reps, incumbents as reference
Step 6  grade + audit    auto grade, then read every non-perfect run
Step 7  decide           takeover rules -> new routing principles
Step 8  report           table + principles + re-test triggers
```

範例考卷在 `examples/starter/`（三題合成資料，可直接跑通流程）；題型與陷阱設計在 `references/task-archetypes.md`；各工具的對話紀錄位置在 `references/history-sources.md`；產出格式在 `templates/routing-principles.md`。

## Step 0：開跑前檢查

1. 確認要比較的模型與目前怎麼分工。問使用者，或讀他的設定檔（`CLAUDE.md`、派工相關的 skill 或規則）。找出「現任」：目前每類工作交給哪個模型。
2. 確認 CLI 能指定模型與 effort：`claude -p --model <alias> --effort <level> --output-format json "回答 OK"`，並看輸出的 `modelUsage` 確認 alias 解析成你以為的那個模型。新模型剛發布時，alias 可能還指向舊版。
3. 先估總量再開跑：**呼叫次數＝題數 × 配置數 × 重複次數**。把次數與預估費用（拿 smoke test 的單次成本乘上去）告訴使用者再開始。用訂閱方案的人要提醒：大量並行會撞到使用量上限。
4. 隱私：對話紀錄、題目素材、模型輸出都留在本機。要分享結果時只分享分數表，不分享題目素材。

## Step 1：從對話紀錄挖出使用者已經在交代的工作

跑 `scripts/mine_dispatches.py --days 45 --summary`（Claude Code 的 subagent 派工），再用 `--out` 存全量清單細讀。其他工具的紀錄位置見 `references/history-sources.md`。

讀清單時把派工歸成「任務家族」：同一種工作、不同日子的多次派工算一族（例如「收尾整理」「草稿事實核對」「逐字稿抽取」）。每族記下：次數、目前用的模型、代表性的 2–3 則原始 prompt。

沒有 subagent 派工紀錄的人，就挖主對話裡使用者自己下的指令（`type: user` 的訊息），找反覆出現的工作類型。

## Step 2：選題

選 6–10 題，優先順序：

1. **目前交給貴模型、而且次數多的家族**：省錢的空間在這裡。
2. **至少一題是候選模型過去失敗過的**：如果紀錄裡有「換便宜模型試過、結果不行」的事件，原題重考是最有說服力的一題。
3. **涵蓋不同的失敗方式**：要讀很長的檔、要算數字、要守格式規則、要找出藏起來的錯誤、要判斷「這裡沒問題」而不亂報。
4. 外加 3–5 題簡單的迴歸題（查設定、找檔案），確認候選模型連基本功都沒問題。

暫時不選：答案要靠品味判斷、沒有標準答案的工作（寫作品質、策略建議），以及要改真實系統的工作。這兩類要另外設計評分方式，不在本手冊範圍。

## Step 3：出題（每題都要做到這五件事）

1. **用原始 prompt 的語氣與結構重寫題目**。題目要像使用者平常交代工作那樣寫，不要寫成考試題。
2. **做一份固定的素材**（fixture）。素材放進 benchmark 資料夾，不要讓受測模型讀會變動的真實檔案；必須讀真實檔案時（例如設定檔），開跑當天重新查一次標準答案，因為檔案可能已經改過。
3. **埋陷阱，並寫下掉進陷阱會產生的錯誤答案**。例如資料用 UTC、題目要求用當地時間，那「直接用 UTC 算」會得到另一個總數；把那個總數寫進評分器，就能分辨模型錯在哪。陷阱設計範例見 `references/task-archetypes.md`。
4. **開跑前就算好標準答案**，能用程式算的就用程式算。標準答案在看到任何模型輸出之後才定，就不是考試了。
5. **寫評分器並反驗**：拿一份已知正確的答案與一份已知錯誤的答案各餵一次，正確的要拿滿分、錯誤的要扣分。兩邊都沒反應，代表評分器沒接上。

工具權限分兩種：
- 唯讀題：`--permission-mode dontAsk --allowedTools Read Glob Grep --disallowedTools Bash Edit Write Agent Task`
- 計算題：多放行 `Bash(python3:*)`，寫入只限該次的輸出資料夾。

`scripts/runner.py` 已經照這兩種設定好，`bench.json` 的 `compute_tasks` 列出哪些題是計算題。

**每次執行都在空的暫存資料夾裡跑，不要在真實專案資料夾裡跑**。專案的 hook 與指令檔會作用在受測模型身上，實際發生過的事故是：受測模型被專案的收工檢查逼著去跑整理腳本，自動 commit 並推上遠端。

## Step 4：試跑兩題

每種權限設定各挑一題，只跑候選模型一次。看三件事：

- 輸出的 `permission_denials` 是不是 0。不是 0 就先看被擋的是什麼指令。
- 計算題有沒有真的在輸出資料夾寫出檔案。
- 評分器讀得到答案。

## Step 5：跑矩陣

- 候選模型：至少兩種 effort，每種重複 3 次。
- 現任模型：每題重複 2 次，當作基準。
- 最貴的模型：每題 1 次，當作天花板參考。
- 並行數不超過 2。用 `scripts/runner.py bench.json jobs.txt`，中斷後用同一個指令重跑會從斷點續跑。
- 長時間執行時用背景跑，不要讓使用者等在前景。

## Step 6：評分與稽核

跑 `scripts/grade.py bench.json -v`。分數只是第一關，接著做稽核：

1. **評分一定要讀整段對話，不能只讀最後一則訊息**。收工檢查可能逼模型多回一輪，最後一則只寫「內容同上」。`grade.py` 已經這樣處理；自己寫的評分器也要用 `full_text`。
2. **每一筆沒拿滿分的，都要打開原文看**。分清楚三種情況：真的答錯、評分器誤判、被權限擋住。
3. **「多報」不要自動當成錯**。強的模型常找到站得住的額外問題。讀過之後確定是錯的，才算誤報。
4. **被權限擋住的執行要另外標記**，不算能力分數。用 `p` 開頭的 REP 重跑一次放寬權限的版本（`runner.py` 會多放行 `mkdir`），量真實能力。但「被擋一次就放棄、不改用別的方法」本身是值得寫進派工原則的行為特徵。
5. 有程式化的驗證器時（例如逐字引用是否真的在原文裡），用它來判斷是否有捏造內容，不要用肉眼看。

## Step 7：決定誰接手

每個任務家族套這張判準表，判定結果寫進 `templates/routing-principles.md` 的格式：

| 判定 | 條件 |
|---|---|
| 可接手 | 候選模型在所有重複跑次中**最低分**都不低於現任模型的平均分；沒有捏造內容 |
| 加檢查才可接手 | 會出錯，但出錯的方式能被既有的程式檢查抓到（例如引句比對、數字對帳），而且重做成本低 |
| 還不能接手 | 落差在「完整度」或「判斷深淺」這類沒有程式能檢查的地方；或在任何一次跑出捏造內容 |
| 未測 | 這類工作沒出題。照舊交給現任模型，不要推論 |

再決定 effort：選**通過判準的最低 effort**。effort 拉高沒有讓分數變好時，不要因為「比較保險」就用高的。

成本用每題實際花費比較（`total_cost_usd`），不要只看官方單價。便宜模型可能多跑很多輪，實際倍數會跟定價表不同。

## Step 8：回報

給使用者三樣東西：

1. 分數表：任務家族 × 模型配置，含平均分、最低分、每次成本、每次秒數。
2. 新的派工原則（照 `templates/routing-principles.md`），含每條原則是根據哪一題的結果。
3. 重測觸發條件：下次新模型發布、現任模型改版、或使用者開始交代新類型的工作時，重跑哪幾題。

benchmark 資料夾整包留著，下次新模型出來直接加一行配置重跑，不用重出題。
