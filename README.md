# 西瓜噜噜桌宠 🍉

住进 DeepSeek Harness 的黄色小伙伴：头顶小橙子，穿着西瓜短裤，陪你工作、挥手、走路和发呆。

![西瓜噜噜](docs/character.png)

**40 组独立动作 · 27 张配图 · 透明背景 · 可备份恢复**

[观看动作预览](docs/preview.mp4) · [给 DeepSeek 的安装说明](INSTALL_FOR_DEEPSEEK.md) · [动作清单](config/actions.json)

## 给 DeepSeek 发送什么

把下面这段话发送给 **DeepSeek Harness 桌面版的智能体**（需要能操作本机文件和终端）：

> 请帮我安装“西瓜噜噜桌宠”：https://github.com/Dinosaur-Marr/xigua-lulu-desktop-pet 。先阅读仓库的 README.md 和 INSTALL_FOR_DEEPSEEK.md，下载到一个新的独立目录，校验素材后运行安装脚本。识别我实际使用的 DSH_HOME 和 profile，安装前保留备份，不要删除、移动或清理我的任何工作空间。保留我的模型设置、聊天记忆和桌宠大小位置。完成后告诉我备份路径，并提醒我保存任务后重启 DeepSeek Harness。

普通 DeepSeek 网页聊天不能直接安装本机插件；这段话需要发送给具备本机操作能力的 Harness。

## 安装

支持 Windows + DeepSeek Harness 桌面版；需要 Node.js **22.12.0 或更高**，以及可用的 `dsh` 命令。角色包适配 **dsh-pet 0.3.7**。其他版本会停止安装，不自动降级。

在下载、解压后的项目目录运行：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\install.ps1
```

缺少 dsh-pet 时脚本调用其正式安装命令 `dsh plugin --profile desktop add dsh-pet@0.3.7`，随后安装角色包。已安装的其他版本不会被覆盖。依赖安装需要网络。

安装完成后，**保存当前任务，完全退出并重新打开 DeepSeek Harness**。脚本不会强制结束应用。素材从旧进程缓存中更新可能需要完整重启。

如果你的 Harness 使用自定义目录或 profile：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\install.ps1 -DshHome "你的 DSH_HOME 目录" -Profile desktop
```

只检查、不改动（需要已经安装 dsh-pet）：

```powershell
node install.mjs --verify
powershell -NoProfile -ExecutionPolicy Bypass -File .\install.ps1 -DryRun
```

## 具体改动

- 安装 40 个透明 WebM 动作；每个 5 秒、24 帧/秒、640×360。
- 通过 127 个旧/新动作别名兼容原有触发入口；**127 不代表 127 个独立动作**。
- 替换 27 张聊天/碎碎念配图为西瓜噜噜；更新名字、人设和动作分配。
- 修正桌面端和网页端的行走方向，保留裤子与腿一起运动的步态。
- 保留已有模型选择、聊天记忆、桌宠大小、位置和显示方式。首次安装默认关闭自动碎碎念和余额检查，可在设置里自行开启。

只写入选定 `DSH_HOME` 中的 `dsh-pet` 角色文件、指定 profile 的三处朝向代码，以及 `xigua-lulu-backups` 备份目录。每次安装先完成素材哈希与版本检查，再备份实际涉及的文件。不会操作用户工作空间。

## 恢复

安装结果会输出 `backup` 路径。使用该路径恢复：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\install.ps1 -Restore "安装器输出的备份目录"
```

恢复后同样要重启 Harness。如果相关文件在安装后被再次修改，脚本会停止，避免覆盖新修改。多次安装按最近一次开始逐次恢复。恢复角色包不会自动卸载 dsh-pet。

## 二次创作

安装无需生成视频。想修改动作，可编辑 `animation-src/work/` 中的 Python 动作参数，输入图层已包含在 `animation-src/` 内。

```powershell
python -m pip install -r animation-src/requirements.txt
python animation-src/render.py --action hug --output custom/hug.webm
```

需要 PATH 中有支持 `libvpx-vp9` 的 FFmpeg，或用 `FFMPEG_BINARY` 环境变量指定。渲染入口为 `animation-src/render.py`；`work/` 下旧的批处理入口保留了开发过程的目录依赖，请通过统一入口生成单个动作。新生成的视频需要重新检查透明边缘和动作，再更新校验清单，不会自动替换已安装素材。

安装器测试：`node --test tests/install.test.mjs`。包校验：`node install.mjs --verify`。

本次发布使用已检查的 40 组素材；[边缘检查报告](docs/edge-audit.json)覆盖 4,800 帧。像素检查不能保证每个动作都符合所有人的审美；目前是二维图层动画，大幅转身和复杂关节动作仍有限制。

## 来源与许可

基于 [PC2005-cloud/dsh-pet](https://github.com/PC2005-cloud/dsh-pet) 运行，感谢原作者提供桌宠框架。代码使用 MIT；素材来源与权利范围见 [NOTICE.md](NOTICE.md)。本项目不附带聊天记录、API 密钥、个人配置或本机工作空间。
