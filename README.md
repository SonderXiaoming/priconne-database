# Priconne Database API & Releases

本仓库公开提供《超异域公主连结☆Re:Dive》国服、台服与日服的可读 SQLite 数据库 Release，以及用于查询版本和获取下载地址的轻量 API。

数据库可用于个人学习、资料研究、数据分析和开发交流。数据库生成、下载、解密、名称恢复、彩虹表及自动化生产代码不在本公开仓库中提供。

## API

API 地址：[`https://priconne-database.vercel.app/api/databases`](https://priconne-database.vercel.app/api/databases)

常用参数：

| 参数 | 可选值 | 说明 |
| --- | --- | --- |
| `region` | `cn`、`tw`、`jp` | 只返回指定区服 |
| `version` | 数据库版本号 | 只返回指定版本 |
| `source` | `auto`、`github`、`proxy` | 下载来源；`auto` 会对中国大陆请求使用代理地址 |
| `compression` | `none`、`br` | 下载格式；`none` 为原始 `.db`，`br` 为 Brotli 压缩的 `.db.br` |
| `download` | `1`、`true`、`yes` | 直接 302 跳转到选中的数据库资产 |

示例：

```text
https://priconne-database.vercel.app/api/databases?region=jp
https://priconne-database.vercel.app/api/databases?region=tw&download=1
https://priconne-database.vercel.app/api/databases?region=cn&source=github
https://priconne-database.vercel.app/api/databases?region=jp&compression=br
https://priconne-database.vercel.app/api/databases?region=jp&compression=br&download=1
```

API 返回最新版本和历史版本的 Release 地址、文件名与 SHA-256。提供 Brotli 压缩资产的版本还会返回可选字段 `br_url`。不传 `compression` 时，`download=1` 下载原始 `.db`；指定 `compression=br` 后，响应中的 `url`、`urls` 和 `download_filename` 会指向 `.db.br`，与 `download=1` 组合即可直接下载压缩文件。没有 Brotli 资产的旧版本不会出现在 `compression=br` 的结果中。响应缓存时间为 5 分钟。

## Releases

也可以直接从 [GitHub Releases](https://github.com/SonderXiaoming/priconne-database/releases) 下载数据库。

| 区服 | 当前版本 | Release |
| --- | --- | --- |
| 国服 | `202608131846` | [`database-cn-202608131846`](https://github.com/SonderXiaoming/priconne-database/releases/tag/database-cn-202608131846) |
| 台服 | `600015` | [`database-tw-600015`](https://github.com/SonderXiaoming/priconne-database/releases/tag/database-tw-600015) |
| 日服 | `10070300` | [`database-jp-10070300`](https://github.com/SonderXiaoming/priconne-database/releases/tag/database-jp-10070300) |

使用 GitHub CLI 下载示例：

```powershell
gh release download database-jp-10070300 `
  --repo SonderXiaoming/priconne-database `
  --pattern "*.db.br"
```

Release 标签格式为 `database-<区服>-<版本>`。未压缩数据库文件名格式为 `master_<区服>_unhash_<版本>_<归档日期>.db`，Brotli 压缩文件会在其后追加 `.br`。Release 同时附带 `SHA256SUMS`。

## 下载 Brotli 压缩数据库

最新版本提供体积更小的 `.db.br`。以下 PowerShell 示例通过 API 获取日服最新 Brotli 条目、下载压缩文件、使用 `brotli` 命令行工具解压，并校验解压后数据库的 SHA-256：

```powershell
$entry = (Invoke-RestMethod `
  "https://priconne-database.vercel.app/api/databases?region=jp&compression=br").latest.jp

$compressed = $entry.download_filename
Invoke-WebRequest -Uri $entry.url -OutFile $compressed
brotli --decompress --output $entry.filename $compressed

$actual = (Get-FileHash -Algorithm SHA256 $entry.filename).Hash.ToLowerInvariant()
if ($actual -ne $entry.sha256) {
  throw "数据库 SHA-256 校验失败"
}
```

`br_url` 是可选字段，早期 Release 可能只有 `url`。`sha256` 始终对应解压后的 `.db` 文件，不是 `.db.br`；因此应先解压，再进行校验。

## 当前历史资产校验

| Release | 文件 | SHA-256 |
| --- | --- | --- |
| `database-cn-202607312107` | `master_cn_unhash_202607312107_2026-08-06.db` | `2b16e9692838b32b08b072ca407869aeabce1d40e826279788d8763421f4aec9` |
| `database-cn-202608131846` | `master_cn_unhash_202608131846_2026-08-14.db` | `bfb953bf0f218e22b24da6a4cede4472fbf9e67a40a3e7a1b9b0af33bf0173d2` |
| `database-jp-10070110` | `master_jp_unhash_10070110_2026-08-06.db` | `0220035ca34a9a0e93c1d46e470a6c5d40b7fef63da73c0a93c6887b0baa8482` |
| `database-jp-10070200` | `master_jp_unhash_10070200_2026-08-10.db` | `997794edcfad2bd326a622cdbd45bed031701bb1f22d49a6c881d52111bb29d3` |
| `database-jp-10070250` | `master_jp_unhash_10070250_2026-08-12.db` | `c4489bc82bb05561d461a228b5f0c38bcca237ec1d395d77b827bfa0f4b6bc3c` |
| `database-jp-10070300` | `master_jp_unhash_10070300_2026-08-15.db` | `77fd60ea1d1efcbbccc8649d644453d22c5ce5ec3cf3ecd2841aeb19ca90b2a2` |
| `database-tw-600009` | `master_tw_unhash_600009_2026-08-06.db` | `bd25b8a8e6109d63611822dafcff41544d248122e4a80a5f1190066362082136` |
| `database-tw-600011` | `master_tw_unhash_600011_2026-08-07.db` | `a602d5fecf55adb62ee926ab52f14d50a497f40971ef46ebbbf3b7291491da59` |
| `database-tw-600013` | `master_tw_unhash_600013_2026-08-11.db` | `34726a5d7d36b009d14fdb4ff2a250cc51110b537230ad7d02a3022bd3d6f03f` |
| `database-tw-600015` | `master_tw_unhash_600015_2026-08-12.db` | `b3a995a197d466d5d9eb9244c1f8320f4723beceda666750b04bbe802845d473` |

PowerShell 校验示例：

```powershell
Get-FileHash -Algorithm SHA256 .\master_jp_unhash_10070300_2026-08-15.db
```

## 使用说明

数据库使用 SQLite 格式，可用 SQLite、Python、DataGrip、DBeaver 等工具读取。游戏更新可能增加、删除或调整表结构；未能可靠识别的名称不会猜测重命名。

公开 Git 分支不保存数据库文件和数据库生产工具，只保存 API、Release 索引及说明文档。请避免高频重复请求 API 或 Release 下载地址。

游戏、数据库内容、角色、商标及其他相关素材的权利归原权利人所有。本仓库不隶属于或代表游戏运营方；内容仅用于个人学习、研究与资料保存，请勿用于商业用途。
