# UE MCP 能力测试成果总录

> 自动维护文档：每轮测试后自动更新。最后更新：2026-08-24 v2.5 债务清理轮
> 累计：T1-T9 + v2.4/v2.5 共 58 项测试，51 ✅，3 ⚠️半成，4 ❌；Pitfalls P1-P49；模板 12 个全验证
> 关联：CCC/UE_Test_Report.md（完整过程）、skill unreal-mcp **v2.5.0**（知识库已固化）

## 一、总成绩矩阵

| 轮次 | 域 | 结果 | 明星发现 |
|------|-----|------|---------|
| T1 | 已有能力边界 | 6/6 ✅ | DSL 36节点单写；变量10类；函数图表；PIE闭环 |
| T2 | 未触碰工具集 | 9/10 ✅ | 材质/MI/UMG/Niagara/PCG/DT/CT/SM/Tags 全通；SemanticSearch需在线embedding |
| T3 | 综合小项目 | 3/3 ✅ | 交互门/收集游戏/AI贴图→材质全链路 |
| T4 | C++ 工作流 | 2✅+1⚠️ | UBT编译+BP继承全通；LC热替换最后一跳未证 |
| D | 深挖 | 2✅+1部分 | Slate复活法；/Memory/UEDPIE_ 破案 |
| T5 | 扩展轮 | 7/8 ✅ | **DSL 307节点**；Sequencer+Camera；HUD运行时闭环 |
| T6 | 通信与动画 | 6✅+2⚠️ | BP跨蓝图Cast链全通；GM WorldSettings覆盖生效；PIE蓝图变量写入=边界 |
| T7 | 高级工具+P43 | 4✅+1⚠️ | SkeletalMesh全查询套件(23工具)；GAS引擎测试集；PIE物理模拟运行✅但overlap未触发→P44 |
| T8 | P44攻坚+新域 | 3✅+1❌(P44) | **AutomationTest 8790发现+4/4跑通**；ControlRig 44工具(create+RigVM节点)；PhysicsAsset自动生成11 bodies；P44根因三连 |
| T9 | 收官轮 | 2✅+1❌(P44终) | **Sequencer关键帧全链**(track→section→Location.X双键0→500)；Niagara AddEmitter+SetEmitterData；P44终极真相=**OpenWorld地形埋没**(trace_world破案) |
| v2.4 | 迭代轮(模板补全) | 2/2 ✅ | **spawn_despawn**(PIE 6周期@2s实测)；**save_load**(SaveOK=true+TestSlot.sav 2014B落盘)；P47发现:SaveGame基类实例化但存盘静默false→必须BP子类 |
| v2.5 | 债务清理轮 | 1破解+1定论+1验证 | **债务1破解**: BeginPlay运行时SetSimulatePhysics→真实物理坠落实测(z1500→50)! P38+physics_runtime模板；**债务2定论**: Ctrl+Alt+F11触发LC✓(Live coding succeeded+patch_1)但native热替换✗ P39；**债务3**: 重放置workaround债务1中验证有效 |

## 二、已验证可复用工作流（按价值排序）

### W1. 蓝图逻辑全流程（DSL）`[VERIFIED]`
变量(10类)→事件→函数图表→307节点复杂逻辑，单次 write_graph_dsl+compile+save。
要素：bind复用(R10)/elif链/for嵌套/bool→select转换。

### W2. 碰撞体系 `[VERIFIED]`
sweep命中：mesh提根组件(P7)+bSweep=true+BlockAll+EventHit(AddEvent|Collision|前缀)。
重叠触发：TriggerOnly+bGenerateOverlapEvents+BeginOverlap事件。

### W3. 输入控制 `[VERIFIED]`
EnableInput前置(P9)→IsInputKeyDown(需PC引用P2)→或键盘K2Node_InputKey(create_node非add_event P12)。

### W4. 材质管线 `[VERIFIED]`
create→add_expression(Constant3Vector/VectorParameter/TextureSample)→set_properties(红/PascalCase参数名)→connect_to_output(MP_BaseColor)→recompile→**save**。MI:create(parent)+set_vector_parameter覆盖。

### W5. UMG管线 `[VERIFIED]`
CreateWidgetBlueprint(camelCase)→**先CanvasPanel为根**(P23)→AddWidget子件→set_properties文本→compile→save。
运行时:UserInterface|CreateWidget(:Class)+UserInterface|Viewport|AddtoViewport(P30)。

