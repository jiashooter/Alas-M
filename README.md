## 环境配置

### 1. 创建 `.env` 文件

在项目根目录下创建一个 `.env` 文件，并添加以下内容：

MONITOR_URL=  

MONITOR_PORT=  

SCKEY=  

CHECK_INTERVAL=300  

### 2. 安装 Docker 和 Docker Compose

确保你的系统已经安装了 Docker 和 Docker Compose。如果没有，请参考官方文档进行安装：

- [Docker 安装指南](https://docs.docker.com/get-docker/)
- [Docker Compose 安装指南](https://docs.docker.com/compose/install/)

## 使用方法

### 1. 构建 Docker 镜像

在项目根目录下运行以下命令来构建 Docker 镜像：

`docker-compose build`

### 2. 启动容器

构建完成后，运行以下命令来启动容器：

`docker-compose up -d`

### 3. 查看日志

你可以通过以下命令查看容器的日志输出：

`docker-compose logs -f`

### 4. 停止容器

如果需要停止容器，可以运行以下命令：

`docker-compose down`

## 文件说明

### `monitor_script.py`

这是主监控脚本，包含以下主要功能：

- 初始化 Chrome WebDriver
- 等待页面加载完成
- 截取页面截图
- 在截图中查找并点击特定图像
- 通过 Server 酱发送微信告警
- 定期执行监控任务

### `Dockerfile`

用于构建 Docker 镜像，包含安装系统依赖和 Python 包的步骤。

### `docker-compose.yml`

用于定义和管理 Docker 容器，包含环境变量配置和卷挂载等信息。

### `requirements.txt`

列出了项目所需的 Python 包。

### `.env`

包含环境变量配置，如监控 URL、端口、Server 酱的 SCKEY 和检查间隔时间。

### `.gitignore`

用于忽略不需要提交到版本控制的文件，如 `.env` 文件。

## 注意事项

- 请确保在 `.env` 文件中正确配置了各项环境变量。
- 监控脚本会定期清空 `tmp` 文件夹中的所有文件，请确保该文件夹中没有重要数据。
- 如果需要修改检查间隔时间，可以在 `.env` 文件中调整 `CHECK_INTERVAL` 的值。

## 许可证

本项目采用 MIT 许可证，详细信息请参阅 LICENSE 文件。