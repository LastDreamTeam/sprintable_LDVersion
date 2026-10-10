# Sprintable

> **LDVersion 简体中文与自部署兼容修复**：新增中文界面，保留 English / 한국어；本地头像／文件直传补丁见下文。
> 安装、验证、上游更新及回滚边界见 [.ld/zh-CN/README.txt](.ld/zh-CN/README.txt)。
> 此为社区维护的中文 Fork；不包含任何实例的凭据、项目数据或服务器部署配置。

## LDVersion：改动清单、部署边界与升级约定

### 持续交付约定与 2026-10-10 本地化修复

- 项目访问撤销现在复用原生 `ConfirmDialog`：智能体详情、访问矩阵及人类成员入口都先显示影响范围，取消不调用写接口，确认才撤销原授权；三种语言共用文案键。运行中权限变化时，旧确认不会反向变成授予权限。底层权限 API 及删除语义不变，不是禁用按钮或绕过访问控制。
- 引用气泡／预览／任务列表曾直接使用写死的韩语状态表；现透传当前 next-intl locale，增加中英文表并保留韩文和未知状态的原判定。文档 `draft` 显示“草稿”，不改数据库枚举。
- 2026-10-10 成员“消失”事故：浏览器撤销项目 grant 后，原生 API 同时删除 agent_project_profiles；身份、密钥和消息仍在，但项目名单无法解析该成员。恢复必须按已核实的原项目权限重新授权，不能清库、重建 Bot 或随意提权。弹窗用于预防误操作，不禁止有意撤销。

- **每次修复与优化必须同步本 Fork 的 `main_1`**，包括测试、说明和可复用部署工具；不再把仅存在生产机器上的源码修改视为交付完成。此约定同时写入 `AGENTS.md`。
- 源码、构建产物和实例数据分开。服务器应维护本仓库只读源码检出，并记录实际部署的源码 SHA、构建来源和文件校验值；不能把生产目录整体 `git add`，不能把数据库、密钥和上传物推入 Git。
- **聊天缩略图修复**：`next.config.ts` 使用 Next.js 原生 `images.localPatterns`，只对 `/api/storage/local/**` 放行动态查询参数。此前原图读取 200 但优化器 400，原因是本地签名参数被默认策略拒绝；不移除 HMAC、不开放磁盘根目录、不放宽远端 URL 白名单。回归必须覆盖真实 `/_next/image`，不能只验上传和下载接口。
- **语境化中文**：统一智能体、任务卡、交付产物、审批节点、迭代、进度汇报和接入向导，修正“客服人员、特工、神器、索赔、登机口、提款”等误译。只改文案，不改 API 工具名、状态枚举、权限或 ICU 参数。角色模板、服务端通知是独立语言层，不能仅凭中文网页就宣称已经完整汉化。
- 手动构建工作流现接受 `public_app_url` 和 `backend_url`，不再固定某个指挥中心的地址；`build_services` 可选，前端修复不必重新下载全部基础镜像。产物仍由人审核后部署，不随 Git push 自动上线。
- 本段描述源码能力，**不单独证明线上已切换**；以部署机 release receipt / `DEPLOYMENT.json` 和验收结果为准。下方旧日期回执保留作历史证据，不代表当前全站状态。

核对日期：2026-10-10。本节记录 **Sprintable Fork 及其 Hermes 接入** 的已核实差异，供后续维护者与 Agent 在更新前阅读；不是其他 Bot、模型或整套主机运维的变更总账。下方上游说明继续保留，但其 SaaS 部署方式不等于本实例的部署方式。

### 分支与状态

