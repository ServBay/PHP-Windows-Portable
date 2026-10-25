# Windows v2 的 PHP 独立资产收集

`scripts/collect_split_assets.py` 离线收集现有 producer 的原始 ZIP。它不编译、不执行 DLL/PHP、不联网、不上传，不改既有 merged 包，也不生成最终 v2 core/module 包。PHP 自带扩展继续留在原始 core runtime ZIP；此次 prepare 选择的第三方扩展各自保留独立 runtime ZIP。

现有 `.github/workflows/build.yml` 将 core 原始 `artifacts/` 保存为 `php-build-artifacts-<arch>-<nts|ts>`，将各扩展的 `artifacts/` 保存为 `extension-<matrix.name>-<display_version>-<arch>-<nts|ts>`。`no-extensions.zip/.7z` 是这些 core ZIP 的外层集合，不能作为本脚本的 core runtime 输入。扩展顶层 runtime ZIP 与 `logs/` 中同名 ZIP 必须按完整相对路径区分。

支持消费收据的新 producer 在每个扩展分组根同时保存唯一的
`consumed-core.json`。它由实际选中的 core runtime/devel ZIP 在解压前按字节计算，并绑定最终扩展 runtime ZIP；它不是安装载荷，不能进入 runtime ZIP 或 `logs/` ZIP。历史 producer 没有该文件时仍可收集，但
`extension_consumed_core_hashes` 保持 pending。

收据的 `extension.requested_ref` 是 prepare 的原始请求 ref，`extension.ref` 是 producer 用于产物名的归一化 ref（例如 PR 的 `refs/pull/123/merge → 123`）。collector 分别绑定两者；普通 tag/branch 两者相同。

## 调用

Python 标准库即可运行，没有第三方依赖：

```python
collect_split_assets(
    core_artifacts,       # 下载后原始 core artifact 内容目录，顶层为原始 ZIP
    extension_artifacts,  # 父目录，每个下载的 extension artifact 保留完整分组名
    selected_extensions, # 此次 prepare 已选择、过滤后的 JSON 数组
    build_context,       # 由 producer 明确提供的下述对象
    output_dir,          # 必须不存在，其父目录必须已存在，且位于输入目录外
)
```

```sh
python3 scripts/collect_split_assets.py \
  --core-artifacts /work/core-artifacts \
  --extension-artifacts /work/extension-artifacts \
  --selected-extensions /work/selected-extensions.json \
  --build-context /work/build-context.json \
  --output-dir /work/split-assets
```

`core_artifacts` 的本地目录名可自定，清单中的来源 artifact 名由实际 producer 命名协议生成。`extension_artifacts` 必须保留各分组名，不能用 merge-multiple 将它们合并。没有选中第三方扩展时，传空数组和真实空父目录即可收集 core-only 资产；这不改变现有 Release workflow 的条件。

## 输入 schema

`build_context` 仅接受以下字段，全部必填。以下值是说明用合成示例，不是已核实的生产运行证据：

```json
{
  "producer": {
    "repository": "ServBay/PHP-Windows-Portable",
    "commit": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    "run_id": 123,
    "run_attempt": 1
  },
  "display_version": "8.2.35",
  "source_ref": "8.2.35",
  "build_version": "8.2.35",
  "build_branch": "",
  "arch": "x64",
  "thread_safe": "nts",
  "core_runtime_filename": "php-8.2.35-nts-Win32-vs16-x64.zip",
  "core_devel_filename": "php-devel-pack-8.2.35-nts-Win32-vs16-x64.zip"
}
```

