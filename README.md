# 绿色芯片CEO竞选计

在线游玩：<https://critty-lin.github.io/GREENIC-CEO/>

一个像素风的单页文字 + 小游戏合集：你扮演 `xunxun`，去「绿色芯片」（股票代码 **ADVN**）竞选 CEO，在海选、面试、职场流言、董事会护盘和终局拉票里活下来，最后按股价、董事会印象和剩余对手数拿到九种结局之一。

纯前端、零依赖、无构建步骤：一个 `index.html` 就是完整游戏。可选的 Python 服务、Cloudflare Pages Functions 或 Worker 只负责收集对局数据。

## 本地运行

```bash
python3 server.py
# 打开 http://127.0.0.1:8000/
```

`PORT` 可选，默认 8000：

```bash
PORT=3000 python3 server.py
```

直接双击 `index.html` 也能玩，只是「授勋」百分位和搜索不到数据。

## 操作

- 鼠标 / 触摸点击按钮；键盘 `1` `2` `3` 选择，`Enter` 继续。
- 海选弹幕：点红框删反对言论，`空格` 删最左边一条。
- 一面开口：`空格` / `Enter`，让指针落在绿区。
- 二面记忆：先看词，再按顺序点；支持数字键 `1`–`6`。
- 拉票：数字键 `1`–`4` 对应四个席位，`Enter` 提交。
- 结局页：`R` 或 `Enter` 重开。

## 关卡与判定

| 场景 | 玩法 |
| --- | --- |
| 海选 | 18 秒弹幕，删反对、误伤支持者扣分、漏掉反对也扣分 |
| 一面 | 三次时机判定，指针停在绿区 |
| 二面 | 记住三个词的顺序再复现 |
| 职场 | 五条流言判断「拆穿 / 放过」 |
| 董事会 | 8 秒护盘，点掉红 K 线 |
| 终局 | 说动董事并提交表决 |

三项数值：股价（初始 `$138.40`）、董事会印象（初始 42）、剩余对手（初始 128）。得分：

```text
印象 × 12 + max(0, 股价 - 90) × 2.2 + 已淘汰 × 2
```

结局按优先级判定：`任命冻结` → `印象没过线` → `被对手截胡` → `你出任 CEO` → `泡沫上的加冕` → `临危受命` → `有争议的任命` → `顾问席`；中途放弃是 `另谋出路`。九种结局都收录在首页的「结局陈列室」。

## 目录

```text
index.html            游戏本体（样式 + 逻辑 + 像素立绘 + 音效）
review.html           数据复盘页（按设备分组、导出 CSV / JSON）
config.js             数据服务地址（当前指向 Pages API）
server.py             本地 / 自托管服务：静态托管 + /api/runs + /api/honor
wrangler.toml         Cloudflare Pages 项目配置（KV 绑定 / CORS）
functions/api/        Pages Functions 版 /api/runs + /api/honor
pages-public/         API 的简单落地页
serverless/worker.js  可选：Cloudflare Worker 版战绩 API
serverless/wrangler.toml
data/runs.json        本地对局账本（已 gitignore，不会提交）
robots.txt            禁止索引复盘页
```

## 公开发布：GitHub Pages

游戏本体可以直接放到 GitHub Pages，所有人打开网址就能玩。

1. 新建仓库并推送本项目（`data/`、日志和缓存已被忽略）。
2. 仓库 **Settings → Pages → Build and deployment → Source**，选择 **GitHub Actions**。
3. 仓库已带 `.github/workflows/pages.yml`，推送到 `master` 后会自动部署；首次也可以在 **Actions → Deploy Pages → Run workflow** 手动触发。
4. 等一两分钟，访问 `https://<用户名>.github.io/<仓库名>/`。

工作流只发布 `index.html`、`review.html`、`config.js`、`robots.txt` 和 `.nojekyll`，不会把 `server.py`、README 或开发文件放进站点。

**注意：GitHub Pages 只能托管静态文件**，`/api/runs`、`/api/honor` 不存在。纯 Pages 部署时：

- 游戏、结局、陈列室全部正常；
- 「查看排行」会显示「对照暂时连不上」；
- 不会收集任何数据，`review.html` 也没有数据可看。

如果只想要“能玩”，这就够了。想保留数据，见下一节。

## 公开发布：接上战绩服务