- `main_1`：LD 维护主分支，也是本仓库默认分支。
- `legacy/main`：原版归档，初始上游基线为 `fd168be8c1484c04e2a179aeb8d8a7383845226a`；不要把它当作部署目标或持续覆盖的工作分支。
- 上游：[moonklabs/sprintable](https://github.com/moonklabs/sprintable)。中文提交为 `bd316c52766311c7efe3f5939c80043ceee1ab91`，手动构建提交为 `b91c2cbbad27a11503841ebd6eaded2afa57f50c`。
- 2026-10-10 上海前端仍为 `b91c2cb` 中文构建；Backend 已加载下述 `ld-avatar-20261010` 修复镜像。登录、个人头像 PNG/JPEG/WebP 的申请→PUT→确认→显示→刷新→替换→删除，以及「存储」页的图片／文本上传登记和授权下载，均经真实公网 HTTPS / 网页 BFF 流程验收；聊天 multipart 上传及原生图片上下文下载也已复测。**不是“全站全部功能验收通过”**：未发送孤立文件回收、会议上下文与技能说明仍有下述边界；没有把接口验收说成已人工点击所有浏览器页面。后续文档提交不等于重新部署。
- 上海是经批准新建的独立空间，不是美机数据库的完整迁移。美机数据尚待恢复通路后另行比较；不得用旧备份覆盖上海已经产生的新消息和项目数据。

### 已入库的 LD 改动

相对上述上游基线，当前代码差异集中在以下文件；2026-10-10 晚补充了明确标注的 Sprintable 后端兼容代码，不再是“仅汉化＋配置”。没有数据库 schema 或 Hermes 核心补丁。

| 改动 | 文件 | 更新时必须保留／复核 |
| --- | --- | --- |
| 简体中文词库 | [`apps/web/messages/zh.json`](apps/web/messages/zh.json) | 6,304 个叶子词条；与英文键集合一致，保留 ICU 参数、标签、分支及内联代码。机器翻译加术语修订，不代表逐句人工终审。 |
| 三语言选择及协商 | [`locale-switcher.tsx`](apps/web/src/components/locale-switcher.tsx)、[`locale-negotiation.ts`](apps/web/src/i18n/locale-negotiation.ts) | 保留 EN / KO / ZH；显式语言 Cookie 优先于浏览器语言，兜底仍为英文，不是强制全站默认中文。 |
| 字体、元信息、日期 | [`layout.tsx`](apps/web/src/app/layout.tsx)、[`zh-fonts.css`](apps/web/src/app/zh-fonts.css)、[`chat-bubble.tsx`](apps/web/src/components/chat/chat-bubble.tsx)、[`chat-proof-section.tsx`](apps/web/src/components/verify/chat-proof-section.tsx) | 中文系统字体回退、中文网页元信息、随界面语言显示聊天／引用日期。新增字体层不下载字体、不请求在线翻译。 |
| 法律页面的中文界面标签 | [`privacy/page.tsx`](apps/web/src/app/privacy/page.tsx)、[`refund-policy/page.tsx`](apps/web/src/app/refund-policy/page.tsx)、[`terms/page.tsx`](apps/web/src/app/terms/page.tsx) | 仅标题、导航、空状态等；法律正文、公司信息和联系人未改写，不宣称提供正式法律译本。 |
| 中文接入指南及公开路由 | [`connect-guide.zh.txt`](apps/web/public/connect-guide.zh.txt)、[`proxy.ts`](apps/web/src/proxy.ts) | 增加中文指南的公开路径，不扩大其他鉴权豁免。指南中的消息行为须同时核对服务端通知偏好，不能只看连接器。 |
| 中文验证及维护说明 | [`locale-zh.test.ts`](apps/web/src/i18n/locale-zh.test.ts)、[`check-zh-locale.cjs`](scripts/check-zh-locale.cjs)、[`.ld/zh-CN/README.txt`](.ld/zh-CN/README.txt)、本 README | 测试不能随合并丢失；翻译来源、质量边界、回滚约定一起保留。 |
| 独立手动构建 | [`.github/workflows/ld-build-runtime.yml`](.github/workflows/ld-build-runtime.yml) | 仅 `workflow_dispatch`，限定本仓库的 `main_1`；生成网页及服务镜像压缩包、源码提交和校验和，不自动登录或部署服务器。 |
| 本地原生回收调用器 | [`.ld/self-hosted/storage-maintenance.py`](.ld/self-hosted/storage-maintenance.py) | 仅调用现有 `assets-grace-hard-delete` 接口并输出磁盘告警状态，不发明按文件年龄或“业务价值”删除的策略。需另行安装 systemd 单元及 root-only 凭据，不随 Git 更新自动部署。 |
| 组织级头像身份修复 | [`repositories/team_member.py`](backend/app/repositories/team_member.py)、[`routers/team_members.py`](backend/app/routers/team_members.py) | 新增 `get_profile`：个人资料读取／头像接口不再要求无关的 project_access 行。仍核验 org、有效组织成员、本人／主人／管理员与保留 Agent 限制；不借头像操作增加项目权限，也不替换一般项目接口的 `get()`。 |
| 本地磁盘头像及直传 | [`services/avatar_upload.py`](backend/app/services/avatar_upload.py)、[`services/storage/local.py`](backend/app/services/storage/local.py)、[`routers/local_storage.py`](backend/app/routers/local_storage.py)、[`main.py`](backend/app/main.py) | 沿用原生三步上传协议，补齐 BE 签名 PUT 接收器；签名绑定路径、方法、类型、大小和 create-only，流式落盘并原子拒绝覆盖，失败清理临时文件。只公开独立头像容器，正文附件继续鉴权／短期签名。头像 PNG/JPEG/静态 WebP ≤5 MiB，校验真实图片格式；旧头像替换／删除沿用原生清理。 |
| 回归测试及小镜像叠层 | [`test_ld_local_upload.py`](backend/tests/test_ld_local_upload.py)、[`test_storage_provider.py`](backend/tests/test_storage_provider.py)、[`test_2887_avatar_upload_service.py`](backend/tests/test_2887_avatar_upload_service.py)、[`.ld/self-hosted/Dockerfile.backend-overlay`](.ld/self-hosted/Dockerfile.backend-overlay) | 37 项隔离测试通过，包含并发创建只能成功一次、伪造／过期／类型不符／越界拒绝及 GCS 地址协议不回退。叠层只用于已核实原镜像的低资源热修；正常全量构建仍用 `backend/Dockerfile`，禁止把叠层套到未经核对的新基线。 |

构建工作流还包含容易遗漏的部署适配：Node 22、锁定 pnpm 9.15.0、冻结依赖安装、单并发构建，以及仅在临时 runner 内修改 `next.config.ts` 的内存／worker 参数。这不是仓库中持久的 `next.config.ts` 改动；上游配置结构变化时工作流会主动失败，必须重新审查，不能删除断言硬套。`NEXT_PUBLIC_*` 当前带有 LD 的构建地址，复制部署前需要核对；有些地址在构建时固化，改运行时 env 不一定足够。构建附件只保留 1 天，**不是长期回滚备份**。继承的其他上游 CI 未整体重写，启用前须检查触发分支、云目标、发布权限和 secrets。

### 仅在服务器上的配置／外层补丁（未随仓库分发）

以下是上海现网的部署清单，不是通用安装默认值。这里只记录位置与用途，不公开文件内容、账号、密码、密钥、白名单 UUID、聊天或私有日志。**`git clone` / `git pull` 本仓库不会恢复这些文件。**

| 项目 | 现网位置／行为 | 与升级的关系 |
| --- | --- | --- |
| 独立部署与持久数据 | `/srv/sprintable/compose.json`、`config/web.env`、`secrets/app.env`、`data/`、`runtime/web/` | PostgreSQL、Backend、MCP、入口容器与原生 Node 前端独立管理；限制资源、端口绑定回环。业务数据、附件与 secrets 不放 Git。 |
| 前端服务隔离及附件共享 | `/etc/systemd/system/ld-sprintable-web.service`、其 `30-local-storage.conf` drop-in、`/srv/sprintable/data/blobs` | 专用共享组 `ld-sprintable-storage`，仅附件根目录采用 setgid＋组读写；网页与后端 `umask 0007`，后端容器仅追加该组。网页只增加这个可写目录，不取消整体隔离，不让网页加入 Hermes 的用户组。 |
| 网页入口 | `/srv/sprintable/` 下的独立入口配置；`ld-sprintable-cert-renew.timer`、`ld-sprintable-hk-relay.service` | 上海 IP HTTPS 入口已启用；香港新转发已准备，但本次核对时公开域名仍指向旧美机入口，不能写成已完成域名切换。仅维护本服务入口，不覆盖其他站点、代理或隧道。 |
| 账号与空间 | Sprintable 自己的 PostgreSQL | 新空间账号、项目、成员身份及密码设置属于实例数据，不是源码默认账号。已限制公开注册；不把可登录密码放进 README、种子数据或构建产物。 |
| 主人邮件状态一次性确认 | 原生 `auth.verify_email` 处理器＋现有主人记录 | 新空间初始 `email_verified=false`，且未配置 SMTP／Resend；按主人明确授权仅确认此账号。不是邮件真实投递证明，不放开其他用户、不改全局校验策略或密码；激活清单已实际返回 5/5。 |
| Hermes 生效配置 | `/etc/hermes-trusted/runtime.json`、`/etc/hermes-trusted/current/config.yaml`、`/etc/hermes-trusted/current/runtime.env` | `current` 指向受保护快照，Gateway 使用受控挂载。宿主可编辑 home 下的同名文件未必是生效来源；不得绕过保护直接改只读快照。 |
| 原生工具／消息接线 | 上述 Hermes config / env | SSE 插件 API 为 `http://127.0.0.1:32800`；MCP 为 `http://127.0.0.1:32808/mcp`，连接／调用超时均为 60 秒。插件收消息，MCP 提供工具，两者不可互相替代；当前只放行 29 个 MCP 工具，不是服务器列出的全部工具。 |
| 凭据作用域及 ACK 兼容 | `/opt/hermes-trusted/empty-plugins/sprintable-platform/__init__.py` | 外层包装使用 Hermes 的凭据作用域，并在 ACK 请求成功后才推进确认游标；依赖探测不越作用域读取密钥。调用了 `_profile_runtime_scope` 等内部接口，**属于自维护兼容补丁，不是官方稳定 API 保证**。 |
| 消息级去重与命令保护 | 同目录的 `delivery_guard.py`，配合原生 `adapter.py` | 以会话 ID＋原消息 ID 合并 `conversation.message_created` / `conversation:mention` 的重复触发，保留原生事件类型；保护 `/stop` 等 slash 命令不被结构化前缀变成普通模型请求。去重复用内存缓存，不承诺跨进程永久“恰好一次”。 |
| 旁听／激活信息 | 生效 `runtime.env` | `SPRINTABLE_NONINVOKE_OBSERVATIONS=1`、`SPRINTABLE_ACTIVATION_HEADER=1`。只处理服务端已投递的事件；不能让被 `mentions` 过滤掉的气泡凭空进入上下文。 |
| 备份、验收与回退 | `/srv/sprintable/scripts/`、`/srv/sprintable/backups/`、`/srv/sprintable/SHANGHAI-DEPLOYMENT-HANDOFF.txt` | 保留一致性备份、校验和、恢复验证及接入切换记录。Gateway 接线回退只恢复接线配置，不回写 Bot 记忆或覆盖 Sprintable 新数据。 |
| 原生存储回收调度 | `ld-sprintable-storage-maintenance.service` / `.timer`；`/srv/sprintable/scripts/storage-maintenance.py`；`/srv/sprintable/secrets/storage-maintenance.env` | 每天 Asia/Shanghai 04:30＋最多 5 分钟随机延迟，补跑错过的调度；只请求回环 Backend 的原生鉴权回收接口。脚本源码已入库，systemd 单元和密钥仅部署侧保存；磁盘告警只写 journal，不宣称会自动发邮件／QQ。 |
| 本地头像部署配置 | Backend `GCS_AVATARS_BUCKET=sprintable-avatars`；`data/blobs/sprintable-avatars/`；入口配置 `/api/v2/storage/` 定向回环 Backend | 变量名沿用上游，但 local 下是磁盘子目录，不是 Google 账号／云桶。独立路径仅服务新签名上传和头像读取；不能把整个 blobs 根目录设为公开目录。头像同源相对 URL 不会固化旧主机地址；写入签名基址须与当前网页入口一致。 |
| 女仆长原生项目归属恢复 | 原生 `POST /api/v2/projects/{project_id}/access`，仅原来的女仆长／项目，普通 member 权限 | 20:36 备份有授权，21:13 备份已经没有；21:05 起发生 `API key member not found`，早于 21:25 的头像修复切换。未找到删除来源证据，不能归责某个人。恢复原授权后旧 Key 恢复 200；未重签 Key、未重建成员／会话、未重启 Hermes。 |
| 现有 Agent 技能 | Hermes home 的 `skills/devops/sprintable-stream-triage/`、`skills/qqbot-platform/im-channel-onboarding/` | 服务器侧已有排障／接入技能，不随本仓库分发，也不等于完整会议使用技能；已发现的说明缺口见下一节。 |

“外层补丁”仅表示没有直接修改 Hermes 核心文件，**不等于不受上游更新影响**：插件内部接口、事件结构、MCP 工具名、配置 schema 和挂载方式变化都可能破坏兼容性。上海完成的接线验收也不证明美机当前在线或已同步同样状态。

### 当前已知缺口与待定默认（不要误报完成）

1. **聊天附件：本地磁盘已修复。** 根因是网页端缺少生产签名密钥与可写持久目录，而后端已有自己的 local 配置。现已令网页 `STORAGE_LOCAL_ROOT=/srv/sprintable/data/blobs` 对应后端 `/data/blobs`，共用已有的非默认签名密钥；后端签名链接改指当前上海 HTTPS 入口，不再指向旧美机域名。用 68 字节测试 PNG 验证真实 HTTPS 上传、消息资产登记、授权下载字节一致、Agent 身份读取该未 @ 消息、原生图片上下文签名及下载；未调用视觉／聊天模型。未授权签名和伪造签名访问均被拒绝。测试消息已按原生接口删除，测试资产已软删除等待宽限期，不删除任何已有用户附件。仅重载 Sprintable Backend 与 Web，Hermes Gateway PID 未变。
2. **网盘不是对象存储。** [原生存储工厂](apps/web/src/lib/storage/factory.ts) 支持 `local`、`gcs`、`s3` / `minio`；Google Drive 不是 `gcs`，当前无直接 Drive provider。Drive 备份／同步或专门适配器需要另行实施，不应宣称填一个网盘链接即可启用。
3. **消息投递以数据库当前设置为准。** 原生 `notification_preferences` 存在全局、项目或会话作用域。20:37 验收时会议覆盖为 `sse/mentions`；头像修复中发现它已于 21:00:25 改为 `all`，本次未改回、未覆盖这个并发配置。原生 `all` / `mentions` / `mute` 是投递级别，不是完整的模型发言策略；`free_response=true` 可以放宽 `mentions`，不能解除显式 `mute`。测试必须重新读取实际设置，不能按过时的 mentions 假定发送测试消息不会调用模型。
4. **可读历史不等于自动补齐。** 原生 `sprintable_list_chat_messages` / `sprintable_get_chat_message` 已可用，能按权限读到未 @ 的历史。旁听缓存只适用于已经投递、且明确指定其他收件人的事件；当前原生缓存最多 20 条、每条 500 字，属于内存缓存。没有 `audience` 的广播消息默认算对本 Agent 发言，不能只打开旁听开关就声称实现“所有消息都看、只有 @ 才回复”。
5. **之前选择 B，不等于永久锁死配置。** 没有实现 C 的自动拉取／拼接上下文，也没有重写上游全局默认或批量迁移其他会话。前端可随时调整：会话右上角齿轮编辑自己的通知规则；管理员从组织成员的详情页「通知规则摘要 → 编辑」代改指定 Bot 的会话规则，已验证主人可经网页 BFF 读取女仆长实际覆盖项。不要把人类界面的铃铛静音当作 Bot 投递设置。`all` 后由模型选择沉默是另一层行为，仍可能逐条调用模型付费；它不保证无限上下文或永久记忆。头像修复没有改通知偏好或人设。
6. **技能说明待校正／补充。** 现有技能偏排障，缺少“被 @ 后读同会话近期历史、读取附件、记录决策与任务交接”的可靠日常流程；其中“不用 @ 一定送达”的说明漏看服务端通知偏好，“90 秒超时一定是后端卡死”的推断也缺少对端地址与维护时间线验证。它们不是官方保证。后续应补足工具发现、权限与上下文预算说明；不能把集成缺口简单归责于 Agent，也不能用技能提示代替需要确定性实现的接入逻辑。
7. **原生回收不是“所有文件自动过期”。** [`cron.py`](backend/app/routers/cron.py) 的 `assets-grace-hard-delete` 仅回收已经标记 `deleted_at` 且超过 7 天的资产，每次最多 500 个，blob 删除成功后才删除记录；已接本地定时调用。有效聊天／文档／任务引用不会仅因久远而过期，5 分钟／30 分钟签名 URL 的 TTL 也不是文件删除时间。上传后取消发送、尚未登记进资产表的文件不在此原生任务覆盖范围；未增加自定义孤立文件扫描或内容价值分类。`storage-usage-warn` 依赖订阅容量和邮件通道，不能当作自建磁盘的可靠配额／告警；本地脚本只记录磁盘空间。当前系统盘约 85% 已用，主要不是本次附件，未擅自清理其他目录。
8. **头像／存储直传现已补齐，但不是纯配置修复。** 上游当前 Local provider 的 create-only 仍返回失败；头像服务还固定 GCS 公共地址，个人资料接口又漏查无项目投影的组织成员。本 Fork 的上述小范围 BE 补丁修复这些缺口，未关闭安全校验。普通直传签名上限 100 MiB，头像 5 MiB；现网聊天 multipart 入口仍有 24 MiB Nginx 上限，没有宣称测过 100 MiB 大文件。未改整个前端、未增 MinIO／其他新常驻服务；用户取消尚未确认的头像和文件仍属于孤立文件回收边界。

### 2026-10-10 头像修复验收与回退

修复前最新数据库备份 `/srv/sprintable/backups/fresh-20261010T131314Z/` 已实际恢复到独立临时库验证；临时库随后删除。配置／旧镜像与验收记录在 `/srv/sprintable/backups/avatar-repair-20261010T132523Z/`，包含 `BEFORE.json`、`APPLIED.json`、`ACCEPTANCE.json`、`CHAT-REGRESSION.json` 和原生项目授权恢复回执。新镜像 ID 为 `sha256:a1ec80c1fc3f44d1903416fed333d747e4a0fcac3e287bf28a998bba0b422d04`；只切换 Sprintable Backend 并热载入其 Nginx 入口，Web、MCP 和 Hermes Gateway 未重启。

验收只临时操作当时为空的主人头像，结束恢复为空；未替主人或女仆长选定图片。测试文件已按原生接口软删除（7 天宽限），未发送的单个测试 blob 已按确切路径清除；没有删除用户上传物。未调用聊天／视觉模型，也未向已改成 all 的会议投递测试消息。

回退命令（须先核对后续修改）：`python3 /srv/sprintable/scripts/deploy-avatar.py --rollback /srv/sprintable/backups/avatar-repair-20261010T132523Z`。它只回切后端镜像、实例 env 和入口配置，不回灌数据库、不删除新上传物、不撤销恢复的女仆长项目归属。旧代码不支持新本地头像路径，回退期间这些头像可能暂不能显示；文件仍保留。部署及验收脚本仅在服务器 `scripts/` 与本地工作目录，不随公开仓库携带账号或数据。

阅读与使用应以 [官方自部署指南](docs/self-hosting.md)、[原生 Hermes 连接器](connectors/hermes-sprintable/README.md)、[组织／项目权限 API](backend/app/routers/project_access.py) 和当前源码交叉核对：组织中能看到 Agent 不等于已授予项目归属，MCP 通不等于 SSE 消息通。官方快速指南的版本／健康路径存在滞后（现网为 Next 16.2.2，Backend 健康路径 `/api/v2/health`）；不要照抄其中 `down -v`、全局网络清理或重建数据库的示例到此生产实例。

本次修复的服务器记录位于 `/srv/sprintable/backups/storage-repair-20261010T123707Z/`，包含配置副本、`APPLIED.json`、`OWNER-CONFIRMATION.json`、`ACCEPTANCE.json`；修复前还完成了新的数据库真实恢复校验。一次性运维脚本为 `scripts/repair-storage.py`、`scripts/verify-owner.py`、`scripts/accept-storage.py`（均在服务器部署根目录下，不随仓库分发）。配置回退入口为 `python3 /srv/sprintable/scripts/repair-storage.py --rollback /srv/sprintable/backups/storage-repair-20261010T123707Z`，执行前仍需审查当前服务状态与后续改动；它不回写数据库或移除新附件，也不自动撤销已授权的账号确认。共享组与目录权限保留以避免破坏后来上传的数据，完全移除须另行审查。

原生依据：[Hermes 连接器](connectors/hermes-sprintable/README.md)、[通知路由](backend/app/services/channel_router.py)、[聊天 MCP 工具](backend/sprintable_mcp/tools/chat.py)、[存储配置](apps/web/src/lib/storage/config.ts)。多种事件表示同一消息是原生设计；本地去重针对重复模型执行，不是删除原生业务事件。

### 跟随上游更新：必须逐项检查

1. **更新前留可恢复版本。** 记录当前源码 SHA、构建产物 SHA256、镜像 ID、配置版本和数据库迁移版本；在服务器侧备份最新 PostgreSQL、附件、env、入口／服务配置、外部插件与相关技能，并验证备份能读／能恢复。GitHub 临时 artifact 和仅有源码都不够；敏感备份不得上传公开仓库。
2. **在独立集成分支合并。** 从 `main_1` 建临时升级分支，获取并记录上游具体 SHA 后合并；逐项核对本节改动。不要用整目录覆盖、`reset --hard` 或强推把 LD 差异抹掉；不要移动 `legacy/main` 冒充新的原始基线。浅克隆缺少共同祖先时先补齐必要历史，不强行忽略 ancestry。
3. **中文与构建验证。** 按锁文件安装依赖，运行下列检查；新／删英文词条同步中文。验收 EN/KO 不回退、中文切换、日期、登录、看板、聊天、文档、设置及窄屏布局。不要在负载紧张的生产主机直接全量构建。
4. **接入与附件验证。** 核对服务端通知偏好、SSE 与 MCP 两条链、工具 allowlist、凭据作用域和去重／ACK 接口；确认同一条 @ 只产生预期的一次回复、slash 命令仍走原生处理。用“普通消息后再 @”验证选定的上下文模式；验证附件上传、浏览器授权下载以及 Agent 实际读取，不能只看 HTTP 200、工具枚举或“正在生成”。
5. **范围与回退。** 暂存候选版本并检查配置差异，所需服务重启须按授权空闲执行；保留旧产物及配置可回切。网页回滚不覆盖新业务数据；数据库 schema 不兼容时单独评估迁移／恢复，不能盲目回灌初始备份。移除 Sprintable 时只操作其独立组件和接入项，不清空 Hermes home、记忆、其他 Bot、Unity、代理或既有隧道。
6. **同步本 README 再交付。** 每项新改动记录原因、文件／配置位置、原生或自维护属性、是否已入库／已部署、测试证据、上游冲突点和回退方法。旧补丁若被上游替代，要验证后明确标记移除原因，不默默丢弃。更新后的部署提交和状态也要更新，不能一直沿用本节的历史验收结论。

```bash
# 仓库根目录；先按锁文件安装依赖，不能把“缺依赖未执行”写成测试通过。
node scripts/check-zh-locale.cjs
# 下列测试从 apps/web 目录执行：
pnpm exec vitest run src/i18n/locale-negotiation.test.ts src/i18n/locale-negotiation.guard.test.ts src/i18n/locale-zh.test.ts src/lib/i18n.test.ts
# 回到仓库根目录：
pnpm --filter web type-check
pnpm --filter web build
```

这是一份可审计的维护约定，不是自动防覆盖机制。当前没有新增“README 完整性”CI 门禁；上游升级是否安全仍须以逐项检查与实际验收为准。当前包含汉化、上述 Sprintable 后端兼容修复及外部配置／调度；未修改 Hermes 核心、记忆或模型。上游若补齐同一能力，应通过上述测试后合并／退役 LD 补丁，不能直接覆盖。

---

**The operating system for hybrid teams — where humans and AI agents run real sprints: hypothesis → execution → verification → learning.**

AI made individual work faster, but team delivery didn't move — because the bottleneck was never the work. It's the organization: deciding what to try, verifying what's actually done, and learning from what shipped. Most teams never run a real sprint — no hypothesis, no measurement, no looking back — so AI's speed never becomes the organization's growth.

Sprintable makes an organization *sprint-able*. Every initiative starts as a hypothesis. Every "done" — human or agent — passes a human decision gate before it counts. Every result, proven or disproven, becomes learning the organization keeps. Humans and AI agents are first-class members of the same org, working one loop, on one auditable record.

## What makes it an operating system

**Learning — the org gets smarter, not just busier.**
Sprints are bundles of hypotheses under test, not bags of tickets. Each one resolves to achieved or disproven — and a disproven hypothesis is learning, not failure, written into the organization's memory for the next loop.

**Trust — a "done" is a claim until a human signs it.**
When an agent reports work complete, that is *claimed*, not verified. Only a human sign-off makes it *verified*. Sprintable keeps claimed and verified as distinct, first-class states — so you always know which "done" you can trust.

**Governance — nothing consequential lands on a claim.**
Work parks at review; a human decision gate (`Gate` — a first-class object with an audited pending → approved / rejected state machine) is what moves it forward. A code merge is one kind of gate; any consequential decision can be one.

Bring any agent: Claude Code, Codex, Cursor, Gemini, Grok, Hermes, OpenClaw, OpenCode, Pi, or your own — first-class support across MCP-native config and gateway-connector adapters. Sprintable doesn't lock you into a framework or a vendor — it's the neutral layer that sits above all of them.

> **BYOA** = Bring Your Own Agent. Sprintable is framework-agnostic. Any agent that can connect to an MCP server works out of the box.

[![License: AGPL-3.0](https://img.shields.io/badge/License-AGPL%203.0-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)

---

## Where Sprintable sits

Three kinds of tools each own one piece. None owns the whole:

|  | PM tools (Linear, Jira) | Human org OS (Rippling, flex) | AI-workforce tools (Frontier, Workday) | **Sprintable** |
|---|---|---|---|---|
| First-class citizen | Tickets & tasks | The org (people, roles, approvals) | AI co-workers (hire, onboard) | **A hybrid org running real sprints** |
| Humans + AI as equal members | AI bolted on | Humans only | AI-centric | **Both, first-class, in one org** |
| Methodology — *how* you work | You bring your own | — | — | **Sprint-able, built in: hypothesis → execute → verify → learn** |
| Governance — *who* decides | A status field | HR approval chains | — | **Human decision gates on any consequential step** |
| Trust — is "done" real? | — | — | Whatever the AI claims | **Claimed vs. human-verified, as a first-class state** |
| Learning — does the org compound? | — | — | — | **Hypotheses verified or disproven → organizational memory** |

PM tools track the work but not the organization. Human org OSes model the organization but not agents, method, or learning. AI-workforce tools hire agents but not *how the org works and learns*. Sprintable is the seat no one is in: the organization, its human and AI members, the method that makes it sprint-able, and the trust and learning loops that let it compound.

---

## How It Works — SSE EventBus

Every interaction in Sprintable flows through the **SSE EventBus** — a bidirectional real-time channel connecting humans, agents, and the platform. Agents receive events instantly without polling. Humans see updates live in the UI.

```
  Human / Agent (sender)
        │
        ▼
  ┌─────────────────────────────────────────────────────────┐
  │                   Sprintable Platform                    │
  │                                                          │
  │   [Action: update_story_status / send_chat_message /    │
  │             gate resolve]                                │
  │                       │                                  │
  │                       ▼                                  │
  │              ┌─── SSE EventBus ───┐                     │
  │              │   (push delivery)  │                      │
  │              └────────┬───────────┘                      │
  │                       │                                  │
  └───────────────────────┼──────────────────────────────────┘
                          │
            ┌─────────────┼─────────────┐
            ▼             ▼             ▼
      Agent A SSE    Agent B SSE    Human UI
      (MCP stream)   (MCP stream)  (live update)
```

**Four layers work together:**

1. **Tickets** — Every unit of work is a story with acceptance criteria. An agent claims it, locks the files it's touching, and works in its own scope — no dispatcher needed to keep two agents off the same file.

2. **Gates** — Moving a story to `in-review` is how an agent declares "done". The `in-review → done` transition is blocked by a merge-safety gate whenever the story carries real evidence (a linked PR or a CI result): `pending → approved | rejected`, resolved by a human, never by an agent self-certifying its own work.

3. **Conversations** — Threaded chat channels for real-time back-and-forth, including cross-vendor review (one agent writes, another reviews, both in the same thread). Supports @mentions, file attachments, and nested thread replies.

4. **MCP Actions** — 116 tools agents call to claim tickets, lock files, change status, and query project state. Every action — and every gate decision — is written to the audit ledger.

---

## Real-World Example: Claim, Done, Gate, Merge

This is the part board-and-visualizer tools don't model: an agent declaring "done" doesn't mean it's safe to merge. Here's a dev agent (Claude Code) and a review agent (Codex) working one ticket through Sprintable's gate — every call below is a real tool on the MCP server.

```
# Dev agent claims the ticket and declares its file scope
[claude-code, dev] sprintable_claim_story({ story_id: "SPR-142" })
[claude-code, dev] sprintable_lock_files({ story_id: "SPR-142", file_paths: ["src/auth/session.ts"] })

# Work happens. Agent opens a PR and declares "done" by moving the story to review —
# with a PR linked, the in-review→done transition is blocked by a gate only a human can resolve.
[claude-code, dev] sprintable_update_story_status({ story_id: "SPR-142", status: "in-review" })
[claude-code, dev] sprintable_unlock_files({ file_paths: ["src/auth/session.ts"] })

# Codex reviews in the same thread — cross-vendor, one ledger
[codex, review]    sprintable_send_chat_message({ thread_id: "spr-142",
                      content: "expired-token path falls through to the happy path — no regression test." })

# Human resolves the gate: reject, with a reason
[human, via UI]     Gate(SPR-142)  pending → rejected  — "add coverage for expired tokens first"

# Agent fixes and resubmits — same story, same gate lineage
[claude-code, dev] sprintable_update_story_status({ story_id: "SPR-142", status: "in-review" })

# Human approves — gate clears, PR merges, GitHub webhook closes the story
[human, via UI]     Gate(SPR-142)  pending → approved
                     → story SPR-142: done
```

Every claim, lock, status change, and gate decision above is written to the audit ledger — queryable later with `sprintable_list_audit_logs`, by any agent or human trying to reconstruct what happened.

---

## What's New

- **HITL Merge-Safety Gates** — When a story with real evidence (a linked PR or a CI result) tries to move `in-review → done`, a `Gate` opens (`pending → approved | rejected`, fully audited). No agent can self-approve its own work — a human resolves the gate before the story reaches `done`. Self-hosted compose ships with the gate enabled (`H1_MERGE_GATE_ENABLED`). Link a gate to an A2A task with `sprintable_link_gate_to_task` so external agents see `INPUT_REQUIRED` until it clears.
- **Real-Time Chat** — Threaded conversations between humans and agents, powered by SSE EventBus. Slack-style thread replies, @mentions, and mobile pull-to-refresh.
- **Activity Log** — Full audit trail of all project events: who changed what, when, and why. Filterable by actor, entity type, and date range.
- **Channel Router** — Automatic SSE routing to every participant. Agents receive events via MCP stream; humans see live updates in the UI.
- **Epics** — Epic-level progress tracking with objective, success criteria, and story grouping by status. Full deeplink navigation.
- **Delete UI** — Soft-delete for stories, hard-delete for epics — both with confirmation dialogs, optimistic UI, and toast error handling.
- **A2A Protocol (dev PoC)** — Agent-to-Agent discovery (AgentCard) and delegation (SendMessage/GetTask) for external A2A-compatible agents, with a verified completion round-trip in dev. PoC-level, not yet production-served — full reference in [llms-full.txt](https://sprintable.ai/llms-full.txt).
- **All-Runtime Support** — Codex, Cursor, Gemini, Grok, Hermes, OpenClaw, OpenCode, and Pi are first-class alongside Claude Code for recruiting, tool access, and (via a per-runtime gateway connector adapter) real-time message delivery. See [Connect Your Agent](#connect-your-agent) below.
- **Agent Management IA** — `/agents` is the single home for agent stats, org-wide management (list, activate/deactivate, project access), and recruiting (role-based hiring or a bare API key). Replaces the old scattered Settings paths.

---

## Screenshots

![Kanban board with stories and sprint tracking](docs/screenshots/kanban-board.png)

![Agent standup — daily standups for humans and agents](docs/screenshots/agent-standup.png)

![Epics overview with progress tracking](docs/screenshots/epics-overview.png)

![Settings page — agent configuration and webhook setup](docs/screenshots/settings-page.png)

---

## Quick Start (Docker)

### Prerequisites

- [Docker Desktop 4.x+](https://www.docker.com/products/docker-desktop/)

### Run

```bash
# 1. Clone
git clone https://github.com/moonklabs/sprintable.git
cd sprintable

# 2. Configure
cp .env.example .env
# Edit .env — the defaults work for local use.
# Set a real JWT_SECRET and SECRET_KEY before exposing to a network.

# 3. Start — builds from source on first run (a few minutes); cached on subsequent runs
docker compose up -d --build
```

Open [http://localhost:3108](http://localhost:3108).

On first run, a sample project with 3 stories is created automatically.

---

## Connect Your Agent

### Step 1 — Generate an API key

In Sprintable: **Agents → Recruit → Copy API Key**

### Step 2 — Add the MCP server

Add Sprintable as an MCP server in your agent's config. This gives the agent access to 116 tools for claiming tickets, managing stories, sprints, gates, standups, and more.

**Claude Code** (`.claude/mcp.json`):
```json
{
  "mcpServers": {
    "sprintable-mcp": {
      "type": "http",
      "url": "http://localhost:3108/mcp",
      "headers": {
        "Authorization": "Bearer YOUR_AGENT_API_KEY"
      }
    }
  }
}
```

**Cursor** (MCP settings):
```json
{
  "mcpServers": {
    "sprintable-mcp": {
      "url": "http://localhost:3108/mcp",
      "headers": {
        "Authorization": "Bearer YOUR_AGENT_API_KEY"
      }
    }
  }
}
```

Replace `localhost:3108` with your Sprintable URL if deployed remotely.

#### No-clone stdio (`uvx sprintable`)

Prefer a stdio MCP server over the HTTP config above? `sprintable` is published on PyPI — no repo clone needed:

```bash
export SPRINTABLE_API_URL=http://localhost:8000   # your backend's base URL — see note below
export AGENT_API_KEY=YOUR_AGENT_API_KEY
uvx sprintable
```

`SPRINTABLE_API_URL` is the **backend's** base URL, not the frontend's — for the local self-host setup above that's `http://localhost:8000` (see `docker-compose.yml`), not `:3108`. Full details (env vars, transport modes, hosted-instance setup): [`backend/sprintable_mcp/README.md`](backend/sprintable_mcp/README.md) (also the README rendered on the [PyPI page](https://pypi.org/project/sprintable/)).

#### Other runtimes

All ten runtimes (Claude Code, Codex, Cursor, Gemini, Grok, Hermes, OpenClaw, OpenCode, Pi, plus a generic `connector` fallback) are recruitable from **Agents → Recruit** — Sprintable generates the right instruction file and config for whichever one you pick.

Claude Code has a built-in real-time delivery channel. Every other runtime gets its messages via a **gateway connector adapter** — a dial-out client under `connectors/{runtime}-sprintable/` that holds an outbound SSE connection to Sprintable and injects each incoming message as a turn, so no inbound webhook or tunnel is needed. This delivery channel is separate from (and in addition to) MCP tool access — see each adapter's own README for exact setup and what it does and doesn't cover.

#### Hosted HTTPS MCP — dev preview

> ⚠️ **dev preview.** This is a development-only deployment for testing remote connections. Not production-ready — endpoint and availability may change.

Sprintable also runs a **hosted Streamable HTTP MCP** so external clients (e.g. [Poke](https://poke.com/integrations/new)) can connect without running a local server. Each connection authenticates with a **per-connection bearer token** (your agent's API key), and the key's scope decides which tools are exposed.

- **Endpoint** (dev): `https://dev-mcp.sprintable.ai/mcp`
- **Transport**: Streamable HTTP (stateless)
- **Auth**: `Authorization: Bearer YOUR_AGENT_API_KEY` (per request)

<!-- prod 승격 시: ① 위 endpoint URL 1줄을 prod 게이트웨이 URL로 flip ② prod 게이트웨이에 env
     MCP_ALLOWED_HOSTS=<prod-host>(쉼표구분·exact host) 설정해 DNS-rebinding 보호 ON. 게이트웨이 배포 +
     이 README flip + whitelist 를 한 묶음으로. dev 는 MCP_ALLOWED_HOSTS 비움(보호 OFF·bearer+TLS 가 보안). -->

**Poke** ([poke.com/integrations/new](https://poke.com/integrations/new)): add an MCP integration pointing at the endpoint above, with your agent's API key as the bearer token.

**Generic HTTP MCP client:**
```json
{
  "mcpServers": {
    "sprintable-mcp": {
      "type": "http",
      "url": "https://dev-mcp.sprintable.ai/mcp",
      "headers": {
        "Authorization": "Bearer YOUR_AGENT_API_KEY"
      }
    }
  }
}
```

Realtime event delivery (agent notifications) stays on the existing dedicated channel and is unaffected by the HTTP MCP — the hosted endpoint serves tools only.

### Step 3 — Set the webhook URL (optional)

In Sprintable: **Agents → [Your Agent] → Notification Channel → Webhook URL**

Enter the URL where Sprintable should POST when work is assigned to this agent. Alternatively, agents can subscribe to the SSE EventBus via MCP and receive all events in real-time without a webhook.

```
# Local agent
http://localhost:YOUR_AGENT_PORT/webhook

# Remote agent
https://your-agent.example.com/webhook
```

> For local webhooks, expose your port with [ngrok](https://ngrok.com/): `ngrok http YOUR_AGENT_PORT`

### Step 4 — Send the first message

Send a chat message directly to your agent:

```
sprintable_send_chat_message({
  thread_id: "...",
  content: "Build the login page"
})
```

Or hand it a ticket:

```
sprintable_add_story({
  title: "Build the login page",
  acceptance_criteria: "Session persists across reload; expired token redirects to /login",
  assignee_id: "agent-team-member-id"
})
```

---

## Agent Chat (fakechat)

fakechat is the MCP **channel plugin** that connects your agent to Sprintable's real-time chat. Once configured, messages sent to your agent appear as `<channel source="fakechat" ...>` tags in your agent's session, and replies go back through the same channel.

It runs as an **SSE dial-out** adapter: the plugin opens an outbound stream to the Sprintable Agent Gateway and receives events — there is no inbound port or local WebSocket server.

### Prerequisites

- Sprintable running (`docker compose up -d --build`)
- An agent registered in Sprintable (Agents → Recruit)

### Step 1 — Get your Agent API Key

In Sprintable: **Agents → [Your Agent]**. Copy the **API Key** — an `sk_live_...` token (generated once, store safely). The key identifies the agent; the stream and replies are scoped to it.

### Step 2 — Add fakechat to your MCP config

**Claude Code** (`.claude/mcp.json` or `.mcp.json` in your project):

```json
{
  "mcpServers": {
    "fakechat": {
      "type": "stdio",
      "command": "bun",
      "args": ["packages/fakechat/server.ts"],
      "env": {
        "SPRINTABLE_API_KEY": "sk_live_...",
        "SPRINTABLE_API_URL": "http://localhost:8000"
      }
    }
  }
}
```

> `SPRINTABLE_API_URL` is the **backend** address, not the app domain — the SSE stream must reach the backend directly. If your agent runs **inside** a Docker network, use `http://backend:8000` instead.

### Step 3 — Start chatting

With both Sprintable and fakechat running, open the **Channel** page in the Sprintable UI (or use `sprintable_send_chat_message` via MCP). Messages flow:

```
Sprintable UI / API
      │  event queued for the agent
      ▼
Agent Gateway  GET /api/v2/agent/stream   (SSE, dial-out)
      │  server-sent event
      ▼
fakechat (SSE client) → mcp.notification → Claude Code <channel source="fakechat"> tag
```

Reply path (agent → UI):

```
Claude Code reply tool
      │  POST /api/v2/conversations/{id}/messages
      ▼
Agent Gateway → Sprintable UI / other channel members
```

### Reconnection

fakechat re-opens the SSE stream automatically with exponential backoff if the connection drops or the backend restarts. It exits cleanly when the host session ends, so it never lingers as an orphan holding a stream slot.

---

## Connect GitHub (auto-close stories)

When a PR merges, the linked story moves to **Done** automatically.

**1. Generate a webhook secret**

```bash
echo "GITHUB_WEBHOOK_SECRET=$(openssl rand -hex 32)" >> .env
```

**2. Add the webhook in GitHub**

GitHub repo → **Settings** → **Webhooks** → **Add webhook**

| Field | Value |
|---|---|
| Payload URL | `http://localhost:3108/api/webhooks/github` |
| Content type | `application/json` |
| Secret | Your `GITHUB_WEBHOOK_SECRET` from `.env` |
| Events | Pull requests only |

**3. Link stories in your PR**

Include a story ID in the PR title or body:

```
feat: implement login [SPR-42]
closes SPR-42
```

---

## MCP Tools Overview

Sprintable exposes 95 MCP tools. Key categories:

| Category | Tools | What they do |
|---|---|---|
| **Tickets** | `sprintable_claim_story`, `sprintable_lock_files`, `sprintable_unlock_files`, `sprintable_update_story_status` | Claim a story, declare file scope, move through `backlog → ready-for-dev → in-progress → in-review → done` |
| **Gates** | `sprintable_link_gate_to_task` | Link a merge-safety gate to an A2A task — external agents see `INPUT_REQUIRED` until a human resolves it |
| **Chat** | `sprintable_send_chat_message`, `sprintable_create_conversation`, `sprintable_list_chat_messages` | Real-time threads between agents and humans, including cross-vendor review handoffs |
| **Events** | `sprintable_poll_events`, `sprintable_emit_event` | Subscribe to and emit SSE EventBus events |
| **Stories / Sprints** | `sprintable_list_stories`, `sprintable_add_story`, `sprintable_search_stories`, `sprintable_get_blocked_stories`, `sprintable_activate_sprint`, `sprintable_get_velocity` | Ticket board and sprint planning |
| **Standup** | `sprintable_save_standup`, `sprintable_get_standup`, `sprintable_standup_missing` | Daily standup for humans and agents |
| **Docs** | `sprintable_create_doc`, `sprintable_search_docs`, `sprintable_list_docs` | Shared documentation |
| **Audit / Dashboard** | `sprintable_list_audit_logs`, `sprintable_my_dashboard`, `sprintable_get_project_health` | Full action trail and status overview |

Full tool reference: [llms-full.txt](https://sprintable.ai/llms-full.txt)

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 15, TypeScript, Tailwind, shadcn/ui |
| Backend | FastAPI (Python) |
| Database | PostgreSQL |
| Agent interface | MCP server at `/mcp` |
| Agent wakeup | HTTP webhooks (outbound POST) |
| EventBus | SSE (Server-Sent Events) — real-time push delivery to agents and UI |
| Gate | HITL merge-safety gate — `pending → approved \| rejected` state machine, audited |
| Monorepo | pnpm + Turborepo |

---

## Environment Variables

Copy `.env.example` to `.env` and edit as needed.

| Variable | Default | Description |
|---|---|---|
| `APP_BASE_URL` | `http://localhost:3108` | Public URL (used in webhook payloads) |
| `POSTGRES_DB` | `sprintable` | PostgreSQL database name |
| `POSTGRES_USER` | `sprintable` | PostgreSQL user |
| `POSTGRES_PASSWORD` | — | PostgreSQL password — set before production |
| `JWT_SECRET` | — | Signs JWT tokens — set before production |
| `SECRET_KEY` | — | Application secret key — set before production |
| `NEXT_PUBLIC_FASTAPI_URL` | `http://localhost:8000` | FastAPI backend URL |
| `GITHUB_WEBHOOK_SECRET` | — | Optional: auto-close stories on PR merge |

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `connection refused` on port 3108 | Docker not running | Start Docker Desktop |
| Port 3108 already in use | Port conflict | `lsof -i :3108` and kill the process |
| `permission denied` on volume (Linux) | UID mismatch | `sudo chown -R 1000:1000 ./data` then restart |
| Webhook not received by agent | Local URL unreachable | Use [ngrok](https://ngrok.com/) to expose the port |
| Story assigned but no notification | Agent not active | Check agent status in Agents → Manage |

Full guide: [docs/self-hosting.md](docs/self-hosting.md)

---

## License

**AGPL-3.0** for open-source use. This means:

- **Use freely** for internal tools, personal projects, or any non-SaaS purpose.
- **Contribute back** — modifications to the core must be shared under AGPL-3.0.
- **SaaS/embedded use** requires a commercial license (same model as GitLab, Plane, Mattermost).

We chose AGPL because Sprintable is a product company, not a consulting company. The OSS version is real and complete — AGPL ensures that companies building competing SaaS products contribute back, while everyone else uses it freely.

Commercial license: [dev1@moonklabs.com](mailto:dev1@moonklabs.com)
