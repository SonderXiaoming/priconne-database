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
| `download` | `1`、`true`、`yes` | 直接 302 跳转到选中的数据库资产 |

示例：

```text
https://priconne-database.vercel.app/api/databases?region=jp
https://priconne-database.vercel.app/api/databases?region=tw&download=1
https://priconne-database.vercel.app/api/databases?region=cn&source=github
```

API 返回最新版本和历史版本的 Release 地址、文件名与 SHA-256。响应缓存时间为 5 分钟。

## Releases

也可以直接从 [GitHub Releases](https://github.com/SonderXiaoming/priconne-database/releases) 下载数据库。

| 区服 | 当前版本 | Release |
| --- | --- | --- |
| 国服 | `202607312107` | [`database-cn-202607312107`](https://github.com/SonderXiaoming/priconne-database/releases/tag/database-cn-202607312107) |
| 台服 | `600011` | [`database-tw-600011`](https://github.com/SonderXiaoming/priconne-database/releases/tag/database-tw-600011) |
| 日服 | `10070200` | [`database-jp-10070200`](https://github.com/SonderXiaoming/priconne-database/releases/tag/database-jp-10070200) |

使用 GitHub CLI 下载示例：

```powershell
gh release download database-jp-10070200 `
  --repo SonderXiaoming/priconne-database
```

Release 标签格式为 `database-<区服>-<版本>`，数据库文件名格式为 `master_<区服>_unhash_<版本>_<归档日期>.db`。后续 Release 会同时附带 `SHA256SUMS`。

## 当前历史资产校验

| Release | 文件 | SHA-256 |
| --- | --- | --- |
| `database-cn-202607312107` | `master_cn_unhash_202607312107_2026-08-06.db` | `2b16e9692838b32b08b072ca407869aeabce1d40e826279788d8763421f4aec9` |
| `database-jp-10070110` | `master_jp_unhash_10070110_2026-08-06.db` | `0220035ca34a9a0e93c1d46e470a6c5d40b7fef63da73c0a93c6887b0baa8482` |
| `database-jp-10070200` | `master_jp_unhash_10070200_2026-08-10.db` | `997794edcfad2bd326a622cdbd45bed031701bb1f22d49a6c881d52111bb29d3` |
| `database-tw-600009` | `master_tw_unhash_600009_2026-08-06.db` | `bd25b8a8e6109d63611822dafcff41544d248122e4a80a5f1190066362082136` |
| `database-tw-600011` | `master_tw_unhash_600011_2026-08-07.db` | `a602d5fecf55adb62ee926ab52f14d50a497f40971ef46ebbbf3b7291491da59` |

PowerShell 校验示例：

```powershell
Get-FileHash -Algorithm SHA256 .\master_jp_unhash_10070200_2026-08-10.db
```

## 使用说明

数据库使用 SQLite 格式，可用 SQLite、Python、DataGrip、DBeaver 等工具读取。游戏更新可能增加、删除或调整表结构；未能可靠识别的名称不会猜测重命名。

公开 Git 分支不保存数据库文件和数据库生产工具，只保存 API、Release 索引及说明文档。请避免高频重复请求 API 或 Release 下载地址。

游戏、数据库内容、角色、商标及其他相关素材的权利归原权利人所有。本仓库不隶属于或代表游戏运营方；内容仅用于个人学习、研究与资料保存，请勿用于商业用途。
