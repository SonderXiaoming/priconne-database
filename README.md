# Priconne Database API

面向开发者的《超异域公主连结☆Re:Dive》国服、台服、日服可读 SQLite 数据库与历史版本 API。项目每 6 小时检查各服官方 iOS CDN，恢复可识别的表名和字段名，将当前数据库提交到仓库，并把每个历史版本归档到 GitHub Releases。

## 公共 API

生产地址：

- 主域名：<https://pcr.cialloworld.com>
- Vercel 备用域名：<https://priconne-database.vercel.app>

API 当前无需密钥，允许浏览器跨域请求。JSON 响应使用 UTF-8，并缓存约 5 分钟。数据库文件不经过 Vercel 中转；下载接口会以 `302` 重定向到 GitHub Release 原始地址或其代理地址，适合前端、机器人、后端服务和定时同步程序使用。

默认 `source=auto`：Vercel 根据 `X-Vercel-IP-Country` 判断访问者国家，中国大陆（`CN`）使用 `gh.rem.asia` GitHub 代理，其他地区直接使用 GitHub。IP 定位不准确时，可用 `source=proxy` 或 `source=github` 显式覆盖。JSON 中始终同时提供两个地址，便于客户端自行重试。

### 快速开始

查询三服最新版和全部历史记录：

```bash
curl "https://pcr.cialloworld.com/api/databases"
```

查询日服：

```bash
curl "https://pcr.cialloworld.com/api/databases?region=jp"
```

下载日服最新版，`-L` 用于跟随 Release 重定向：

```bash
curl -L "https://pcr.cialloworld.com/api/databases?region=jp&download=1" \
  -o master_jp_unhash.db
```

强制使用 GitHub 代理或 GitHub 原始地址：

```bash
curl -L "https://pcr.cialloworld.com/api/databases?region=jp&download=1&source=proxy" \
  -o master_jp_unhash.db

curl -L "https://pcr.cialloworld.com/api/databases?region=jp&download=1&source=github" \
  -o master_jp_unhash.db
```

浏览器或 Node.js：

```js
const baseURL = "https://pcr.cialloworld.com";
const response = await fetch(`${baseURL}/api/databases?region=tw`);

if (!response.ok) {
  throw new Error(`Priconne Database API: ${response.status}`);
}

const data = await response.json();
console.log(data.latest.tw.version, data.latest.tw.url);
```

### 接口参考

所有查询都使用：

```text
GET /api/databases
```

| 参数 | 必填 | 说明 |
| --- | --- | --- |
| `region` | 否 | 区服：`cn`、`tw` 或 `jp` |
| `version` | 否 | 精确版本号。建议始终按字符串处理，避免国服长版本号精度丢失 |
| `download` | 否 | `1`、`true` 或 `yes` 时重定向到匹配数据库；默认返回 JSON |
| `source` | 否 | `auto`、`proxy` 或 `github`；默认按访问者国家自动选择 |

常用请求：

