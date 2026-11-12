# 白名单与抓取方法

## 一、十家白名单（自动抓取范围内）

| # | 机构 | 域名 | 状态 | 备注 |
|---|---|---|---|---|
| 1 | NBER 美国国家经济研究局 | nber.org | ✅ 实测可用 | 有 RSS 新论文源，PDF 直下 |
| 2 | ILO 国际劳工组织 | ilo.org | ✅ 实测可用 | PDF 路径藏在详情页，必须解析 |
| 3 | 斯坦福 SIEPR | siepr.stanford.edu | ⚠️ 列表页通 | PDF 未逐份测，按 ILO 方式解析 |
| 4 | IZA 劳动经济研究所 | iza.org | 待测 | 结构类似 NBER |
| 5 | OECD | oecd.org | 待测 | 部分报告付费，遇到标「付费墙」 |
| 6 | 世界银行 | worldbank.org | 待测 | 以开放获取为主 |
| 7 | Hamilton Project（布鲁金斯） | hamiltonproject.org / brookings.edu | 待测 | 文件名常误标为 MIT，机构以版权页为准 |
| 8 | MIT（含 Shaping Work、Stone Center） | mit.edu / shapingwork.mit.edu | 待测 | 论文与政策简报混发，注意类型判定 |
| 9 | 中国社会科学院 | cass.cn | 待测 | 中文，部分只发摘要 |
| 10 | 国务院发展研究中心 | drc.gov.cn | 待测 | 中文，需找公开版 |

现状：**2 家完全实测可用（NBER、ILO），1 家只验了列表页（SIEPR），7 家待测**。第一次真跑时逐家验，不通的降级到手动投放，并在本表里改状态，不要每次都重试。对外介绍时按「白名单 10 家」说没有问题，但不要承诺十家都能自动抓。

## 二、手动投放（自动抓不了，放 inbox/）

| 机构 | 原因 |
|---|---|
| 麦肯锡 MGI | 服务器主动切断连接，需浏览器 |
| BCG、普华永道 | 需注册 |
| 腾讯研究院等 | 多为公众号长图，无 PDF |

抓不下来的不硬攻，也不找镜像站——来源不可控。

## 三、已验证的抓取要点

### NBER
- RSS：`https://www.nber.org/rss/new.xml` → 200，条目含标题与作者，可直接筛关键词。
- 列表：`https://www.nber.org/papers?page=1&perPage=50&sortBy=public_date` → 200。
- PDF 直链规律：`https://www.nber.org/system/files/working_papers/w{编号}/w{编号}.pdf` → 实测 200，`application/pdf`。

### ILO
- 列表：`https://www.ilo.org/publications` → 200。
- 详情页：`https://www.ilo.org/publications/{slug}` → 200。
- **PDF 路径必须从详情页解析**。页面里同时有 CSS 的 `/sites/default/files/...` 和真正的 PDF 路径，筛 `.pdf` 结尾那条。
- 真实文件名常与标题无关，例：`/sites/default/files/2026-03/Research%20Brief%20GenAI_final0403_0.pdf`。拼 URL 必 404（实测连错三次）。
- 2026-11-12 实测：自动下载 1,185,687 字节，sha256 与用户手工下载的文件完全一致（`7e9f9c7f76f66108613bf03b…`）。

### 通用
- 请求带 `User-Agent: Mozilla/5.0`，否则部分站点返回空页。
- 下载后先校验文件头 `%PDF` 再入库——有些站返回 200 但内容是 HTML 登录页。
- 网址里的 `%20` 有时二次编码成 `%2520`，两种都试；都不通就回详情页重新解析，别猜。

## 四、检索策略

用 WebSearch，`allowed_domains` 填白名单域名，`freshness` 对应时间窗。关键词组合：

- `AI employment report`、`generative AI labour market`
- `automation jobs evidence`、`AI occupational exposure`
- 中文：`人工智能 就业 影响 报告`

**不用不限域名的通用搜索**。通用搜索前列多是咨询公司营销物料与二手转述，正是要避免的那类。

## 五、简报表七列的口径

| 列 | 怎么填 |
|---|---|
| 研报名称 | 原文标题；有中文版同时给中译 |
| 出处/作者 | 机构 + 作者姓名。只写机构不合格 |
| 出处/作者简介 | 20–40 字，说清机构性质或作者身份，不写宣传语 |
| 直达链接 | 报告详情页，不是首页、不是搜索结果页 |
| 可阅读性 | 四选一：免费全文 / 需注册 / 付费墙 / 仅摘要 |
| 可下载性 | 三选一：可直接下载 / 需登录后下载 / 仅在线阅读 |

**类型不进表**：进表前就要按 spec 第 7 条的四步顺序判好，但只用于第 5 步的写法约束，不占表格列。四步走完仍判不出的，简报表里写「待核」，入库时 `summary.json` 的 `meta.type` 填「待核」、`type_reason` 写清卡在第几步。不要为了填满四类而猜。
