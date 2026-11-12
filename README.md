# VezroCAD 家装施工图图层与图形表达标准（提案 v2.0）

> **定位：独立的规范仓库**，不是 VezroCAD 插件源代码。先讨论、校验、试打，再通过版本化的数据契约接入插件。 
> **状态：提案 / 未经 AutoCAD 2027 实机打印验收**（2026-11-12）。

这套规范服务于家装/室内设计：方案平面、拆改、地面铺装、顶棚、机电、定制柜、立面、节点、图纸套输出。核心是**业务对象 / 图形表达角色 / 实体图层 / 视图模板 / 打印样式**五层解耦。

## 最重要的约定

1. **颜色不控制线宽**；实体的线宽默认由图层决定，简单图块允许 Layer 0 + ByBlock，复合图块按角色映射。
2. **遮罩不是填充**；WIPEOUT 所在图层必须保持可打印，框线是否显示由 `WIPEOUTFRAME` 控制，并验证实体绘制顺序。
3. 同一个 DWG 的彩色/黑白打印，切换同名样式的两套 `STB`；**两套 STB 均不覆盖对象线宽**。
4. **图层中文命名、智能对象语义 ID、CAD 图块定义名是不同概念**。旧 `BS-*` 等图层不自动覆盖或重命名。
5. A3 横向为主要纸张，模型真实尺寸、布局 1:1、视口决定比例。
6. 图层目录按需生成，不要求每份 DWG 默认加载全部 142 层。

## 目录

- [`docs/01-总体架构.md`](docs/01-总体架构.md)：五层模型与设计边界
- [`docs/02-图层命名与线宽.md`](docs/02-图层命名与线宽.md)：中文命名、A3 线宽
- [`docs/03-图形表达角色.md`](docs/03-图形表达角色.md)：主轮廓/次轮廓/细线/虚线/遮罩/填充
- [`docs/04-图块遮罩绘制顺序.md`](docs/04-图块遮罩绘制顺序.md)：普通块、动态块、WIPEOUT、智能构件
- [`docs/05-STB打印及A3.md`](docs/05-STB打印及A3.md)：彩色/黑白、Normal 陷阱、A3 验收
- [`docs/06-图纸套与视图模板.md`](docs/06-图纸套与视图模板.md)：同模型多图纸套
- [`docs/07-遗留模板迁移.md`](docs/07-遗留模板迁移.md)：CTB/统帅旧模板兼容
- [`docs/08-验收清单.md`](docs/08-验收清单.md)：CAD 2027 实机测试矩阵
- [`docs/09-迭代路线与待决问题.md`](docs/09-迭代路线与待决问题.md)：先讨论再实施
- [`docs/10-标准依据与边界.md`](docs/10-标准依据与边界.md)：国标/行业标准来源和非强制建议项
- [`docs/11-GitHub初始化与协作.md`](docs/11-GitHub初始化与协作.md)：独立私有仓库建立与迭代流程
- [`docs/adr/0001-拆分图层与表达角色.md`](docs/adr/0001-拆分图层与表达角色.md)：首个架构决定记录
- [`data/layers-v2.json`](data/layers-v2.json)：142 层提案目录，含默认表达角色、稳定键
- [`data/representation-roles.json`](data/representation-roles.json)：13 个图形表达角色
- [`data/view-presets.json`](data/view-presets.json)：9 套施工图显示模板
- [`data/semantic-role-layer-mapping.example.json`](data/semantic-role-layer-mapping.example.json)：智能对象→角色→图层映射示例
- [`assets/stb/`](assets/stb/)：两套命名打印样式，**需要实机试打**
- [`assets/dxf/`](assets/dxf/)：仅作为图层目录（不是生产 DWT）
- [`assets/VZ-图层辅助命令-v2.lsp`](assets/VZ-图层辅助命令-v2.lsp)：只增加缺失图层

## 试用步骤

1. 先备份 DWG/DWT，**不要覆盖你上传的统帅模板**。
2. 把 STB 放到 `STYLESMANAGER` 打开的目录；确认 `PSTYLEMODE=0`。旧 CTB 图请先在**副本**按 AutoCAD 的转换流程处理。
3. `APPLOAD` 加载 LISP，先在当前布局执行 `VZBW` 再执行 `VZLAYERS`。已有同名层跳过不改。
4. 在一张 A3 图中放置墙、柜、马桶、门窗、插座和地砖，重点打印遮罩与层级关系。
5. 用 `VZCOLOR` 切换当前布局，打印彩色版并比对线宽是否恒定。
6. 实机通过 [`docs/08-验收清单.md`](docs/08-验收清单.md) 再发布试用版。

## 约束 / 来源

- 参考 GB/T 50001-2017 与 JGJ/T 244-2011，**本项目自定义值不代表标准原文的强制细则**。
- 参考上传的统帅/类 DOP CTB 线宽层级，但**未解析原 DWT 完整图层表**，不声称一一复刻。
- 不把原始商业模板 CTB、DWT 或客户图纸上传到仓库。见 [`docs/07-遗留模板迁移.md`](docs/07-遗留模板迁移.md)。

## 变更协作

采用 `docs/adr` 记录已确认的架构选择；大改动先发 Issue；更新数据 JSON 后运行 `python scripts/validate.py`；通过打印样张对比才提升状态。详见迭代路线。