### 方案 A：Cloudflare Pages Functions + KV（当前线上用法，推荐）

游戏在 GitHub Pages，API 单独部署成一个 Cloudflare Pages 项目。国内网络通常可以访问 `*.pages.dev`，而 `*.workers.dev` 可能被 DNS 污染。

- 根目录 `wrangler.toml`：Pages 项目名、KV 绑定、CORS 来源
- `functions/api/[[path]].js`：Pages Function，复用 `serverless/worker.js`
- `pages-public/`：API 的简单落地页

```bash
npx wrangler login
npx wrangler kv namespace create RUNS
# 把 id 填进根目录 wrangler.toml 和 serverless/wrangler.toml

npx wrangler pages project create greenic-ceo-api --production-branch main

# 设置复盘访问钥匙。不设置的话 GET /api/runs 是公开的。
npx wrangler pages secret put REVIEW_KEY --project-name greenic-ceo-api

npx wrangler pages deploy pages-public --project-name greenic-ceo-api --branch main
```

`REVIEW_KEY` 不会写进仓库，也不会出现在 `config.js` 里；复盘页会让访问者手动输入。对局上报 `POST /api/runs` 和授勋 `GET /api/honor` 仍然是公开的。

拿到 `https://greenic-ceo-api.pages.dev` 后，把 `config.js` 改成：

```js
window.ADVN_API = "https://greenic-ceo-api.pages.dev";
```

提交推送，GitHub Pages 会自动重新部署；游戏上报、授勋和复盘页都走这个 API。`ALLOW_ORIGIN` 要写成你的 GitHub Pages 站点源（例如 `https://critty-lin.github.io`，不带仓库路径）。

> KV 是最终一致存储，而且当前把整本账写在一个 `runs` 数组里，多个玩家同一秒结算时理论上可能互相覆盖。朋友局够用；如果要公开大流量，建议换 D1 / 队列，或至少接受极小概率的丢记录。

### 方案 B：Cloudflare Worker + KV（备用）

`serverless/worker.js` 同时是一个标准 Worker。如果 `workers.dev` 在你的网络可访问：

```bash
cd serverless
npx wrangler login
npx wrangler kv namespace create RUNS
# 把输出里的 id 填进 wrangler.toml
npx wrangler secret put REVIEW_KEY
npx wrangler deploy
```

拿到 `https://advn-runs.<你的子域>.workers.dev` 后，改 `config.js` 并提交。记得把 `ALLOW_ORIGIN` 改成你的 Pages 域名。

> KV 是最终一致存储，极少数并发同时提交时可能少记一条。小游戏够用；要严格计数可以换 D1 或给 Worker 加队列。

### 方案 C：继续用 Python 服务（完整功能）

把 `server.py` 部署到任意有持久磁盘的容器 / VPS（Render、Fly.io、Railway、自己的机器），`PORT` 由平台注入。游戏和复盘页同源，`config.js` 留空即可。

如果游戏在 GitHub Pages、API 在另一台机器，需要跨域：服务会按 `ALLOW_ORIGIN` 返回 CORS 头，默认 `*`；上线时建议改成你的 Pages 域名：

```bash
ALLOW_ORIGIN="https://<用户名>.github.io" PORT=8000 python3 server.py
```

并把 `config.js` 指向 `https://你的域名`。

数据在 `data/runs.json`，写入使用临时文件原子替换，最多保留 2000 条。服务端已经：

- 禁止通过 HTTP 读取 `data/`、`.git/`、`server.py`、`app.toml` 和 `.log`；
- 对写文件加锁；
- 静默客户端断连导致的 BrokenPipe / ConnectionReset；
- 添加 `X-Content-Type-Options: nosniff`。

> 不要用无持久磁盘的免费实例，重启会丢 `data/runs.json`。记得定期把数据文件或复盘页导出的 JSON 备份走。

### 方案 D：Supabase / 其他 BaaS

接口只有三个，按同样契约实现即可；把 `config.js` 指向你的服务地址。复盘页不需要改。

## 数据页怎么维护

- 地址：`https://<站点>/review.html`。页面 HTML 本身仍是公开的，但**没有访问钥匙看不到任何对局数据**：`GET /api/runs` 会校验 `X-Review-Key`，返回 401 时页面只显示输入框。
- 钥匙设置在 Cloudflare Pages 的加密 Secret `REVIEW_KEY` 里，不写进代码；复盘页输入后只存在当前浏览器标签页的 `sessionStorage`，关掉页面就要重新输入。页面上有「锁定」按钮可以立即清除。
- 设置或更换钥匙：

