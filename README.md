# GarageBand Renderer

把 ABC 谱或 MIDI 交给 macOS 库乐队出声、导出 MP3，再套一层本地混音预设。整个过程在本机完成，不上传音频和乐谱。

由 Clavis 制作，以 [MIT License](LICENSE) 开源。

导出前会自动关闭 GarageBand 节拍器，避免咔哒声混进成品。

## 已知可用环境

- macOS 26
- GarageBand 10.4.13
- 简体中文界面（已实测）
- 英文界面（脚本已兼容菜单文字，但尚未在英文系统实测）

## 安装

先从 Mac App Store 安装 GarageBand，并安装 [Homebrew](https://brew.sh)。然后在终端运行：

```bash
cd garageband-renderer
chmod +x install.sh garageband
./install.sh
./garageband --doctor
```

第一次自动操作库乐队时，macOS 会要求“辅助功能”权限。把运行这个命令的终端或 AI 客户端加入：

`系统设置 → 隐私与安全性 → 辅助功能`

## 使用

```bash
# ABC 谱 → MIDI → 库乐队原声 → room 混音
./garageband examples/rusty-waltz.abc --mix room

# 直接渲染 MIDI
./garageband song.mid --mix oldrecord --name my-song

# 自定义输出目录
./garageband song.abc --out ~/Desktop/garageband-output
```

默认输出到 `~/Music/GarageBand/exports/`：

- `<名字>.mid`：中间 MIDI
- `<名字>-raw.mp3`：库乐队原声
- `<名字>.mp3`：最终混音

混音预设：`none`、`dry`、`room`、`hall`、`oldrecord`、`musicbox`。

## 安全说明

- 库乐队已经开着时，工具默认拒绝运行，以免碰到未保存工程。
- `--force-close` 会不保存关闭当前库乐队工程，只能在确认安全后使用。
- 工具不会删除或移动任何 `.band` 工程。
- 导出时使用一次性的随机文件名，并检查创建时间，避免捞到同名旧文件。
- 导出前必须找到并关闭节拍器控件；如果 GarageBand 改版导致控件无法识别，工具会报错停止，不会悄悄导出带节拍器的成品。

## 作为 Claude Code skill 使用

把整个目录复制到 `~/.claude/skills/garageband/`，运行一次 `./install.sh`。`SKILL.md` 已包含调用说明。

## 当前限制

- 只能整首导出，不能按轨单独混音。
- GarageBand 的 UI 自动化仍会受未来界面改版影响。
- GarageBand 记住的导出目录无法稳定地由脚本指定；工具使用唯一临时文件名，从常见目录找到当次新导出的文件后再移动到目标目录。

## License

MIT © 2026 Clavis
