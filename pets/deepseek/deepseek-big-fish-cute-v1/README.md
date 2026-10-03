# DeepSeek 大肥鱼（可爱版）v1

![角色预览](preview.png)

为 `192×208` 宠物尺寸重绘的大头小身体蓝发女仆鲸鱼娘。她保留白色头饰、深蓝白裙、鱼鳍耳与大鲸尾，并会浮动、眨眼、挥手和在工作时演绎“托腮思考 → 思考泡泡 → 灵光一现”。

## 安装到 Codex

在仓库根目录运行：

```bash
mkdir -p ~/.codex/pets
cp -R pets/deepseek/deepseek-big-fish-cute-v1 ~/.codex/pets/deepseek-big-fish-cute-v1
```

然后在 Codex 的“设置 → Mini 与虚拟宠物”中选择“DeepSeek 大肥鱼（可爱版）”。若列表未立即刷新，请重启 Codex。

## 包内容

| 文件 | 用途 |
| --- | --- |
| `preview.png` | GitHub 目录和 README 的角色预览。 |
| `spritesheet-preview.png` | 完整 8×11 动作与方向帧表的预览。 |
| `pet.json` | Codex 读取的宠物配置。 |
| `spritesheet.webp` | 可安装的透明 v2 精灵图集，尺寸为 `1536×2288`。 |
| `build/` | 源图、工作姿势源图和可重复构建图集的脚本。 |
| `build/poses/` | “托腮思考”和“灵光一现”两个独立动作姿势源图。 |
| `qa/` | 图集校验结果、动作帧表与方向检查产物。 |

## 预览完整帧表

![精灵表预览](spritesheet-preview.png)

## 创作与许可

角色主视觉与工作姿势以 `gpt-image-2.5-sunburst` 生成后，再由本目录 `build/build_spritesheet.py` 编排为动画帧。设计优先保证小尺寸下的轮廓、眼睛、鲸尾和动作可读性。成品图集已通过 Codex v2 尺寸、透明通道、帧位和透明像素残留校验。

本宠物是独立的非官方社区创作，与 DeepSeek 无隶属或合作关系。素材与代码以仓库的 [MIT License](../../../LICENSE) 发布。