### W6. AI素材全链路 `[VERIFIED]`
generate_image→下载→import_asset.ps1模板→AssetTools.write_file(py)→Slate控制台"py <path>"→IMPORT_DONE→find_assets+CaptureAssetImage验证。Slate死时Unobserve→Observe复活(P22)。

### W7. C++编译 `[VERIFIED]`
DOTNET_ROOT=引擎.NET10(P25)→写.h/.cpp→关UE→Build.bat→重启带MCP参数。
BP继承:/Script/<Mod>.<Class>父类→CDO可读UPROPERTY。

### W8. PIE运行时验证 `[VERIFIED]`
StartPIE(warmup)→find_actors拿/Memory/UEDPIE_N_路径(P20)→读写实时状态。
截图:CaptureViewport(3D)/SlateInspector.Screenshot(含HUD,P31)。

### W9. 数据资产 `[VERIFIED]`
DataTable:create(schema=引擎struct)+add_rows(raw JSON真数组)。
CurveTable:add_row+add_key({time,value}对象)。StringTable:string_table参数。

### W10. Sequencer `[VERIFIED]`
create_level_sequence(package_path)→open_sequence→create_camera(spawnable→bindingId)。

### W11. BP跨蓝图通信（T6已验证）`[VERIFIED 2026-08-23]`
WorldSettings.DefaultGameMode=BP GM → Player按E → GetGameMode → CastTo<GM名>(Utilities|Casting|) → 取门引用 → CastTo<Door名> → OpenDoor调用。
**关键规律（P40/P41/P42）**：跨BP访问的节点id = `Class|<BP名去掉下划线>|<函数/变量>`（如 Class|BPGridGameMode|GetTheDoor、Class|BPDoor|OpenDoor）；Cast节点输出pin名 = `As<类名去空格>`（如 AsBP Grid Game Mode→AsBPGridGameMode，实测带空格）；Cast的Object pin接非空引用前编译报"undetermined"。

### W12. Tick+RInterpTo补间动画（T6已验证-编译级）`[VERIFIED compile-level]`
if Opening → MakeRotator(cur) + MakeRotator(tgt) → RInterpTo(Current/Target均**Rotator**类型,DeltaTime,InterpSpeed) → SetActorRotation → SetCurrentYaw(.yaw newRot)。
运行时触发验证受阻于P43（PIE蓝图变量不可外部写入）— 编译链完整，逻辑按UE标准。

### W13. Screen Control兜底层 `[VERIFIED]`
原生弹窗:窗口rect截图→AI读坐标→换算点击；或WM_CLOSE跳过。详见references/screen_control.md。

### W14. WorldSettings GameMode覆盖（T6新）`[VERIFIED]`
find_actors(name=WorldSettings) → set_properties DefaultGameMode="/Game/.../BP_GM.BP_GM_C" → PIE中GM实例以BP名出现在PersistentLevel（/Temp/UEDPIE_0_...BP_GM_C_0）。

## 三、全部 Pitfalls 索引（P1-P37）