| 请求 | 用途 |
| --- | --- |
| [`/api/databases`](https://pcr.cialloworld.com/api/databases) | 三服最新版与历史记录 |
| [`?region=cn`](https://pcr.cialloworld.com/api/databases?region=cn) | 国服最新版与国服历史 |
| [`?region=tw`](https://pcr.cialloworld.com/api/databases?region=tw) | 台服最新版与台服历史 |
| [`?region=jp`](https://pcr.cialloworld.com/api/databases?region=jp) | 日服最新版与日服历史 |
| [`?region=jp&version=10070110`](https://pcr.cialloworld.com/api/databases?region=jp&version=10070110) | 查询指定日服版本 |
| [`?region=jp&download=1`](https://pcr.cialloworld.com/api/databases?region=jp&download=1) | 下载日服最新版 |
| [`?region=jp&download=1&source=proxy`](https://pcr.cialloworld.com/api/databases?region=jp&download=1&source=proxy) | 强制通过 `gh.rem.asia` 下载日服最新版 |
| [`?region=jp&download=1&source=github`](https://pcr.cialloworld.com/api/databases?region=jp&download=1&source=github) | 强制通过 GitHub 下载日服最新版 |
| [`?region=cn&version=202607312107&download=1`](https://pcr.cialloworld.com/api/databases?region=cn&version=202607312107&download=1) | 下载指定国服版本 |

JSON 响应结构：

```json
{
  "repository": "SonderXiaoming/priconne-database",
  "download_source": "github",
  "latest": {
    "jp": {
      "region": "jp",
      "version": "10070110",
      "date": "2026-08-06",
      "tag": "database-jp-10070110",
      "filename": "master_jp_unhash_10070110_2026-08-06.db",
      "source": "github",
      "url": "https://github.com/.../master_jp_unhash_10070110_2026-08-06.db",
      "urls": {
        "github": "https://github.com/.../master_jp_unhash_10070110_2026-08-06.db",
        "proxy": "https://gh.rem.asia/https://github.com/.../master_jp_unhash_10070110_2026-08-06.db"
      }
    }
  },
  "history": []
}
```

- `latest`：按区服键名返回当前筛选结果中的最新版本。
- `history`：所有符合 `region` 和 `version` 条件的归档记录。
- `date`：首次归档日期，采用 UTC 的 `YYYY-MM-DD` 格式。
- `download_source`：本次请求由自动判断或 `source` 参数选中的下载源。
- `url`：当前选中下载源的地址，保持对旧客户端兼容。
- `urls.github`：GitHub Release 原始地址。
- `urls.proxy`：在 GitHub 地址前加上 `https://gh.rem.asia/` 的代理地址。

HTTP 行为：

| 状态 | 含义 |
| --- | --- |
| `200` | 查询成功；没有匹配项时返回空的 `latest` 和 `history` |
| `204` | CORS 预检成功 |
| `302` | `download=1`，重定向到自动或显式选中的下载源 |
| `400` | `region` 或 `source` 参数无效 |
| `404` | 下载模式下没有找到匹配版本 |

## 数据库与兼容性

当前数据库：

- `data/master_cn_unhash.db`：国服 SQLite 数据库。
- `data/master_tw_unhash.db`：台服 SQLite 数据库。
- `data/master_jp_unhash.db`：日服 SQLite 数据库。
- `data/version_*.json`：各服版本、官方资源哈希和来源信息。
- `data/history.json`：API 使用的历史版本索引。

开发时请注意：

- 游戏更新可能新增、删除或调整表结构，不应假定所有版本具有完全相同的 schema。
- 自动恢复只应用有可靠证据的名称。无法确认的表或字段会保留 `v1_<hash>` 或哈希字段名，不会猜测重命名。
- 数据库通常为数十 MB，建议通过 `download=1` 或响应中的 `url` 下载后在本地缓存，不要反复从 Git 分支读取大文件。
- 历史数据库以“区服 + 版本号”作为 Release 标签，以 UTC 日期记录首次归档时间。

## 更新与名称恢复策略

| 区服 | 原始数据 | 名称恢复优先级 | 失败策略 |
| --- | --- | --- | --- |
| 国服 | 官方 iOS CDN | `rainbow_cn.json` → 上一版国服数据库 | 保留无法确认的哈希名 |
| 台服 | `img-pc.so-net.tw` 官方 iOS CDN | `rainbow_tw.json` → 上一版台服数据库 | 保留无法确认的哈希名 |
| 日服 | 官方 iOS CDN 加密 CDB，经 Coneshell 解密 | 同版本 `pcr-tool` 部分库 → roboninon → 上一版日服数据库 | 保留无法确认的哈希名；官方恢复失败时使用 roboninon 可读库兜底 |

日服官方 CDB 当前包含两组结构镜像；脚本会在确认两组表结构、类型、主键和行数逐表一致后，只保留与可读参考源对应的第二组。`pcr-tool` 部分库只有在其 `truthVersion` 和资源 MD5 都与官方 iOS 清单一致时才会用于精确恢复列名，尤其用于 `unit_name`、技能槽位和羁绊字段。roboninon 用于补齐更多表名、字段名和最终可读库兜底；上一版日服数据库继续补充前两个来源没有覆盖的名称。

roboninon 的部分无后缀文本字段是英文，并另外提供 `_jp` 日文字段；因此它不会覆盖同版本 `pcr-tool` 给出的日服原始字段名。项目不需要登录游戏账号。每次生成结果后都会运行 SQLite `integrity_check`，并检查美空笔记依赖的关键日服字段；名称映射和恢复报告只保存在 GitHub Actions 的 `.cache` 中，不提交到仓库。

自动任务位于 `.github/workflows/update-databases.yml`：

1. 每 6 小时检查三服版本，也支持手动触发。
2. 下载、解包、恢复名称并校验数据库。
3. 提交当前数据库和版本元数据。
4. 为首次出现的版本创建 GitHub Release，并更新 `data/history.json`。
5. 保存内部缓存，供下次版本更新迁移名称。

## 本地运行

完整数据库更新需要 Python 3.11 或更高版本；官方日服 CDB 解密需要 Windows：

```powershell
python -m pip install -r requirements.txt

python scripts/priconne_unhash.py update-cn `
  --rainbow rainbow_cn.json

python scripts/priconne_unhash.py update `
  --rainbow rainbow_tw.json

python scripts/priconne_unhash.py update-jp
```

如果台服还有自己的可读参考库，可以重复传入：

```powershell
python scripts/priconne_unhash.py update `
  --reference "my-tw=C:\path\redive_tw.db=95"
```

参数末尾数字为参考库优先级。参考库应属于同一区服，时间越近的可信库可设置越高优先级。

运行测试：

```powershell
python -m unittest discover -s tests -v
```

## 部署自己的 API

仓库已经包含 `api/databases.py`、`pyproject.toml` 和 `vercel.json`。将仓库连接到 Vercel 并部署 `master` 即可，无需配置数据库或 API 密钥。函数只需要打包 API 源码和 `data/history.json`；`data/*.db`、恢复脚本、测试与彩虹表已从函数包中排除。

Vercel Python 入口为：

```toml
[tool.vercel]
entrypoint = "api.databases:handler"
```

如果使用自己的域名，将域名绑定到 Vercel Production Deployment 后，把客户端的 `baseURL` 换成该域名即可。

GitHub Actions 使用仓库自带的 `GITHUB_TOKEN`。请在仓库设置中确认 **Actions → General → Workflow permissions** 为 **Read and write permissions**，否则机器人无法提交索引或创建 Releases。

## 致谢与声明

日服 CDB 解密沿用上游收录的 `Coneshell_call.exe`（EAirPeter、esterTion）与 Cygames `coneshell.dll`，出处见 `src/vendor/coneshell/README.md`。

本项目只用于资料研究、开发和数据保存；游戏及数据版权归原权利人所有。公共服务受 Vercel 与 GitHub 的可用性及流量限制约束，生产项目建议做好本地缓存与失败重试。
