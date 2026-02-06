# Iconify SVG Skill - 开发计划

## 目标
实现一个 Anthropic Agent Skill，让 AI 能快速搜索并获取合适的 SVG 图标。

## 里程碑

### M1: 基础框架（1-2小时）
- [ ] 创建目录结构
- [ ] 实现 iconify_cli.py 基础 CLI
- [ ] 实现 list-collections / search / get-svg 命令
- [ ] 实现缓存机制
- [ ] 创建 SKILL.md

### M2: 索引和搜索（2-3小时）
- [ ] 实现 build_index.py（SQLite FTS5）
- [ ] 优化 search 命令
- [ ] 实现 LRU 缓存

### M3: 完整功能（2-3小时）
- [ ] 实现 suggest 命令
- [ ] 实现 doctor 检查
- [ ] 实现 attribution 生成
- [ ] 编写测试
- [ ] 完善文档

## 验收标准
1. 能搜索 Iconify 图标集合
2. 返回纯 SVG 代码
3. 支持颜色和尺寸定制
4. 自动处理别名和属性
5. 生成正确的许可证和署名信息
6. 有完整的测试覆盖
