# Input Tools

> `godot_input` — 向執行中的遊戲注入輸入。

> 詳細工作流見 [../03-Realtime-Testing/Guide.md](../03-Realtime-Testing/Guide.md)。
> 互動式 UI 操作（CLICK/HOVER/DRAG/PRESS/HOLD/TYPE 完整 recipes）見 [../03-Realtime-Testing/Interactive-Playtest.md](../03-Realtime-Testing/Interactive-Playtest.md)。

---

## `godot_input`（寫入，gated）

| Action | 參數 | 回傳 | 說明 |
|--------|------|------|------|
| `action` | `action, pressed, strength?` | `{ok}` | InputMap action（`strength` 0.0-1.0，類比按壓程度） |
| `key` | `key, pressed, modifiers?` | `{ok}` | 鍵盤按鍵 |
| `mouse_button` | `button, position, pressed, coords?` | `{ok}` | 滑鼠按鈕 |
| `mouse_motion` | `position? \| delta, button_mask?, coords?` | `{ok}` | 滑鼠移動。給 `position` 為絕對移動，給 `delta` 為相對移動。`button_mask?` 是移動時按住的滑鼠按鈕清單（字串陣列，同 `button` 格式，如 `["MOUSE_BUTTON_LEFT"]` 表示拖曳），不指定時為無按鈕 |
| `joypad` | `device, control, index, value?` | `{ok}` | 手把按鈕/搖桿 |
| `text` | `text` | `{ok}` | 文字輸入（unicode） |
| `sequence` | `steps: [{type, ...params, frame_delay?}], frame_delay?` | `{ok}` | 複合輸入序列。`steps` 每個元素是 `{type, params, frame_delay?}`——`type` 對應上表 action 名稱（`mouse_button`/`mouse_motion`/`key`/`action`/`text`/`joypad`），`params` 即該 action 的參數。CLICK 必須用**單一** `sequence` 包 press+release（default `frame_delay: 1` 才是它像真人點擊的原因），不要拆成兩次 calls |

> **CLICK/DRAG 固定寫法**（完整版見 Interactive-Playtest.md §2）：
> - CLICK：先 `godot_exec eval` 取 `(node as Control).get_global_rect().get_center()` → flat `{"x","y"}`，再**一個** `sequence` press+release，同座標 + `coords: "viewport"`。
> - DRAG：`mouse_motion` 到起點 → `mouse_button` 按下 → `mouse_motion` 帶 `button_mask: ["MOUSE_BUTTON_LEFT"]` 到終點（跨過 drag threshold 的關鍵）→ `mouse_button` 放開；用 `gui_is_dragging()` 驗證。
> - HOVER 後用 `get_tree().root.gui_get_hovered_control()` 驗證（下一個 call 再查，input 下一幀才派發）。

> **拖曳注意**：只給 `position` 的絕對移動會自動合成 `relative`（引擎靠累積 `relative` 超過拖曳門檻才啟動拖曳；若 `relative` 為 0 拖曳永不開始）。拖曳流程：`mouse_motion` 到起點 → `mouse_button` 按下 → `mouse_motion` 帶 `button_mask` 到終點 → `mouse_button` 放開。另外，root viewport 的 `get_mouse_position()` 讀的是 OS 真實游標，永遠不反映注入位置——驗證注入請用 `gui_get_hovered_control()`。注入事件在下一帧才派發（accumulated input），hover/拖曳狀態要在下一次呼叫再查。

> **`text`/wheel/flush 注意**：
> - `godot_input text` 目前損壞（同一個 `InputEventKey` 物件在同 frame 內 press+release，事件被丟棄、欄位留空並記 error）；`godot_input key` 不帶 `unicode`，`LineEdit` 會忽略。請用 eval push 全新的 `InputEventKey`（每字元 down+up），或設 `field.text` + emit `text_changed` 後再用真實滑鼠點 OK。
> - 沒有 wheel action：用 eval push `InputEventMouseButton`（`WHEEL_UP`/`WHEEL_DOWN`，`pressed=true`、`factor=1.0`、`position` 設好）過 viewport。
> - 離散 press/release 後，在同一個 eval 內 `Input.flush_buffered_events()` 並斷言目標狀態——未 flush 的輸入會留在 accumulated buffer，看起來像壞掉的 UI。
> - menu 淡入期間不要在同一個 `execute` 內連點：後續 click 可能 miss（回 `ok` 不代表命中），一次只送一個 click 並 probe 目標節點。

