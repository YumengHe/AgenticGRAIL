# 玄银 · 太极 / Silver in Motion

这是一个真实的三维骨骼动画制作项目：Meshy 生成并绑定女性角色，生成云手风格的动作并重定向到角色，Blender 对骨架添加脚部 IK、调整动作时间，最终逐帧渲染视频。

**在线页面：<https://yumenghe.github.io/AgenticGRAIL/>**（成片、可旋转的骨架视图、制作日志与源码下载）

## 成果

- `output/taichi_final.mp4`：18 秒、1920×1080、24 fps 的 H.264 成片（无音轨）。
- `output/taichi_scene.blend`：完整 Blender 5.2 工程，包含打包材质、24 骨骼角色、432 帧动画、双脚 IK 控制器、灯光、镜头、场景。
- `output/character_web.glb`：经过采样的动画角色，可在网页中旋转、播放、查看骨架。
- `output/blender_portable.zip`：便于网页下载的完整工程副本（贴图压缩到 2K，骨架、动作、场景、灯光与镜头保持一致）；本地原工程保留 4K。
- `output/contact_sheet.jpg`：六个时间点的成片检查图。
- `assets/`：Meshy 原始几何、4K 贴图角色、绑定后的 GLB/FBX、原始动作及重定向结果。
- `logs/events.jsonl`：带 UTC 时间的制作日志、提示词、任务进度、API credit 消耗、渲染进度。
- `output/scene_report.json`、`motion_quality.json`、`video_report.json`：场景、动作约束和视频解码验证记录。
- `web/`：查看视频、交互骨架、角色、制作进度和导出日志的网页源码（Vite + React 静态站点，由 GitHub Actions 自动部署到 GitHub Pages）。

## 实际制作步骤

1. **角色重建**：使用 Meshy 7 Text to 3D，描述成年女性、轻卡通风格、黑发盘髻、黑色太极服和长裤、银色盘扣及配饰。要求 A-pose，目标约 45,000 三角面。生成结果为 45,830 面。
2. **材质**：Refine 生成 4K PBR 贴图，固定黑色衣裤与银色细节。原始材质保留在 Blender 中，网页 GLB 使用 2K JPEG 压缩副本。
3. **骨架**：Meshy 自动绑定为 24 根骨骼，角色目标身高 1.68 m。导入时删除附带的辅助球体，修正骨骼显示长度的厘米/米比例问题，保留蒙皮和骨骼方向。
4. **动作**：Meshy Text to Motion Prime 生成 10 秒云手风格动作，要求缓慢重心转移、屈膝、圆弧手势、无跳跃或快拳。Animation API 将其重定向到本角色。
5. **控制骨架**：在 Blender 中逐帧读取关节旋转、位置和缩放，重采样为 432 帧 / 18 秒。给双踝建立可编辑目标，腿部使用两骨 IK，脚掌使用世界空间旋转约束，改善原始动作中的悬空和滑动。上半身保留生成动作。没有使用视频贴图伪装三维动作。
6. **场景与渲染**：浅银色圆形练功台、圆形浮雕背景、四盏柔光灯、缓慢移动的摄影机；Cycles + RTX 5090 OptiX，48 samples，AgX 和去噪。先渲染六张低分辨率检查图，修正脚部问题后再渲染全片。
7. **编码与归档**：FFmpeg 将 432 张 PNG 编码为 H.264 / yuv420p / faststart MP4，重新解码检查全部帧。网站只复制明确列出的成片、模型、说明、脚本和脱敏日志。

## 费用记录

本次 Meshy 调用共使用 **48 credits**：几何 20、材质 10、绑定 5、动作生成 10、动作重定向 3。调用前余额 4,840，完成后 4,792。重新运行脚本时会复用保存在本地的任务 ID，避免重复提交。

## 如何复现

需要 Blender 5.2、Python 3（Pillow、NumPy、imageio-ffmpeg）以及 Node.js / pnpm。

```powershell
python scripts/meshy_pipeline.py
blender -b --python scripts/build_scene.py -- --preview
blender -b output/taichi_scene.blend --python scripts/verify_motion.py
blender -b output/taichi_scene.blend --python scripts/render_frames.py
python scripts/encode_video.py
python scripts/sync_web.py
cd web
pnpm install
pnpm dev          # 本地预览 http://localhost:5173
pnpm build        # 输出静态站点到 web/dist
```

推送到 `main` 分支后，`.github/workflows/deploy-pages.yml` 会在 GitHub Actions 中执行 `pnpm build`（`VITE_BASE=/AgenticGRAIL/`）并发布到 GitHub Pages。网页里的媒体、数据与源码副本来自 `scripts/sync_web.py`，改动 `output/` 或 `logs/` 后先运行它再提交 `web/public/`。

当前机器的程序路径保存在 `scripts/run_local.ps1`。`scripts/render_frames.py` 会跳过已经存在的完整图片；修改场景后应将旧 `output/frames/` 改名保存，再重新渲染，以免混用旧帧。

`.env` 仅在本地由 Meshy 脚本读取；密钥、带签名的临时素材链接和完整 API 响应位于忽略文件中，不进入网页。`logs/private/` 用于断点恢复，不应发布。网页没有调用 Meshy 的权限，也不会产生额外 credits 消耗。

## 编辑骨骼

在 Blender 打开工程，选择 `target_character` 后进入 Pose Mode。动作是 `TAICHI_CloudHands_18s_Baked`。`CTRL_Left_Ankle` 与 `CTRL_Right_Ankle` 是脚部目标。移动这些空物体可以改变脚的位置；修改腿部 IK 或脚掌旋转约束可调整接触方式。动画曲线保持可编辑。

## 范围与限制

这是由 AI 生成并经过骨架修正的太极风格短片，不是某一门派标准套路的动作捕捉。骨架没有单独的手指关节，手部姿态和袖口变形属于简化效果；衣服与头发随蒙皮运动，未做独立布料或发丝模拟。没有生成参考视频，也没有添加音乐。

## 官方接口资料

- [Meshy Text to 3D](https://docs.meshy.ai/en/api/text-to-3d)
- [Meshy Rigging](https://docs.meshy.ai/en/api/rigging)
- [Meshy Text to Motion](https://docs.meshy.ai/en/api/text-to-motion)
- [Meshy Animation](https://docs.meshy.ai/en/api/animation)
