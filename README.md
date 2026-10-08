# model-bench-kit：用你自己的工作考新模型

[繁體中文](#繁體中文) | [English](#english)

## 繁體中文

新模型發布時，官方跑分告訴你它在別人的題目上表現如何。這個套件讓你的 AI agent 從**你自己的對話紀錄**挖出你平常在交代的工作，做成考卷、算好答案、跑分、評分，最後告訴你：**這個新模型能接手你哪些工作、省多少錢、哪些還不能交給它**，並幫你重寫派工原則。

所有題目、答案與模型輸出都留在你的電腦上。

### 開始使用

用 Claude Code 的話：

```bash
git clone https://github.com/danyuchn/model-bench-kit ~/.claude/skills/model-bench
```

然後跟 Claude Code 說：

> 用 model-bench 幫我測 <新模型> 能不能接我平常派給 <目前模型> 的工作

它會先告訴你要跑幾次、大約花多少錢，你同意才開跑。

用其他 agent（Codex、Cursor 等）：把這個 repo 的網址給它，請它讀 `SKILL.md` 照做。目前的執行腳本（`scripts/runner.py`）呼叫的是 Claude Code 的 headless 模式；其他工具要請 agent 改寫那一支的指令列。

想先看流程跑起來的樣子：

```bash
cd examples/starter
python3 ../../scripts/runner.py bench.json jobs.example.txt
python3 ../../scripts/grade.py bench.json -v
```

三題合成資料（金流對帳、公開文案紅隊、程式驗收），用 Haiku 5.5 跑一輪約 0.04 美元。

### 方法

```
your history ──> task families ──> exam (fixture + traps + answer key) ──> runs ──> grade + audit ──> routing rules
```

六條原則，每一條都是實際踩過坑才留下來的：

1. **題目從你的派工紀錄來**。優先挑「現在交給貴模型、而且次數多」的工作，那裡才有省錢空間；有「換便宜模型試過但失敗」的紀錄，原題重考最有說服力。
2. **開跑前就算好標準答案**。看到模型輸出才定答案，就不是考試了。
3. **每題都埋陷阱，並寫下掉進陷阱會得到的錯誤答案**。例如資料是 UTC、題目要求當地時間；把「直接用 UTC 算」的總數寫進評分器，就分得出模型錯在哪。
4. **在空的暫存資料夾裡、用唯讀權限跑**。在真實專案裡跑，專案的 hook 與指令檔會作用到受測模型身上。
5. **評分讀整段對話，而且每一筆沒拿滿分的都要人工打開看**。我們的評分器出包了三次，三次都是模型答對、評分器判錯。
6. **候選模型每種設定至少跑 3 次，看最低分**。平均分會把「偶爾漏掉一半」藏起來。

詳細步驟見 [SKILL.md](SKILL.md)，九種題型與陷阱設計見 [references/task-archetypes.md](references/task-archetypes.md)。

### 實測案例：Haiku 5.5（2026-10-08）

作者用這套方法，從自己 45 天、761 次的 Claude Code subagent 派工裡出了 8 題困難題、5 題迴歸題。Haiku 5.5 開 medium 與 high 各跑 3 次，Sonnet 5.5（medium）2 次，Opus 5.5（high）1 次，共 87 次。

| 題型 | Haiku 5.5 | Sonnet 5.5 | Opus 5.5 |
|---|---|---|---|
| 5 題迴歸題（查設定、找檔案） | 全對，每題約 $0.011 | — | — |
| 草稿事實核對、公開文案紅隊、死連結掃描、CSV 統計、程式找 bug、金流對帳、歸檔規則遵循（7 題） | 全對（1 次因權限被擋交白卷） | 全對 | 全對 |
| 上面 7 題合計成本／耗時 | $0.17／約 300 秒 | $1.94／約 300 秒 | $4.24／約 300 秒 |
| 62 分鐘訪談逐字稿抽取（逐字引句） | 不捏造；抽出 45–85 筆，不穩定 | 93、99 筆 | 112 筆 |

結論：能對答案的查核類工作，Haiku 5.5 可以接手，成本約為 Sonnet 的 1/11；要求完整度、又沒有程式能檢查漏了什麼的長檔抽取，還是交給 Sonnet。

這是一個人的工作樣本，**請用你自己的工作重測**，不要直接套用這張表。

### 限制

- 只測有標準答案的工作。寫作品質、策略判斷這類沒有單一答案的工作，要另外設計盲評，沒測過之前不要從這裡外推。
- 每種設定只跑 1–3 次，樣本小；結論以最低分為準，而不是平均分。
- 計算題的權限刻意鎖得很緊（只放行 python3），會放大模型「順手用別的指令」的傾向；正式派工的權限通常比較寬。
- `mine_dispatches.py` 只解析 Claude Code 的紀錄；Codex 與 ChatGPT 匯出檔的結構見 [references/history-sources.md](references/history-sources.md)，需要 agent 另寫解析。

### 檔案

```
SKILL.md                         agent 照做的 8 步手冊
references/task-archetypes.md    九種題型、陷阱設計、實測觀察
references/history-sources.md    各工具的對話紀錄在哪、怎麼挖
templates/routing-principles.md  產出的派工原則格式
scripts/mine_dispatches.py       從 Claude Code 紀錄列出所有 subagent 派工
scripts/runner.py                可續跑的 claude -p 執行器（唯讀／計算兩種權限）
scripts/grade.py                 讀整段對話的評分器框架
examples/starter/                三題合成資料範例
```

---

## English

Official benchmarks tell you how a new model does on someone else's tasks. This kit has your AI agent mine **your own conversation history** for the work you actually delegate, turn it into an exam with answer keys, run and grade it, and tell you **which of your jobs the new model can take over, how much that saves, and which it can't handle yet**. It then rewrites your delegation rules.

Questions, answers and model outputs all stay on your machine.

### Quick start

With Claude Code:

```bash
git clone https://github.com/danyuchn/model-bench-kit ~/.claude/skills/model-bench
```

Then ask: *"Use model-bench to test whether <new model> can take over the work I usually give <current model>."* It estimates the number of runs and the cost first and waits for your go-ahead.

With another agent: give it this repo and ask it to read `SKILL.md` and follow it. `scripts/runner.py` drives Claude Code's headless mode; other tools need that one command line adapted.

To see the pipeline work first, run the three synthetic examples in `examples/starter` (about $0.04 on Haiku 5.5).

### Method, in six rules

1. Questions come from your own delegation history, weighted toward work that is frequent and currently goes to an expensive model.
2. Answer keys are computed before any model runs.
3. Every question has a trap, and the grader knows the wrong answer the trap produces.
4. Runs happen in an empty scratch directory with read-only permissions.
5. Grading reads the whole transcript, and every non-perfect run is opened and read by a person. Our grader was wrong three times; each time the model was right.
6. At least three runs per candidate setting; decide on the minimum score, not the mean.

### Case study: Haiku 5.5 (2026-10-08)

Built from 761 sub-agent jobs the author delegated over 45 days: 8 hard questions plus 5 regression questions, 87 runs. On seven checking tasks (fact-checking a draft, red-teaming public copy, dead-link scan, CSV counting, finding planted bugs, payment reconciliation, rule-based filing) Haiku 5.5 scored the same as Sonnet 5.5 and Opus 5.5, at $0.17 total against $1.94 and $4.24, in about the same time. On a long transcript extraction it no longer fabricated quotes, but extracted 45–85 items across six runs against 93–99 for Sonnet and 112 for Opus. One person's sample; rerun it on your own work.

### License

MIT
