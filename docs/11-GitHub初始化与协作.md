# GitHub 仓库状态与持续迭代

## 已完成

- 正式仓库：<https://github.com/hanpeiyu/vezrocad-drafting-standard>
- 默认分支：`main`
- 当前可见性：**Public（公开）**。这只是当前事实，不表示已获授权公开第三方资料。
- 当前标准：`v2.0.0` **Draft / 提案**；未通过 AutoCAD 2027 的 A3 黑白/彩色实机打印验收。
- 与插件 `hanpeiyu/VezroCAD` 分离管理；此处不直接改生产插件代码。

## 讨论与变更

1. 设计问题优先创建 Issue，明确使用场景、可选方案、推荐方案、验收办法。
2. 达成决策后增加 `docs/adr/NNNN-主题.md`，标明 Accepted / Superseded 等状态。
3. 修改 `data/` 中图层、角色或视图配置时，必须同步说明兼容性和迁移方法。
4. 使用 Pull Request 审核，CI 只证明数据结构与文件可解析，**不代表 CAD 实机可打印**。
5. 只有通过 `docs/08-验收清单.md`、附 A3 样张和 CAD 版本，才能进入 Production-ready 状态。
6. VezroCAD 插件侧只依赖经过明确版本固定的数据契约，严禁以图层中文名作智能对象唯一身份。

## 遗留模板和公开仓库风险

- 不将原统帅 DWT、CTB、DOP 商业模板、客户图纸、私有标注信息直接上传到 Public。
- 用匿名脱敏的图层清单、样图和映射结果进行讨论。
- 如未来需要公开第三方内部资料，先核对授权；无法确认时应转为 Private。
- 即使后来将仓库改为私有，已公开过的内容也不应视为自动撤回。

## 本地使用

现有仓库已经完成初始化。**不要重新运行首次建仓脚本向非空 main 强推**；直接克隆：

```powershell
git clone https://github.com/hanpeiyu/vezrocad-drafting-standard.git
cd vezrocad-drafting-standard
python scripts/validate.py
python scripts/verify_binary_assets.py
```

检查打印资产时要在 AutoCAD 2027 中使用副本验证；暂不覆盖原生产 DWT 或默认打印文件。
