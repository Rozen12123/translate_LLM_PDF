# Docker 使用说明文档

本文档说明如何使用 Docker 来运行 PDF 翻译服务。

## 准备工作

确保您的系统已经安装了 Docker。如果没有安装，请参考 [Docker 官方文档](https://docs.docker.com/get-docker/) 进行安装。

## 构建 Docker 镜像

在项目根目录下运行以下命令来构建 Docker 镜像：

```bash
docker build -t pdf-translator -f Dockerfile.custom .
```

## 运行 Docker 容器

构建完成后，使用以下命令启动容器：

```bash
sudo docker run -d \
  --name pdf-translator \
  -p 7860:7860 \
  -v $(pwd)/pdf2zh_files:/app/pdf2zh_files \
  -v $(pwd)/uploads:/app/uploads \
  --restart unless-stopped \
  pdf-translator
```

如果需要使用非 root 用户(如 pythonuser)运行容器，可以添加 `--user` 参数，但需要设置目录的权限：

```bash
cd /path/to/translate_LLM_PDF
sudo usermod -s /usr/sbin/nologin pythonuser
sudo usermod -d /path/to/translate_LLM_PDF pythonuser
sudo chown -R pythonuser pdf2zh_files uploads

mkdir -p $(pwd)/cache
chmod 777 $(pwd)/cache
mkdir -p $(pwd)/config
chmod 777 $(pwd)/config

sudo docker run -d \
  --name pdf-translator \
  --user $(id -u pythonuser):$(id -g pythonuser) \
  -p 7860:7860 \
  -v $(pwd)/pdf2zh_files:/app/pdf2zh_files \
  -v $(pwd)/uploads:/app/uploads \
  --restart unless-stopped \
  -v $(pwd)/config:/.config \
  -v $(pwd)/cache:/.cache \
  pdf-translator

```

如果需要在前台运行并查看输出，可以去掉 `-d` 参数：

```bash
sudo docker run \
  --name pdf-translator \
  -p 7860:7860 \
  -v $(pwd)/pdf2zh_files:/app/pdf2zh_files \
  -v $(pwd)/uploads:/app/uploads \
  pdf-translator
```

参数说明：
- `-d`: 在后台运行容器
- `--name pdf-translator`: 设置容器名称
- `--user pythonuser`: 指定使用 pythonuser 用户运行容器
- `-p 7860:7860`: 将容器内的 7860 端口映射到主机的 7860 端口
- `-v $(pwd)/pdf2zh_files:/app/pdf2zh_files`: 挂载 PDF 输出文件目录
- `-v $(pwd)/uploads:/app/uploads`: 挂载上传文件目录
- `--restart unless-stopped`: 容器停止时自动重启

## 查看容器日志

```bash
docker logs pdf-translator
```

## 停止和删除容器

停止容器：
```bash
docker stop pdf-translator
```

删除容器：
```bash
docker rm pdf-translator
```

## 注意事项

1. 容器启动后会自动激活位于 `/root/Docker/.venv` 的虚拟环境
2. 所有的 PDF 文件都应该放在 `pdf2zh_files` 目录下
3. 服务启动后可以通过 `http://localhost:7860` 访问 Web 界面

## 常见问题排查

如果遇到问题：

1. 确认端口 7860 没有被其他程序占用
2. 检查容器日志是否有错误信息
3. 确保 `pdf2zh_files` 目录有正确的读写权限

## 环境变量

容器内包含以下环境变量：
- `PYTHONUNBUFFERED=1`: Python 输出不缓冲

## 镜像特性

- 使用清华源加速 apt 包和 pip 包的安装
- 自动安装所需的系统依赖和 Python 包
- 直接安装到系统 Python 环境，无需虚拟环境