| 字段 | 精确含义 |
| --- | --- |
| `producer.repository` | 执行此次 producer workflow 的公开 `owner/repository` 名称，不是 URL 或本地路径 |
| `producer.commit` | 该 producer run 的 40 位十六进制 commit；不是 action 的 resolved commit |
| `producer.run_id` / `run_attempt` | GitHub run ID 与 attempt，均为正整数 |
| `display_version` | prepare 的展示版本，用于外层 extension artifact 分组 |
| `source_ref` | prepare 的实际来源请求，例如版本、commit 或 master，不等同于展示版本 |
| `build_version` | prepare 传给 SDK/扩展构建环境的版本请求 |
| `build_branch` | prepare 的 SDK 分支请求；stable/testing 的真实值是空字符串，development 可为 master |
| `arch` | producer 真实枚举 `x64` 或 `x86`；本索引不将它改名为最终 v2 架构枚举 |
| `thread_safe` | producer 真实枚举 `nts` 或 `ts`，不是布尔值 |
| `core_runtime_filename` / `core_devel_filename` | 当前 producer 确认的原始顶层 ZIP 名；脚本不从版本或 VS 映射表猜名称 |

core 的 TS 名称是 `php-<version>-Win32-<toolset>-<arch>.zip`，没有 `-ts-`；NTS 有 `-nts-`。脚本交叉检查 core runtime/devel 的角色、版本、toolset、架构和线程模式。这里核对的是文件名声明的一致性，不能证明 PE 架构、实际编译器版本或 ABI。

`selected_extensions` 必须是此次 prepare **完成版本过滤后的**数组，不能在收集时重读当前默认表。每项仅含 `name/url/ref/args/libs`，全部必填；`args`、`libs` 的真实类型是字符串，包括空字符串。例如：

```json
[{"name":"redis","url":"https://github.com/phpredis/phpredis","ref":"6.3.0","args":"","libs":""}]
```

`name` 来自 matrix，用来选择 artifact 分组；runtime ZIP 的内部 `package_name` 可以不同，例如 matrix.name 为 `http`，内部名称为 `pecl_http`。内部 ZIP 只核对 producer 已知命名后缀的架构和线程模式，不按 matrix.name 推导 DLL 名，也不重命名 DLL/PDB/依赖资源。`url/ref/args/libs` 都是请求输入，不是实际 resolved source/configure/dependencies 的证明。

调用者应只提交公开、无凭据的输入。脚本拒绝未知字段、含认证信息/query/fragment 的 URL，以及明显本地的 URL；不会查环境变量、Git 配置或密钥。URL 格式检查不访问网络，也不证明远端仓库真实性。

## 输出 schema：`servbay.php-split-assets.v1`

新目录中只包含完整原字节资产和最后写入的 `split-assets.json`。API 返回与该 JSON 相同的对象：

| 顶层字段 | 类型与含义 |
| --- | --- |
| `schema` | 固定字符串 `servbay.php-split-assets.v1`，是 producer 资产索引版本 |
| `publishable_v2` | 固定 `false`；不能直接传给 v2 Uploader/backend 当安装包 |
| `build_context` | 经过校验的输入对象原值，包括空 `build_branch` |
| `selected_extensions` | 此次请求列表原值，不追加未选择模块 |
| `native_evidence.status` | 固定 `pending` |
| `native_evidence.missing` | `core_abi`、`actual_toolchain`、`crt_imports`、`resolved_action_commit`、`extension_consumed_core_hashes`、`native_module_load`；仅当所有选中扩展都有完整匹配收据时移除 `extension_consumed_core_hashes` |
| `extension_consumption` | `status` 为 `unavailable`、`partial` 或 `complete`；`validated` 为已核对收据的 path-free 摘要 |
| `source_archive_semantics` | 明确当前 action 的 src ZIP 在补丁前生成，不能称为 patched source 快照 |
| `assets` | 每个收集文件恰好一个对象，字段见下表 |

| `assets[]` 字段 | 类型与含义 |
| --- | --- |
| `role` | 下述固定角色之一 |
| `extension` | 仅 extension 角色有，等于 matrix.name |
| `source_artifact` | 原始完整 artifact 名，不含本地绝对路径 |
| `source_path` | 相对于该 artifact 的路径；例如 `logs/<name>.zip` |
| `original_filename` | 原文件 basename，即使角色未知也完整保留 |
| `filename` | 输出 basename，角色/模块前缀保证不同资产不覆盖；日志额外使用确定性序号区分子目录同名文件。消费者应读此字段，不能自行拼接 |
| `bytes` | 原始资产实际字节数，整数 |
| `sha256` | 原始资产完整字节的 SHA-256，小写 64 位十六进制 |
| `members` | ZIP 资产必有；非 ZIP 日志没有。按 ZIP 原始成员顺序记录每一个文件/显式目录 |

