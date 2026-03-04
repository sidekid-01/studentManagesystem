 学生管理系统 / Student Management System

📝 项目简介 (Overview)
这是一个基于 Python Flask 开发的 Web 应用。该系统旨在为校园环境提供高效的信息管理，支持学生信息维护、课程任务发布以及 EC (Extension) 延期申请的在线审批流程。

This is a Web application developed based on Python Flask. The system is designed to provide efficient information management in a campus environment, supporting student information maintenance, course task publishing, and an online approval process for EC (Extension) requests.

🛠️ 项目结构 (Project Structure)
- `app/`: 核心逻辑包，包含模型(Models)、路由(Routes)、表单(Forms)和 HTML 模板(Templates)。
  Core logic package, containing Models, Routes, Forms, and HTML Templates.
- `run.py`: 项目启动入口。 / Main entry point to start the application.
- `config.py`: 项目配置文件（包含数据库与密钥配置）。 / Configuration file (Database and Secret Key).
- `init_db.py`: 数据库初始化工具，用于自动生成表结构和测试数据。
  Database initialization tool for generating table structures and seed data.

🚀 快速开始 (Quick Start)

1. 安装依赖 (Install Dependencies)
请确保已安装 Python，并在终端运行以下命令安装必要的库：
Ensure Python is installed, then run the following command to install required libraries:

```bash
pip install flask flask-sqlalchemy flask-login flask-wtf email-validator

2. 初始化数据库 (Initialize Database)
在首次运行项目前，必须运行此脚本以生成 app.db 并预填测试账号：
Before running the project for the first time, you must run this script to generate app.db and pre-fill test accounts:

python init_db.py

3. 运行项目 (Launch Application)
执行以下命令启动开发服务器：
Run the following command to start the development server:

python run.py