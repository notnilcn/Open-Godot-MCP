# Interactive Playtest — UI Driving Recipes

> 用 `godot_exec` + `godot_input sequence` 像真人玩家一樣操作執行中的遊戲：點按鈕、拖物品、打字。
> 確定性時鐘概念見 [Guide.md](Guide.md)；工具 API 見 [../02-Tools/Input.md](../02-Tools/Input.md)、[../02-Tools/Runtime-State.md](../02-Tools/Runtime-State.md)。

每個 MCP 工具都取 `(action, params)`。下方的 recipe 會完整寫出兩者，請照抄。

---

## 0. 原則：不要截圖找按鈕

UI 位置寫在 `.tscn` 裡。用 `godot_exec eval` 把 authored node path 解成 live 座標再注入 input。
截圖是 recipe 失敗時的 fallback、或最後的視覺驗證——永遠不是導航手段。

```gdscript
# Control → viewport-space center (always pass with coords:"viewport")
var p = (get_node("/root/MyGame/UI/PlayButton") as Control).get_global_rect().get_center()
return {"x": int(p.x), "y": int(p.y)}
# Non-Control nodes:
# (get_node("/root/MyGame/Player") as Node2D).get_global_position()
```

> **回傳 flat `{"x", "y"}` dict，不要回傳 raw `Vector2`**——Vector2 在 bridge 編碼下不可靠，會靜默 corrupt 座標。Nested dict OK，只有 raw Vector2 會掉。
> 永遠不要猜測或 hardcode 座標。

---

## 1. Session start

1. 先 `godot_health check`。`BRIDGE_NOT_CONNECTED` = editor 沒開，bridge 是跟著 editor 自動載入的——先把 editor 跑起來再重試。
2. `godot_editor_edit open_scene` 吃的是 `params: {"path": ...}`——傳 `scene` 會報 `INVALID_ARGUMENT: path required`。只有 `godot_game play` 吃 `scene`。
   `play` 永遠明確傳 scene（`res://...` 或 `"main"`），不要跑「editor 現在開著的那個」。
   等 `runtime_ready=true`（否則 poll `godot_game status`），再驗證預期的 in-world state（例如 menu hidden + player node 存在）才開始驅動 input。
3. Logs：`godot_log get` / `godot_log errors`。Eval 是 escape hatch（`find_child`、signal 列表、`get()` exports）。

---

## 2. Core primitives

### CLICK `<node_path>` — 固定兩個 calls，不要自創變化形

1. `godot_exec` `eval`（見 §0 取 center）。
2. `godot_input` `sequence`——**單一 call** 含 press + release（default `frame_delay: 1` 才是它像真人點擊的原因），X/Y 來自步驟 1：

```json
{"action": "sequence", "params": {"steps": [
  {"type": "mouse_button", "params": {"button": "MOUSE_BUTTON_LEFT", "pressed": true,  "position": {"x": X, "y": Y}, "coords": "viewport"}},
  {"type": "mouse_button", "params": {"button": "MOUSE_BUTTON_LEFT", "pressed": false, "position": {"x": X, "y": Y}, "coords": "viewport"}}
]}}
```

不要拆成兩個獨立的 press / release calls。

### HOVER `<node_path>`

`godot_input mouse_motion` 到 rect center → **下一個 call** 再 eval `get_tree().root.gui_get_hovered_control()` 確認是目標（或其 child）。
永遠不要用 `get_viewport().get_mouse_position()` 驗證——它讀的是 OS 真實游標。

### DRAG `<pathA>` → `<pathB>`

1. `mouse_motion` 到 A center。
2. `mouse_button` 左鍵 **press** 在 A。
3. `mouse_motion` 到 B center，**帶 `button_mask: ["MOUSE_BUTTON_LEFT"]`**——mask 才是跨過引擎 drag-start threshold 的關鍵。用 eval `get_tree().root.gui_is_dragging()` 驗證。
4. `mouse_button` 左鍵 **release** 在 B。

### PRESS `<key>`

`godot_input key` press + release。Key 用 plain names（`Tab`、`E`、`Up`）——**不是** Godot enum 常數（`KEY_TAB` 會靜默 no-op）。

### HOLD `<key>`

`godot_input key` `pressed: true` → 本地 sleep（遊戲繼續用按住的 key 模擬）→ `pressed: false`。Rate-based 操作（走路、arcball pitch）都用這個。Landing state 一定要重讀驗證（closed-loop），不要假設 duration = 精確角度/距離。

### TYPE `<node_path> <text>`

Eval `get_node("<node_path>").grab_focus()` → `godot_input text`。

---

## 3. Standing rules

