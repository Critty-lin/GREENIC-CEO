# 绿色芯片CEO竞选计

在线游玩：<https://critty-lin.github.io/GREENIC-CEO/>

一个像素风的单页文字 + 小游戏合集：你扮演 `xunxun`，去「绿色芯片」（股票代码 **ADVN**）竞选 CEO，在海选、面试、职场流言、董事会护盘和终局拉票里活下来，最后按股价、董事会印象和剩余对手数拿到九种结局之一。

纯前端、零依赖、无构建步骤：一个 `index.html` 就是完整游戏。可选的 Python 服务和 Cloudflare Worker 只负责收集对局数据。

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
config.js             数据服务地址（默认同源，纯静态部署时填写）
server.py             本地 / 自托管服务：静态托管 + /api/runs + /api/honor
serverless/worker.js  可选：Cloudflare Worker 版战绩 API
serverless/wrangler.toml
data/runs.json        对局账本（已 gitignore，不会提交）
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

### 方案 A：Cloudflare Worker + KV（推荐，和 GitHub Pages 搭配）

`serverless/worker.js` 已经按现有 API 写好，CORS 也处理了。

```bash
cd serverless
npx wrangler login
npx wrangler kv namespace create RUNS
# 把输出里的 id 填进 wrangler.toml
npx wrangler deploy
```

拿到 `https://advn-runs.<你的子域>.workers.dev` 后，改 `config.js`：

```js
window.ADVN_API = "https://advn-runs.<你的子域>.workers.dev";
```

提交并推送，Pages 上的游戏就会把对局写到 Worker，授勋和复盘页也会读它。记得把 `wrangler.toml` 里的 `ALLOW_ORIGIN` 改成你的 Pages 域名（默认 `*`）。

> KV 是最终一致存储，极少数并发同时提交时可能少记一条。小游戏够用；要严格计数可以换 D1 或给 Worker 加队列。

### 方案 B：继续用 Python 服务（完整功能）

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

### 方案 C：Supabase / 其他 BaaS

接口只有三个，按同样契约实现即可；把 `config.js` 指向你的服务地址。复盘页不需要改。

## 数据页怎么维护

- 地址：`https://<站点>/review.html`，页面不在游戏导航里，但**它是公开文件**，`robots.txt` 的 `Disallow` 只是不给搜索引擎收录，不是权限控制。
- 页面做的事：拉 `/api/runs`，按设备编号分组，取每台最高分；提供「导出表格（CSV）」和「导出备份（JSON）」。
- 公开数据想加保护：把复盘页放到单独的私有仓库 / 本地打开；或者复制一份只读 Worker，用 Cloudflare Access 保护它，写入用的 Worker 保持公开。
- 数据字段：得分、结局、印象、股价、剩余对手、淘汰数、宣言、随机设备号、时间戳。设备号是浏览器 `localStorage` 里的 8 位随机串，**不记录 IP、UA、姓名**；Cloudflare 边缘仍可能按平台策略记录访问日志。
- 写接口是公开的，技术上可以伪造分数。如果要做排行榜奖励，请加 Cloudflare Turnstile、限流或服务端校验，别把现有数据当权威成绩。
- 定期在复盘页点「导出备份」；换服务前先导出，再迁移。

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

## 免责声明

本项目是**非官方恶搞作品**，与 NVIDIA 及相关公司、人物没有任何关联。游戏中出现的公司、人物、职位和「¥128 解锁」均为虚构和玩笑，不存在真实付费系统。请勿将本作用于商业宣传或让人误以为获得官方授权。

## License

MIT，见 [LICENSE](LICENSE)。