> **世界輸入 / 時序注意**：
> - 世界放置/破壞只能走 `godot_input`（真實游標）；合成 `get_viewport().push_input()` 對 Control 點擊有效，但世界放置路徑不吃。
> - 注入世界輸入前先確認沒有 dialog 殘留在世界畫面上（resume 後常見）、sim 不在 paused（讀 paused 旗標/dialog 節點，不要只看畫面）。
> - 目標 rect 要在 layout 落定後再解——下一個 call 再讀並 poll 到數值重複（menu 等容器的 rows 在啟動初期會移位）。
> - 相機/畫布 transform 在 frame 結尾才更新：`tile_to_screen`/`screen_to_tile` 要在移動相機後的**下一個** call 讀。
> - 開場/重啟後 OS 游標可能停在視窗邊緣，帶 edge-pan 的相機會逐幀漂移——先把游標 park 到畫面中央並重新置中（能停用相機自動平移就停用）再解世界座標。
> - hold-latched 模式可能需要 KeyUp edge 才會解除；注入的 press 沒 latch 時，改用遊戲自己的 API（`Input.push_event(...)`/`inject_key`）。
> - loading overlay 不只吃點擊，也吃鍵盤（Escape 會落在 loading 分支）——先 drain IO、等 overlay 隱藏再開 dialog。

> **參數格式**：
> - `key`：plain key 名，如 `"Tab"`、`"E"`、`"Up"`、`"Space"`——**不要**用 Godot enum 常數（`"KEY_TAB"` 會靜默 no-op）。`modifiers` 另用字串陣列表示
> - `modifiers`：字串陣列，如 `["ctrl", "shift", "alt", "meta"]`
> - `button`（mouse_button）：Godot MouseButton 常數字串，如 `"MOUSE_BUTTON_LEFT"`、`"MOUSE_BUTTON_RIGHT"`、`"MOUSE_BUTTON_WHEEL_UP"`
> - `button_mask`（mouse_motion）：字串陣列，同 `button` 格式
> - `position`（mouse_button、mouse_motion）：`{x, y}`，預設為實際視窗像素座標（見下方 §座標系統）
> - `delta`（mouse_motion）：`{x, y}`，相對移動量（像素）。未給 `position` 時才使用
> - `coords`（mouse_button、mouse_motion）：`"window"`（預設，實際視窗像素）或 `"viewport"`（設計解析度空間，會自動用 viewport transform 換算）

> **精確時序**：輸入可包在 `godot_game_time step` 的 `inputs` 參數內，在特定時間切片注入。

> **`joypad` 參數**：
> - `device`：手把裝置 ID（整數，0 = 第一個手把）
> - `control`：`"button"` 或 `"axis"`
> - `index`：按鈕索引（如 `"JOY_BUTTON_A"`）或軸索引（如 `"JOY_AXIS_LEFT_X"`）
> - `value`（僅 axis）：軸值，`-1.0` 到 `1.0`

## 座標系統

> **滑鼠座標 = 實際視窗像素座標，不是設計解析度座標**。

`mouse_button` 的 `position` 和 `mouse_motion` 的 `delta` 都是**實際遊戲視窗的像素座標**（透過 `Input.parse_input_event()` 注入，使用 viewport 實際尺寸）。這與 Godot 專案設定的「設計解析度」（`display/window/size/viewport_width/height`）可能不同。

**常見陷阱**：
- 專案設計解析度 1920×1080，但遊戲視窗以 1280×720 開啟
- AI 假設 1920×1080 座標系，發送 `position={x: 960, y: 540}`（以為是畫面中心）
- 實際視窗只有 1280×720，座標 (960, 540) 偏右下，不是中心

**正確做法（推薦）**：直接加 `coords: "viewport"`，把節點座標原封不動送進來，由 runtime 自行換算：

```jsonc
// Button.get_global_rect().get_center() == (1115, 19)，即使視窗被 stretch 也會命中
{"action": "mouse_button", "params": {
  "button": "MOUSE_BUTTON_LEFT", "position": {"x": 1115, "y": 19},
  "pressed": true, "coords": "viewport"}}
```

**手動換算做法**：
1. 先呼叫 `godot_game status` 取得三個欄位：
   - `viewport_size` — 設計解析度空間（節點 rect、`godot_runtime_state` 都用這個）
   - `window_size` — 實際視窗像素（`coords: "window"` 的滑鼠座標空間）
   - `input_scale` — 兩者的換算比例
2. `window_pos = viewport_pos * input_scale`
3. 或用 `godot_exec eval` 轉換：
   ```gdscript
   # 設計解析度座標 → 實際視窗座標
   var design_pos = Vector2(960, 540)
   var actual_pos = get_viewport().get_screen_transform() * design_pos
   ```

> **stretch mode 影響**：若遊戲使用 `canvas_items` 或 `viewport` stretch mode，2D 畫面會縮放以填滿視窗。節點的 `position` 屬性是**遊戲世界座標**（設計解析度空間），但 `coords: "window"` 的滑鼠輸入是**實際視窗像素座標**——兩者座標系不同。用 `godot_runtime_state inspect` 讀到的 `position` 不能直接當 `"window"` 座標用；請改加 `coords: "viewport"`，或先透過 viewport transform 轉換。
>
> **失敗是靜默的**：座標算錯時點擊只是落在按鈕外，`godot_input` 仍回傳 `{"ok": true}`。驗證點擊是否真的生效，要另外讀狀態（例如用 `godot_runtime_state inspect` 檢查 `visible` 有沒有翻轉），不能只看回傳值。
