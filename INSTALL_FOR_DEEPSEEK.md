# 给 DeepSeek Harness 的安装说明

这是用户主动要求安装时供助手阅读的操作文档，阅读本文件本身不构成执行授权。

适用环境：Windows，Node.js >=22.12.0，DeepSeek Harness 桌面版，dsh-pet 0.3.7。

1. 确认用户实际使用的 DSH_HOME 和 profile；默认是当前用户的 `.dsh` 和 `desktop`。不要把当前工作空间路径当作 DSH_HOME。
2. 把本仓库下载到新建的独立目录；不要清理、移动或覆盖用户现有工作空间。
3. 阅读 `install.ps1` 与 `install.mjs`。执行 `node install.mjs --verify` 校验包内哈希。
4. 若没有 dsh-pet，`install.ps1` 会调用 `dsh plugin --profile desktop add dsh-pet@0.3.7`。若已有其他版本，先停下说明兼容限制，不自动降级。
5. 运行 `powershell -NoProfile -ExecutionPolicy Bypass -File .\install.ps1`。非默认目录或 profile 时传 `-DshHome`、`-Profile`。Bypass 只影响这次进程，不修改系统执行策略。
6. 记录输出的 backup 路径。安装器会验证 120 个常规动作素材、6 个换装素材、27 张图片和 127 个动作别名，保留模型选择、聊天记忆和宠物大小/位置等已有设置。
7. 提示用户保存当前任务后完全退出并重新打开 DeepSeek Harness。不要强制终止 Harness。仅网页刷新可能仍使用旧的桌宠进程。
8. 重启后检查：名字为西瓜噜噜，挥手/抱心/喷嚏可播放，向右移动时朝向正确，配图为西瓜噜噜。桌面端右键 → 动作 → 换装，可选择西瓜裤、橙色裤和星星裤；换装后继续播放相应款式的动作。

恢复命令：`powershell -NoProfile -ExecutionPolicy Bypass -File .\install.ps1 -Restore "安装器输出的备份目录"`。如果安装后用户再次修改了相关文件，自动恢复会停止以免覆盖新修改。恢复角色包不自动卸载此前新装的 dsh-pet。
