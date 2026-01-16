# 材料属性管理 API (FastAPI + MySQL + Docker)

本项目是一个基于 **FastAPI** 和 **MySQL** 的材料属性管理系统。通过 **Docker** 容器化编排，实现了 CAS 号及复杂材料性质（JSON 格式）的存储、查询与删除功能。

## 1. 项目结构

```text
Material_management/
├── app/
│   ├── main.py          # FastAPI 路由与生命周期管理
│   ├── database.py      # SQLAlchemy 异步引擎配置
│   ├── models.py        # 数据库 ORM 模型
│   ├── schemas.py       # Pydantic 数据验证模型
│   └── crud.py          # 数据库增删改查逻辑
├── .env.example         # 环境变量模板
├── Dockerfile           # 后端镜像构建
├── docker-compose.yml   # 容器编排配置
└── requirements.txt     # Python 依赖

```

## 2. 配置过程描述

本项目采用**环境隔离**与**容器化编排**的配置思路：

* **环境参数化**：通过 `.env` 文件管理敏感信息（如 MySQL Root 密码、普通用户账号）。代码通过 `os.getenv` 动态加载，确保安全性与灵活性。
* **数据库初始化**：在 `docker-compose.yml` 中映射环境变量，使 MySQL 容器首次启动时自动创建 `material_db` 库并建立低权限用户 `app_user`。
* **异步驱动**：采用 `SQLAlchemy` + `aiomysql`。配置了 `pool_pre_ping=True` 和 10s 连接超时，以应对容器环境的网络波动。

## 3. 启动过程描述

遵循 **“数据库优先 -> 健康检查 -> 应用启动 -> 自动建表”** 的流水线：

1. **容器编排**：执行 `docker-compose up`，Docker 首先拉取镜像并启动 `db` 容器。
2. **健康检查**：`db` 容器通过 `mysqladmin ping` 自检，待数据库完全就绪后，状态转为 `healthy`。
3. **应用拉起**：`app` 容器在 `db` 健康后启动，触发 `lifespan` 钩子。
4. **自愈与建表**：程序内置 **5次重试逻辑**（每2秒一次）以连接数据库。连接后自动执行 `Base.metadata.create_all` 同步表结构。

## 4. 快速启动指南

### 环境准备

* 安装 [Docker](https://www.docker.com/) 和 [Docker Compose](https://docs.docker.com/compose/)。
* 确保 `8000` 和 `3306` 端口未被占用。

### 启动步骤

1. **克隆项目**：
```bash
git clone https://github.com/yuzhouchangwan814/Material_management.git
cd Material_management

```


2. **配置环境**（可选）：修改 `.env` 文件中的数据库密码等信息。
3. **一键运行**：
```bash
docker-compose up --build -d

```


4. **访问接口文档**：打开浏览器访问 [http://localhost:8000/docs](https://www.google.com/search?q=http://localhost:8000/docs) 即可进入 Swagger UI 进行交互式测试。

---

## 5. 数据库表结构描述

系统自动在 MySQL 中维护一张 `materials` 表：

| 字段名 | 数据类型 | 约束条件 | 描述 |
| --- | --- | --- | --- |
| **id** | `INT` | `Primary Key`, `Auto Increment` | 数据库自增主键 |
| **cas_number** | `VARCHAR(50)` | `Unique`, `Not Null`, `Index` | 材料 CAS 登记号（唯一索引） |
| **properties** | `JSON` | `Not Null` | 材料性质，支持存储复杂的键值对对象 |
| **create_time** | `DATETIME` | `Default: CURRENT_TIMESTAMP` | 记录创建时间 |
| **update_time** | `DATETIME` | `On Update: CURRENT_TIMESTAMP` | 记录最后修改时间 |

---
## 6. API 端点实现

| HTTP 方法 | 路径 | 功能描述 | 输入模型 |
| --- | --- | --- | --- |
| **POST** | `/materials/` | 添加记录 (含唯一性校验) | `MaterialCreate` |
| **GET** | `/materials/` | 获取所有材料列表 | 无 |
| **GET** | `/materials/{cas_number}` | 按 CAS 号查询详情 | `cas_number` |
| **DELETE** | `/materials/{cas_number}` | 按 CAS 号删除记录 | `cas_number` |

**实现亮点**：

* **异步 IO**：全链路 `async/await`，提升高并发下的吞吐量。
* **自动文档**：集成 Swagger UI (访问 `/docs`)，支持在线调试。
* **数据校验**：利用 Pydantic 严格校验 CAS 号格式及 JSON 结构。
* **Lifespan 钩子**：应用启动时自动执行 `Base.metadata.create_all`，实现数据库表结构的零手动初始化。
* **错误处理**：对 CAS 重复（409 Conflict）和记录不存在（404 Not Found）进行了标准的异常捕获返回。

---

## 7. 测试命令参考 (WSL2/Ubuntu)

请确保 `curl` 已安装，在 WSL2 或 Linux 环境下运行：

**1. 添加材料记录**

```bash
curl -X 'POST' 'http://localhost:8000/materials/' \
-H 'Content-Type: application/json' \
-d '{"cas_number": "7429-90-5", "properties": {"密度": "2.7 g/cm³", "熔点": "660 °C"}}'

```

**2. 查询所有记录 (美化输出)**

```bash
curl -X 'GET' 'http://localhost:8000/materials/' | python3 -m json.tool

```

**3. 根据 CAS 号查询**

```bash
curl -X 'GET' 'http://localhost:8000/materials/7429-90-5'

```

**4. 删除记录**

```bash
curl -X 'DELETE' 'http://localhost:8000/materials/7429-90-5'

```

---