| # | 标签 | 一句话 | 关键修复 |
|---|------|--------|---------|
| P1 | Pin | Bool进不了运算符 | select转换 |
| P2 | Input | IsInputKeyDown要PC | GetPlayerController |
| P3 | Pin | 重复连接报错 | connected_pins检查 |
| P4 | Flow | 编译错误杀脚本 | compile放最后 |
| P5 | Node | 四种路径格式 | 对应工具对应路径 |
| P6 | Other | MCP未监听 | 启动参数/控制台 |
| P7 | Collision | 根组件决定sweep | 提mesh为根 |
| P8 | Collision | EventHit需sweep/物理 | bSweep=true |
| P9 | Input | 非Pawn无键盘 | EnableInput |
| P10 | Collision | Profile需碰撞形状 | PrimitiveTools件自带 |
| P11 | Node | MakeTransform拼写 | Math\|Transform\| |
| P12 | Node | 键盘事件DSL崩 | create_node |
| P13 | Node | Spawn要_C路径 | 类路径加_C |
| P14 | Pin | 算术只收2参 | 嵌套/bind |
| P15 | Other | Codely先于UE启=无工具 | UE先行 |
| P16 | Node | write_file要绝对路径 | C:/全路径 |
| P17 | Flow | OutputLog抽屉自动收 | 立即snapshot |
| P18 | Other | 原生弹窗阻塞 | screen_control |
| P19 | Flow | 资产不存盘 | save_assets必做 |
| P20 | Flow | PIE实例路径 | /Memory/UEDPIE_ |
| P21 | Node | Slate深度不够 | maxDepth=45 |
| P22 | Flow | Slate多PIE后死 | Unobserve→Observe→等5s |
| P23 | Node | UMG首件成根 | Canvas先行 |
| P24 | Flow | (并入P22) | 同上 |
| P25 | Other | UBT需.NET10+防火墙 | DOTNET_ROOT+netsh |
| P26 | Flow | (并入P20) | 同上 |
| P27 | Flow | (即P19) | save_assets |
| P28 | Node | (即P21) | 45 |
| P29 | Other | LC输出独立窗 | 看patch_N时间戳 |
| P30 | Pin | UMG DSL真名 | Class pin+Viewport\|Addto |
| P31 | Flow | CaptureViewport无HUD | Slate.Screenshot |
| P32 | Node | 长DSL用Python | PS引号地狱 |
| P33 | Other | DataAsset要自定义类 | BP定义DA |
| P34 | Pin | Cast节点动态type_id | CastTo<BP名>_C模式 |
| P35 | Flow | GameMode访问需Cast | GetGameMode→Cast |
| P36 | Node | RInterpTo收Rotator非float | 先MakeRotator包装 |
| P37 | Flow | 跨BP函数调用id | (BP名_C\|函数) 仅同BP；跨BP用Class\|规则 |
| P38 | Node | bool变量b前缀被剥 | 节点id无b（bOpening→GetOpening） |
| P39 | Flow | DSL顶层仅event/fn | 键盘事件必须create_node+连线 |
| P40 | Node | 跨BP节点id规则 | Class\|<名去_>\|<成员> |
| P41 | Pin | Cast输出pin名 | As<类名去空格>（实测含空格AsBP Grid Game Mode） |
| P42 | Flow | Cast Object空引用编译错 | Object必须接具体输出 |
| P43 | Flow | PIE蓝图变量不可外部写 | set_properties对PIE实例BP变量失败（仅transform可） |
| P44 | Collision | PIE中物理下落物overlap未触发 | 根因链已锁定：①trigger体积曾空(mesh丢)→修复bounds 256³✅ ②cube mobility=Static→已确认Movable✅ ③bSimulatePhysics在SMC是**顶层属性**非bodyInstance子属性——两处set均被瞬态实例拒绝→物理半悬停(z=300停滞)。T7那次下落是唯一成功样本。修法候选：通过蓝图Tick AddForce替代物理模拟，或BP模板内置physics cube |
| P45 | Node | 各域create参数名三态 | BP:folder_path+asset_name；CR/LS/ST:path；PA:meshPath+bAssignToMesh；PA查询:physicsAsset(camel)——每个新toolset的create/List必须先查schema |
| P46 | Collision | **P44终极真相：OpenWorld地形埋没一切** | trace_world破案：(0,0)处地形面z≈450，门(z=100)与方块(z=400)全埋地下！方块Tick下落撞地形停在300。修复：**场景操作前先trace_world测地形高度**，Actor抬至地形上方。另：模板改动后已放置实例不自动更新(需重放置)；PIE实例Tick绑定偶发失效(同BP一实例动一实例不动) |

## 四、能力边界（不可做清单）

1. SemanticSearch — 需在线embedding服务
2. LiveCoding热替换最后加载跳 — patch生成≠生效
3. 编辑器运行时全量编译 — LC锁构建必须关UE
4. 引擎通用DataAsset — 需项目自定义类
5. Timeline节点直接创建 — 用Tick+RInterpTo替代(W12)
6. PIE蓝图变量外部写入 — ObjectTools对PIE实例BP变量set失败(P43)；触发逻辑需真实按键或蓝图侧事件
7. DSL顶层键盘事件 — 只能create_node+程序化连线(P39)

## 五、测试资产清单（CCC项目内，已保存）

/Game/TestT1/BP_T11_Complex（307节点压力样本）
/Game/TestT3/M_Brick+MI_Brick_Green+t33_brick（AI材质链）
/Game/TestT5/WBP_HUD+BP_HUDHost+LS_Test+ST_Test+BP_T51_Big
/Game/TestT6/BP_GridGameMode(GetDoor)+BP_Door(OpenDoor+RInterpTo动画)+BP_Player(E键Cast通信链6节点)

