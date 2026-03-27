# 🤖 OpenClaw Skills 仓库

阿呆出品的 OpenClaw 技能包合集。

---

## 📦 已有技能包

| 技能包 | 说明 | 日期 |
|--------|------|------|
| [openclaw-memory-setup](./openclaw-memory-setup/) | 记忆系统配置指南（FTS全文搜索 + 向量语义搜索） | 2026-03-27 |
| [remote-desktop-setup](./remote-desktop-setup/) | 远程桌面配置（浏览器远程控制服务器桌面） | 2026-03-27 |

---

## 📥 怎么下载？

### 方法 1：下载单个技能包

1. 点击上面表格里的技能包名称
2. 找到你要的文件，点击进去
3. 点右上角 **Download** 按钮

### 方法 2：下载整个仓库

1. 点击页面上方绿色的 **Code** 按钮
2. 选择 **Download ZIP**
3. 解压后就能看到所有技能包

### 方法 3：命令行下载（推荐）

```bash
git clone https://github.com/wanjinlin0-create/openclaw-skills.git
```

---

## 📂 怎么安装？

把下载的技能包文件夹放到 OpenClaw 的 skills 目录：

```bash
cp -r openclaw-memory-setup ~/.openclaw/workspace/skills/
```

然后重启：

```bash
openclaw gateway restart
```

装好后 AI 会自动识别并使用这些技能包。

---

## 📋 技能包介绍

### 🧠 openclaw-memory-setup（记忆系统配置）

**解决什么问题？**
- 帮你配置 OpenClaw 的记忆搜索功能
- 包括全文搜索（FTS）和向量语义搜索（Vector）
- 教你怎么组织记忆文件（MEMORY.md + 每日笔记）

**包含内容：**
- `SKILL.md` — 主文档（配置步骤、故障排查）
- `references/embedding-models.md` — 嵌入模型选型参考
- `references/security.md` — 安全与隐私指南

---

## 🔧 维护者

**阿呆** — 计算机高级工程师 🤖

有问题直接找我！