`members[]` 精确包含 `path`（ZIP 原始安全相对路径，目录保留末尾 `/`）、`type`（`file` 或 `directory`）、`bytes`（解压后的实际字节数）、`sha256`（逐成员完整内容哈希）。空目录的字节数为 0，哈希为空内容哈希。隐式父目录不伪造成 ZIP 原始成员。

角色：

- `core-runtime`：明确指定的唯一 runtime ZIP，要求顶层有真实文件 `php.exe`。
- `core-devel`：明确指定的唯一 devel ZIP，要求存在真实文件 `php.h`。
- `core-source`：`php-*-src.zip`；记录原始 source ZIP 的字节，不声称已应用补丁。
- `core-debug`：`php-debug-pack-*.zip`。
- `core-test`：`php-test-pack-*.zip`。
- `core-ancillary`：其他 core 顶层 ZIP。未知角色如实记录，不能被消费者当 runtime 使用。
- `extension-runtime`：选中 artifact 内唯一顶层 ZIP，要求顶层有 `php_*.dll` 文件，保留其中所有文件。
- `extension-consumption-evidence`：唯一顶层 `consumed-core.json`，原字节冻结并以 `evidence--<extension>--consumed-core.json` 输出。
- `extension-log`：选中 artifact 的 `logs/` 子树内全部普通文件，含同名 ZIP 和 `build.log`，仅供审计。

所有角色都以真实文件/成员逐一计算哈希；并不会因为标成日志或源码就跳过 ZIP 校验。merged 包不是输入，也没有被覆盖或拆删。

## 失败与一致性

拒绝缺 core/devel、重复 runtime/devel 候选、缺选中模块、未知分组、多顶层 module payload、错误架构/线程、其他 module 子树、非平铺 core artifact，以及用 no-extensions 外层集合假冒 runtime。输入树和 ZIP namespace 都检查重复、大小写/父目录冲突、危险 Windows 路径、链接和特殊文件；ZIP 另检查加密、完整读取、大小和 CRC。不会将任何 ZIP 成员解压到文件系统，更不会执行载荷。

收集先对输入树建立完整字节清单，再冻结到任务临时目录，比较每一份冻结文件哈希，完成全量 ZIP 校验后重新检查原输入树未变化。输出只从冻结副本复制；全部输出再次核对字节数/哈希，最后才写清单。已有输出目录一律拒绝。发生写盘错误时可能留下未完成的输出目录，缺少完整清单表示失败，不能上传；脚本不会删除用户目录或就地重试覆盖。

有匹配消费收据时，脚本证明该扩展记录的 runtime/devel 实际输入和最终 ZIP 与同组冻结资产一致；缺失收据的历史产物不会被推测成匹配。该证据仍不能证明 ABI、实际工具链、CRT、DLL 闭包或原生加载成功，也不会把 `publishable_v2` 改成 true。下一步需 Windows 原生证据和 Builder 的最终目录转换；最终 v2 host SHA 必须指向最终 v2 core archive，不能拿这里的原始 runtime ZIP SHA 代替。

## 验证

测试使用标准库 `unittest` 和合成真实 ZIP，不编译、联网或上传：

```sh
python3 -m unittest discover -s tests -p 'test_collect_split_assets.py' -v
```

项目授权范围内在 `macOS 26 for Runtime v2` VM 执行，宿主机不执行项目命令。真实 producer artifact 的完整性与原生运行验收应另外记录，不能用合成测试替代。

## Release 持久化接线

`create-release` 仍先下载现有 merged artifact，再独立下载该次 run 的
`php-build-artifacts-<arch>-<nts|ts>` 到 `split-inputs/core`，以及精确匹配
`extension-*-<display_version>-<arch>-<nts|ts>` 的扩展 artifact 到
`split-inputs/extensions`。扩展下载明确 `merge-multiple: false`，保留每个 artifact 的分组目录。
Checkout 固定到 `github.sha`，使用 `producer-source` 独立目录，避免 checkout 初始化清理已先下载的
`release-assets`；Python 沿仓库 action 约定使用 `actions/setup-python@v5`。