**T6 详细记录：**
- T6.1 BP_Door：OpenDoor(NewYaw)函数+Tick RInterpTo动画 ✅（P36 MakeRotator包装修正后编译过）
- T6.2 BP_Player通信链：E→GetGameMode→CastGM→Class|BPGridGameMode|GetTheDoor→CastDoor→Class|BPDoor|OpenDoor(90) ✅（经历P39-P42四坑后全通；重复节点清理术：按type_id分组留最新+ensure补线）
- T6.3 运行时验证：⚠️ GM作为WorldSettings覆盖成功生成PIE实例✅；但PIE蓝图变量(bOpening)ObjectTools写不进去(P43) → 运行时动画触发不可headless验证，逻辑链编译级完整

## 六、T7 详细记录（2026-08-23晚）

| # | 测试项 | 状态 | 详情 |
|---|--------|------|------|
| T7.1 | SkeletalMesh工具 | ✅ | SKM_Starfish(ControlRig模板): verts=1415/lods=1/bones=22/parent查询/add_socket成功。发现：项目无Mannequin，ControlRig模板SKM可用（13个）。23工具 |
| T7.2 | Texture工具 | ✅ | get_size(brick 2048×2048)。仅2工具（轻量集） |
| T7.3 | GAS AttributeSet | ✅ | FindAttributeSetClasses 发现引擎自带 AbilitySystemTestAttributeSet(MaxHealth等)。项目无自定义AS（正常，GAS未启用） |
| T7.4 | P43突破尝试 | ⚠️ | 三方案：①pawn传送进trigger — set_actor_transform teleport不触发BeginOverlap(无sweep)❌；②物理方块下落 — PIE Simulate物理运行✅(z400→152)但overlap未fire→P44(双方overlap events已开仍不通，疑Trigger体积与Root panel几何干扰)；③结论：PIE物理模拟本身可驱动，overlap链需component级事件+几何修正后重试 |
| 附 | 日志假阳性教训 | ✅ | "TRIGGERED"模式匹配到"InvalidateAllWidgets triggered"——日志过滤必须用完整独特串("DOOR TRIGGERED") |

**T7 新 Pitfalls：**

**P44 `[Collision]` PIE物理下落物 Actor级BeginOverlap 未触发**：物理方块(PhysicsActor+双方bGenerateOverlapEvents)落入TriggerOnly体积(300³)内(z=152确认在内)但 EventActorBeginOverlap 不fire。疑因：Root组件(BlockAll panel)与child trigger体积的几何/事件路由。待验证：add_component_bound_event(component级) + panel碰撞改NoCollision。

## 七、T8 详细记录（2026-08-23夜）

| # | 测试项 | 状态 | 详情 |
|---|--------|------|------|
| T8.1 | P44攻坚 | ❌(未通) | 三连修：①trigger体积修复(mesh+scale 3x→bounds 256³✅) ②重放门实例(模板更新✅) ③bSimulatePhysics定位——发现SMC该flag是**顶层属性**（bodyInstance里没有）！但瞬态实例上set被拒(cube悬停z=300)。物理下落仅T7偶然成功一次。结论：编辑器放置实例的物理标志需在BP模板层设置，纯ObjectTools改不动 |
| T8.2 | ControlRig | ✅ | create(path="/Game/.../名")→资产+RigVMModel前向图→create_node(RigUnit_MathFloatAdd)成功。44工具(变量/pin/图操作全套)。P45参数坑:create用path非folder_path |
| T8.3 | AutomationTest | ✅ | DiscoverTests→8790测试可用；RunTestsByFilter(filterExpression="HashToolIdentifier")→**4/4 passed**(引擎MCP自身单测)。ListTests需nameFilter+tagFilter+limit三参 |
| T8.4 | PhysicsAsset | ✅ | CreateFromMesh(meshPath+bAssignToMesh)→自动生成PA_Starfish(11 bodies,自动capsule形状含位置/半径/长度)并assign回网格。17工具全套(body/shape/constraint CRUD) |

**T8 新 Pitfalls：**
P44(更新)：bSimulatePhysics在SMC=顶层属性；瞬态实例set失败→物理需模板层或Tick AddForce驱动
P45(新)：各toolset的create参数名三种风格(BP:folder_path+asset_name / CR+LS+ST:path / PA:meshPath)——新域必先describe查schema

## 八、下轮候选（T9）

- P44 终极方案：BP_Cube模板(内置physics) → 放置 → PIE验证（模板层固化物理标志）
- Niagara深挖：emitter+module增改（T2只测了系统创建）
- Sequencer keyframe（动画曲线写入）
- AI贴图→UMG背景（管线组合）