```bash
npx wrangler pages secret put REVIEW_KEY --project-name greenic-ceo-api
npx wrangler pages deploy pages-public --project-name greenic-ceo-api --branch main
```

- 页面做的事：拉 `/api/runs`，按设备编号分组，取每台最高分；提供「导出表格（CSV）」和「导出备份（JSON）」。
- 如果 `REVIEW_KEY` 没设置，`GET /api/runs` 是公开的，适合本地开发；线上请务必设置。本地 `python3 server.py` 也支持 `REVIEW_KEY=...` 环境变量。
- 数据字段：得分、结局、印象、股价、剩余对手、淘汰数、宣言、随机设备号、时间戳。设备号是浏览器 `localStorage` 里的 8 位随机串，**不记录 IP、UA、姓名**。
- 写接口是公开的，技术上可以伪造分数。如果要做排行榜奖励，请加 Cloudflare Turnstile、限流或服务端校验，别把现有数据当权威成绩。
- 定期在复盘页点「导出备份」；换服务前先导出，再迁移。

## 访问日志

- **GitHub Pages** 不提供逐请求访问日志，仓库的 Traffic 里只有访客/克隆的汇总。
- **Cloudflare Pages** 控制台有请求量、状态码等分析；需要实时看 Function 调用可以用：

```bash
npx wrangler pages deployment tail --project-name greenic-ceo-api
```

`tail` 是实时输出，只显示你运行命令期间发生的请求；它不保存历史。

- 原始 HTTP 请求日志（含 IP、路径）属于 Cloudflare 的 Logpush / 企业级功能，免费套餐通常拿不到；平台会按自己的策略保留访问日志。
- 本项目自身只把随机设备号、分数和结局写进 KV，不记录 IP 或 UA。如果要做访客统计，可以另外接 Cloudflare Web Analytics 或轻量计数器，并在页面上说明隐私政策。

## 最近的修改（2026-11-24）

- 修复「放弃竞选」没有二次确认：`quitask` 的「还是投递」原来指向不存在的 `apply` 动作，现在正确回到投递页。
- 海选弹幕不再一波清场：单条淘汰 8 → 3，结算淘汰 `18 + 4h` → `10 + 2h`；新增漏掉反对言论的股价 / 印象惩罚，并在提示里显示漏过数量。
- 拉票去重：点击席位时一次性结算（+4 印象 / +2.3 股价），提交表决不再重复加一次；总收益和改前一致。
- 键盘补全：二面 `1`–`6`、拉票 `1`–`4` 与 `Enter` 提交、陈列室 `Enter` 返回、授勋页重开；弹窗打开时不再穿透到背后场景。
- 清掉死代码：不可达的 `quitask` 旧按钮、重复的拉票处理、`posted` 状态、`help` 场景、废弃的 `.board-row` 样式。
- 复盘页的宣言从内部 id（`story` / `tech` / `ambition`）显示为中文，并支持跨域数据服务。
- 新增 `config.js`，纯静态部署可以指向外部战绩服务。
- 服务端加固：屏蔽 `data/` 等敏感静态路径、并发锁、非法浮点、默认端口、断连静默。
- 护盘提示统一为「失误」，不再把漏掉的红盘算成「误点绿」。
- 补 favicon、`robots.txt`、README 和部署说明。
- 战绩服务上线：Cloudflare Pages Functions + KV，`config.js` 指向 `https://greenic-ceo-api.pages.dev`，CORS 限定 GitHub Pages 源；`workers.dev` 版本保留为备用。
- 复盘页加访问钥匙：`GET /api/runs` 校验 `REVIEW_KEY`，页面无钥匙只显示输入框；对局上报和授勋保持公开。

## 免责声明

本项目是**非官方恶搞作品**，与 NVIDIA 及相关公司、人物没有任何关联。游戏中出现的公司、人物、职位和「¥128 解锁」均为虚构和玩笑，不存在真实付费系统。请勿将本作用于商业宣传或让人误以为获得官方授权。

## License

MIT，见 [LICENSE](LICENSE)。