```sh
python producer-source/scripts/prepare_split_release.py \
  --core-artifacts split-inputs/core \
  --extension-artifacts split-inputs/extensions \
  --output-dir split-release-assets
```

helper 接受以下两个 JSON 环境变量，另需 Actions 提供 `GITHUB_OUTPUT`：

- `SPLIT_BUILD_CONTEXT_JSON`：对象，精确包含 `producer`、`display_version`、`source_ref`、
  `build_version`、`build_branch`、`arch`、`thread_safe`。`producer` 精确包含
  `repository`、`commit`、`run_id`、`run_attempt`；其余字段的类型、枚举和含义与前述 collector
  schema 一致。GitHub 的 `run_id` / `run_attempt` 可为纯 ASCII 十进制字符串，helper 将其转换成
  collector 要求的正整数；缺失、空值、错误类型均不提供默认值。`build_branch` 允许空字符串。
- `SPLIT_SELECTED_EXTENSIONS_JSON`：本次 prepare 已完成版本过滤的扩展数组，每项精确包含
  `name`、`url`、`ref` 为必填字符串，`args`、`libs` 为可选字符串。与既有 action 消费语义一致，
  helper 仅将缺少的 `args` / `libs` 补为空字符串，再交给严格 collector；存在的值原样保留，
  错误类型及未知字段仍拒绝。这项规范化不会改变选择列表或重读默认扩展表。

Workflow 将字符串通过 `toJSON(...)` 编码成环境 JSON，选中列表直接传递
`needs.prepare.outputs.extensions-json`；不把这些值插入可执行命令，不再读默认扩展配置。
请求 context 不接受 core 文件名；helper 用 collector 的真实文件名 selector 在下载的 core 顶层
发现唯一 runtime/devel 身份，再把完整 context 和原选中列表交给 `collect_split_assets`。
没有版本到编译器的映射，也不重复 ZIP、路径、字节或哈希校验逻辑。

`split-release-assets` 必须是全新目录。collector 完成后，helper 读取精确的
`split-assets.json`，核对返回收据一致且目录只有该索引和 `assets[].filename` 指定文件。
`files` 多行输出只列出这份索引和这些明确文件；路径若含逗号、glob 元字符或换行会拒绝。
当前 `softprops/action-gh-release@v1` 的 `parseInputFiles` 会先按换行再按逗号拆分路径，
因此合法 Windows 日志名 `logs/build,1.log` 也必须在 helper 边界拒绝，避免收据存在但日志漏传。
不会使用递归通配符。全部验证成功后才追加 `GITHUB_OUTPUT`，多行分隔符保证不等于任何文件路径。
失败不会追加成功的 `files` 输出；可能留下未完成目录，需要调查原因，不能就地覆盖重试。

Release 的 `files` 保留既有四条 merged ZIP/7z/校验文件路径，追加
`steps.split-assets.outputs.files`。tag、job 的 `if`/`needs`、权限和原 merged 打包不变。
`build_extensions=false` 的既有 Release 行为没有在本步骤调整。持久化资产仍是 producer 输入，
收据继续声明 `publishable_v2=false`；本改动没有执行 Actions、创建 Release 或完成 Windows 原生验收。

新增测试解析实际 workflow YAML；需沿用测试环境已有的 PyYAML（helper 运行本身只依赖标准库）：

```sh
python3 -m unittest discover -s tests -v
```

测试包含 NTS/x64 与 TS/x86 的原始 core/devel/source ZIP、两个选中模块、matrix.name 与
package_name 不同、日志 ZIP 与模块同 basename、精确原字节/SHA/bytes/索引/Release 列表、
空 `build_branch`、GitHub 字符串 run identity，以及缺失/重复 core、错误架构线程、缺模块、
非法 JSON/schema/数字类型、损坏 ZIP、已有输出、glob 路径、索引不一致和未索引文件的拒绝。