- **Multi-instance**：`godot_game instances` 列出 PIE instances（pid、launch args、ready）。每個 runtime 工具（`godot_exec`/`godot_input`/`godot_runtime_state`/`godot_screenshot`/`godot_game_time`/`godot_profiler`）預設打 instance 1，加 `"instance": N` 才打另一個。Instances 各自獨立 scene tree——sequentially 驅動，不要同 batch 並發打兩個。`stop`/`play` 後 pid 會變，assumed state（camera pose、player position）要重建。
- **Pid stamp**：verification eval 帶 `"pid": OS.get_process_id()`，對照 `godot_game instances`。兩個長一樣的 lobby 會讓 misrouted call 看起來成功，pid 不會說謊。最小化的 window 顯示 stale preview——注入的 input 打的是 in-engine viewport，跟 window state 無關。
- **Closed-loop**：frame rate 會飄，key 按 N 秒走多遠不可預測——每次 drive 後都把 state 讀回來。
- **Sequence timeout = 查 frame loop，不是查 plugin**：`input sequence` 會在 steps 之間 await `process_frame`，所以 loop stalled 時 sequence timeout、但 plain `eval` 還活著（debugger channel 是分開服務的）。診斷：讀兩次 `Engine.get_process_frames()`——沒前進就是 stalled。解法只有 `godot_game stop` + `play`。`frame_delay: 0` 跳過 await，但 press+release 落在同一 frame、click 不會註冊——只能當 probe。
- **Eval 禁止 `for`/`while`**——會 timeout。用 `map`/`filter` 或單節點存取。Broad traversal 也會超時（幾百個節點的 `find_children("*", "MeshInstance3D", true, false)` 曾超過 15s）——scope 到最小 subtree，結果用 `slice(0, N)`。
- **Eval TIMEOUT 通常 = body errored，不是 bridge hung**：拼錯的 function 會回 15s timeout，真正的 error 在 `godot_log errors` 裡。每次 timeout 先查 log 再重試。也不要在 eval 碰 `MeshInstance3D.mesh`（render-thread contention 會 stall）；偏好 transforms、`is_position_in_frustum`、physics raycast、screenshots。
- **C# 節點屬性**：GDScript eval 裡直接 `rig.PitchDegrees` 會失敗，用 `rig.get("PitchDegrees")` / `rig.set("PitchDegrees", v)`。
- **Input 下一幀才派發**——hover/drag/visibility 永遠下一個 call 再查，同一個 call 查不到。
- **Node 名含空格**（如 `"Weapon - 0"`）——`get_node()` 裡要 quote。同名 node 可能在多個 container 各有一份——永遠用 full container path，不要 bare recursive `find_child`。

---

## 4. When a recipe fails

依序查：(1) 目標 + 整條 parent chain 的 `visible`（menu 開/關狀態）；(2) 同一點再 motion 一次後 `gui_get_hovered_control()` 看 click 有沒有落點；(3) `godot_log errors` 看 reducer/script errors；(4) 最後才 `godot_screenshot game` 看畫面到底長什麼樣。

---

## 5. Advanced：3D 歸因（通用模式）

- **Camera pose**：讀 Camera3D `global_transform.origin` + viewport center 的 `project_ray_normal()`——center ray 是 camera 在幹嘛的 source of truth。Rate-based HOLD 轉 pitch 會因 MCP round-trip latency overshoot；能用 `set()` 精確設定的 rig 優先用 `set()`，每次 drive 後重讀 pose。
- ** visibility toggle 歸因**：同 pose 連拍，toggle 單一變數（`camera.projection` ORTHOGONAL↔PERSECTIVE、或 render pipeline 的 master flag），用 PIL 比對（control region pixel-identical = no change）。A-B pair 要求 LIVE loop——先確認 `Engine.get_process_frames()` 在前進，否則會拿到 byte-identical stale frames。每次 toggle 後要 restore。
- **Physics raycast 歸因**（screenshot pixel 模稜兩可時，拿 camera 自己的 ray 打穿那個 pixel 看打到什麼）：

```gdscript
var cam = get_node("/root/MyGame/World/Camera3D")
var o = cam.project_ray_origin(Vector2(X, Y))
var d = cam.project_ray_normal(Vector2(X, Y))
var hit = cam.get_world_3d().direct_space_state.intersect_ray(PhysicsRayQueryParameters3D.create(o, o + d * 5000.0))
return {"pid": OS.get_process_id(), "oy": o.y, "hit": hit}
```

Visual-only 幾何（水面、天空、某些特效層）通常沒有 collision——ray 穿過去打到 nothing 不代表那裡沒畫東西。最強形式是跟 visibility toggle 合併：藏起 suspect node 後 suspect pixels pixel-identical = 該 node 對這些 pixels 零貢獻。一個 eval body 可放多條 sequential statements（只有 `for`/`while` 會 timeout）。

---

## 6. 本檔不收的東西

專案專屬 UI map（哪個按鈕在 `/root/.../哪個Panel`）屬於你的專案文件，不屬於 MCP——請在自己 repo 維護一份 node-path 表，本檔的 `/root/MyGame/...` 只是 placeholder。
