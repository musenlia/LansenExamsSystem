# Lansen Exam System (学习培训考试管理系统 V2.0)

一款主打极致便携的考试练习系统。 

基于 FastAPI + React 构建的在线考试平台，便携版一键启动，无需安装任何环境。支持题库管理、智能组卷、在线考试、实时监控、自动阅卷与成绩分析。

## 功能特性核心特色：

U 盘即插即用：绿色免安装设计，解压即可运行，不写注册表，不残留数据。

数据随身携带：将您的题库与练习进度完整存入 U 盘，实现真正的“一盘在手，走遍天下”。

跨设备无缝衔接：无论是在公司办公机、家中电脑还是图书馆公用机，插上 U 盘即可瞬间进入您的专属备考环境。

### 用户角色
| 角色 | 权限 |
|------|------|
| 管理员 | 全部功能，含考试调整、系统配置 |
| 教师 | 班级管理、考试管理、成绩查看、实时监考 |
| 考生 | 参加考试、查看成绩 |

### 核心功能
- **题库管理**：支持单选、多选、判断、填空四种题型，可按分类组织
- **考试管理**：固定组卷与随机组卷两种模式，支持乱序题目/乱序选项
- **考试调整**：重考、续考、补时、强制交卷、重新激活考试
- **实时监控**：WebSocket 实时推送考生状态，切屏检测、全屏保持等防作弊机制
- **自动阅卷**：客观题自动评分，成绩实时生成
- **成绩统计**：班级与个人成绩分析，知识点掌握度可视化

## 技术栈

| 分类 | 技术 |
|------|------|
| 后端框架 | FastAPI |
| ORM | SQLAlchemy 2.0 |
| 数据库 | SQLite |
| 认证 | JWT (python-jose) |
| 前端 | React (Vite) + Ant Design |
| 实时通信 | WebSocket |
| 服务器 | Uvicorn |
| 语言 | Python 3.13+ |

## 快速开始

本系统为**便携版**，已内置 Python 运行环境和所有依赖，无需安装任何软件。

```bash
# 1. 克隆仓库
git clone https://github.com/musenlia/LansenExamsSystem.git
cd LansenExamsSystem

# 2. 双击 run.bat 启动服务
#    首次运行自动创建数据库（约3秒）
#    启动后自动打开浏览器访问 http://localhost:8000
#    局域网内电脑打开浏览器访问 http://IP地址:8000

## 项目截图
<img width="439" height="434" alt="登录页面" src="https://github.com/user-attachments/assets/cb599584-a2c9-487e-876b-3d9a7b97516d" />
<img width="1204" height="662" alt="管理页" src="https://github.com/user-attachments/assets/c71c0802-41f0-49ef-b3b5-01995e742f0b" />
<img width="1366" height="768" alt="实时监考界面" src="https://github.com/user-attachments/assets/0004bc63-7e29-45b8-a281-fa071dea5b01" />
<img width="1366" height="768" alt="考试登录" src="https://github.com/user-attachments/assets/2d2b4d3e-e6cc-4d23-98d8-8268ccb862d8" />
<img width="1366" height="768" alt="考试答题" src="https://github.com/user-attachments/assets/f24cd315-54a4-4e39-a2d8-43bcdde790f8" />



