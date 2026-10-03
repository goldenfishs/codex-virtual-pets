# Codex Virtual Pets

一个面向 Codex 桌面版的开源虚拟宠物合集。每个宠物按主题与版本分别存放，进入对应目录即可预览形象、查看说明并安装。

## 当前目录

| 分类 | 版本 | 预览 | 说明 |
| --- | --- | --- | --- |
| [DeepSeek（社区创作，非官方）](pets/deepseek/) | [大肥鱼（可爱版）v1](pets/deepseek/deepseek-big-fish-cute-v1/) | ![大肥鱼（可爱版）v1](pets/deepseek/deepseek-big-fish-cute-v1/preview.png) | 原创蓝青小河豚，带完整动画与鼠标注视方向。 |

## 安装

1. 下载或克隆本仓库。
2. 从 `pets/<分类>/<版本>/` 选择一个宠物目录。
3. 将该目录整体复制到 `~/.codex/pets/<宠物 id>/`。例如：

   ```bash
   mkdir -p ~/.codex/pets
   cp -R pets/deepseek/deepseek-big-fish-cute-v1 ~/.codex/pets/deepseek-big-fish-cute-v1
   ```

4. 在 Codex 的“设置 → Mini 与虚拟宠物”中选择该宠物；必要时重启 Codex。

## 目录约定

```text
pets/
  <category>/
    <pet-version>/
      preview.png              # GitHub 的角色预览图
      spritesheet-preview.png  # 完整帧表预览图
      pet.json                 # Codex 宠物清单
      spritesheet.webp         # 可安装的 v2 动画图集
      README.md                # 该版本的说明与安装步骤
```

宠物图集遵循 Codex v2 的 `1536×2288`、8 列 × 11 行精灵表格式，并在 `pet.json` 中声明 `spriteVersionNumber: 2`。

## 贡献

新增宠物请新建 `pets/<category>/<pet-version>/`，不要覆盖已有版本。每个提交应包含可预览的 `preview.png`、可安装的 `pet.json` 和 `spritesheet.webp`，并确保精灵表是透明背景、尺寸正确、动作帧完整。

请只提交拥有使用权的原创素材，不要提交第三方角色、商标标志或未经授权的图片。分类名称仅用于检索与社区创作描述，不代表官方合作或认可。

## License

仓库内容采用 [MIT License](LICENSE)。DeepSeek 是其权利人的商标；本仓库是独立的非官方社区创作，与 DeepSeek 没有隶属或合作关系。
