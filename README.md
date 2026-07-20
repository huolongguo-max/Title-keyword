# Title-Keyword 智能分析平台

基于 **Vue 3 + FastAPI** 的京东商智搜索词报表离线分析工具，覆盖上传解析 → 词池分类 → 风险检测 → 标题生成 → 批量优化全链路。

---

## 技术栈

| 层 | 技术 |
|---|------|
| 前端 | Vue 3 + Vite + TypeScript，原生 CSS（macOS Apple 风格） |
| 后端 | FastAPI + Python 3.11+，pandas + openpyxl，纯离线 |
| 设计 | 毛玻璃卡片、苹果蓝主色、SF Pro 系统字体、12px 大圆角 |

---

## 快速启动

### 环境要求

- Node.js ≥ 18
- Python ≥ 3.11
- macOS / Linux / Windows

### 1. 安装依赖

```bash
# 后端
cd backend
pip install -r requirements.txt

# 前端
cd frontend
npm install
```

### 2. 启动服务

```bash
# 终端 1 — 后端（端口 8000）
cd backend
python main.py

# 终端 2 — 前端（端口 5173）
cd frontend
npm run dev
```

### 3. 访问

- 前端页面：http://localhost:5173
- API 文档（Swagger）：http://localhost:8000/docs

---

## 功能流程

```
 📤 上传解析         📊 词池分类        🛡️ 风险检测
 ──────────        ──────────        ──────────
 上传京东商智       自动四级分类        六大规则检测
 搜索词报表         + 质量得分          + 风险评分
      │                 │                  │
      └─────────┬───────┘                  │
                │                          │
                ▼                          ▼
           ✨ 标题生成              🚀 批量优化
           ──────────              ──────────
           三段式拼接              多文件批量处理
           + 新旧对比              + Excel 导出
```

### 1. 上传解析
- 拖拽/点击上传京东商智-搜索词报表（.xlsx/.xls）
- 自动校验 8 个必填字段：搜索关键词、曝光次数、点击次数、点击率CTR、加购次数、成交订单量、成交金额、引流人数
- 数据清洗：去空行、去空格、数值类型转换
- 展示概览卡片 + 分页表格（50条/页）

### 2. 词池分类
- 点击「一键分类」执行四层级自动分类
- **核心成交词池**：成交订单量 > 0，高权重高转化
- **潜力增长词池**：零成交但曝光/点击高于均值
- **无效弱词池**：有曝光无转化，建议剔除
- **冲突违规词池**：含互斥属性词，需人工审核
- 质量得分 0-100：成交金额×0.5 + 点击×0.3 + 曝光×0.2
- 每个词池卡片可折叠，点击词条查看完整指标详情

### 3. 风险检测
- 输入商品标题，一键检测六大降权风险
- ① 属性冲突：互斥属性词同时出现（标准版/尊享版、有线/无线等）
- ② 年份冲突：2+ 不同年份数字
- ③ 规格冲突：多个不同规格数值
- ④ 语义重复：同义词堆砌（礼盒/套装等）
- ⑤ 关键词堆砌：同一关键词重复 ≥2 次
- ⑥ 无意义垃圾词：填充词、纯符号、超长长尾
- 点击风险项自动在标题中高亮违规内容

### 4. 标题生成
- 基于词池数据一键生成最优标题
- 三段式结构：核心大词前置 → 属性词中段 → 热搜词尾部
- 自动去重、去冲突、去无效词
- 可调字数上限（20-50字）
- 词权重明细表 + 新旧标题对比（核心词数、风险变化、权重提升%）

### 5. 批量优化
- 支持多文件拖拽上传（一个文件 = 一个SKU）
- 批量执行全流程：解析 → 分类 → 标题生成
- 结果汇总表格 + 单个SKU详情弹窗
- Excel 导出：SKU、标题、核心指标

---

## 项目结构

```
Title-keyword/
├── backend/
│   ├── app/
│   │   ├── api/routes.py                     # 所有 API 路由
│   │   ├── core/config.py                    # 全局配置常量
│   │   ├── schemas/common.py                 # Pydantic 请求/响应模型
│   │   └── service/
│   │       ├── analyzer.py                   # 搜索词报表解析
│   │       ├── word_classify_service.py      # 四层级分类 + 质量得分
│   │       ├── risk_detect_service.py        # 六大降权风险检测
│   │       ├── title_generate_service.py     # 标题生成 + 新旧对比
│   │       └── batch_optimize_service.py     # 批量处理 + Excel 导出
│   ├── main.py                               # FastAPI 应用入口
│   └── requirements.txt                      # Python 依赖
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── MacButton.vue                 # macOS 风格按钮
│   │   │   ├── MacCard.vue                   # 毛玻璃卡片
│   │   │   ├── MacTable.vue                  # 极简表格
│   │   │   └── WordPoolCard.vue              # 词池卡片（可折叠）
│   │   ├── views/
│   │   │   ├── UploadView.vue                # 上传解析页
│   │   │   ├── KeywordsView.vue              # 词池分类页
│   │   │   ├── RiskView.vue                  # 风险检测页
│   │   │   ├── GenerateView.vue              # 标题生成页
│   │   │   └── OptimizeView.vue              # 批量优化页
│   │   ├── api/client.ts                     # API 请求封装
│   │   ├── router/index.ts                   # 路由配置
│   │   ├── utils/format.ts                   # 数值格式化工具
│   │   ├── assets/global.css                 # 全局样式 + CSS 变量
│   │   ├── App.vue                           # 主布局
│   │   └── main.ts                           # 入口
│   ├── index.html
│   ├── vite.config.ts
│   └── package.json
│
└── README.md
```

---

## API 接口一览

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/health` | 健康检查 |
| POST | `/api/upload/search-word` | 上传搜索词报表 |
| POST | `/api/word/classify` | 四层级分类 + 得分 |
| POST | `/api/title/check-risk` | 标题六大风险检测 |
| POST | `/api/titles/generate` | 最优标题生成 + 对比 |
| POST | `/api/batch/optimize` | 批量多文件优化 |
| POST | `/api/batch/export` | 导出结果为 Excel |

---

## 可配置参数

所有业务常量集中管理，便于后续调优：

| 模块 | 可调参数 | 位置 |
|------|---------|------|
| 分类权重 | 成交金额 0.5 / 点击 0.3 / 曝光 0.2 | `word_classify_service.py` 顶部 |
| 互斥词库 | 20+ 组属性冲突、12 组同义词 | `risk_detect_service.py` 顶部 |
| 标题字数 | 默认 30 字（20-50 可调） | `title_generate_service.py` 顶部 |
| 词数分配 | 前置 2 + 尾部 2 | `title_generate_service.py` 顶部 |

---

## 设计规范

- 主色调：苹果蓝 `#007AFF`，浅灰背景 `#F5F5F7`
- 卡片：毛玻璃 `backdrop-filter: blur(20px)`，12px 大圆角
- 按钮：8px 圆角，三种样式（主/次/危险）
- 字体：`-apple-system, BlinkMacSystemFont, 'SF Pro Display'`
- 深色模式：CSS 变量已预留 `[data-theme="dark"]`
