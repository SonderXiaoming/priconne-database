# Priconne Database API & Releases

[pcr.cialloworld.com](https://pcr.cialloworld.com) 是本项目的主要对外地址，提供《超异域公主连结☆Re:Dive》国服、台服和日服的 SQLite 数据库查询和下载。也可以在 [GitHub Releases](https://github.com/SonderXiaoming/priconne-database/releases) 找到数据库文件。

## API

用 GET 请求 [`https://pcr.cialloworld.com/api/databases`](https://pcr.cialloworld.com/api/databases) 查询数据库。默认返回三个区服的 JSON。`latest` 按区服列出符合条件的最新条目，`history` 列出所有匹配的版本。例如，日服最新版本的下载地址是 `latest.jp.url`。

| 参数 | 可选值 | 说明 |
| --- | --- | --- |
| `region` | `cn`、`tw`、`jp` | 只返回指定区服 |
| `version` | 数据库版本号 | 只返回指定版本 |
| `source` | `auto`、`github`、`proxy` | 默认 `auto`，中国大陆请求使用代理。也可以手动指定 GitHub 或代理 |
| `compression` | `none`、`br` | 默认返回原始 `.db` 的下载信息。`br` 对应 Brotli 压缩的 `.db.br` |
| `download` | `1`、`true`、`yes` | 直接 302 跳转到选中的数据库资产 |

### 常用链接

- [查日服最新和历史版本](https://pcr.cialloworld.com/api/databases?region=jp)
- [查日服指定版本 `10070300`](https://pcr.cialloworld.com/api/databases?region=jp&version=10070300)
- 查国服下载地址，可指定 [GitHub](https://pcr.cialloworld.com/api/databases?region=cn&source=github) 或 [代理](https://pcr.cialloworld.com/api/databases?region=cn&source=proxy)
- [查日服 Brotli 下载地址](https://pcr.cialloworld.com/api/databases?region=jp&compression=br)
- [直接下载台服 `.db`](https://pcr.cialloworld.com/api/databases?region=tw&download=1)
- [直接下载日服 `.db.br`](https://pcr.cialloworld.com/api/databases?region=jp&compression=br&download=1)

查询结果包含下载地址、文件名和原始 `.db` 的 SHA-256。有 Brotli 文件的版本也会提供 `br_url`。指定 `compression=br` 后，结果只列出有压缩文件的版本，`url`、`urls` 和 `download_filename` 都对应 `.db.br`。

查询响应缓存 5 分钟。加上 `download=1` 会跳转到文件，默认是 `.db`，搭配 `compression=br` 则跳转到 `.db.br`。

同一个 API 也可以通过 [Vercel 域名](https://priconne-database.vercel.app/api/databases) 访问。

## Releases

进入对应版本的 Release，在下载列表里选 `.db` 或 `.db.br`。下面是三个区服的下载示例，最新版本可通过上面的 API 查询。

| 区服 | 版本示例 | Release |
| --- | --- | --- |
| 国服 | `202608131846` | [`database-cn-202608131846`](https://github.com/SonderXiaoming/priconne-database/releases/tag/database-cn-202608131846) |
| 台服 | `600015` | [`database-tw-600015`](https://github.com/SonderXiaoming/priconne-database/releases/tag/database-tw-600015) |
| 日服 | `10070300` | [`database-jp-10070300`](https://github.com/SonderXiaoming/priconne-database/releases/tag/database-jp-10070300) |

例如，用 GitHub CLI 下载上表里的日服压缩包。

```powershell
gh release download database-jp-10070300 `
  --repo SonderXiaoming/priconne-database `
  --pattern "*.db.br"
```

Release 标签形如 `database-<区服>-<版本>`。数据库文件名形如 `master_<区服>_unhash_<版本>_<归档日期>.db`，压缩版会在文件名末尾加上 `.br`。每个 Release 都附有 `SHA256SUMS`。

## 下载 Brotli 压缩数据库

如果下载的是 `.db.br`，先用 `brotli` 解压，再校验 `.db` 文件的 SHA-256。下面的 PowerShell 示例会获取 API 返回的最新日服 Brotli 条目并完成这些步骤。

```powershell
$entry = (Invoke-RestMethod `
  "https://pcr.cialloworld.com/api/databases?region=jp&compression=br").latest.jp

$compressed = $entry.download_filename
Invoke-WebRequest -Uri $entry.url -OutFile $compressed
brotli --decompress --output $entry.filename $compressed

$actual = (Get-FileHash -Algorithm SHA256 $entry.filename).Hash.ToLowerInvariant()
if ($actual -ne $entry.sha256) {
  throw "数据库 SHA-256 校验失败"
}
```

早期 Release 可能只提供原始 `.db`，下载地址可从 `url` 获取。

## 历史版本的 SHA-256

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

例如，在 PowerShell 里计算数据库文件的 SHA-256。

```powershell
Get-FileHash -Algorithm SHA256 .\master_jp_unhash_10070300_2026-08-15.db
```

## 使用说明

下载后的 `.db` 可以用 Python 的 `sqlite3`、DataGrip 或 DBeaver 打开。游戏更新可能会调整表结构，暂时无法确认的表名和字段名会保留原样。

仓库里保存 API、Release 索引和说明。用脚本查询时，建议缓存结果，避免频繁重复请求。

这是独立维护的资料库，内容仅供个人学习、研究和资料保存，请勿用于商业用途。游戏、数据库内容、角色、商标及其他相关素材的权利归原权利人所有。
