# Railway Text Splitter

这是一个文本切割工具，可以将长文本按照指定的最小单词数切割成多个片段。

## 功能特点

- 支持上传TXT、Markdown和DOCX格式的文件
- 可以设置每个片段的最小单词数
- 自动将切割后的文本打包成ZIP文件供下载
- 如果文本长度不足，则不进行切割

## 使用方法

1. 访问网页界面
2. 选择要上传的文件（支持.txt、.md、.docx格式）
3. 设置每个片段的最小单词数（默认为1100）
4. 点击"开始切割"按钮
5. 等待处理完成后，自动下载切割结果的ZIP文件

## 部署方式

### 本地运行

```bash
pip install -r requirements.txt
python app.py
```

### Docker部署

```bash
docker build -t railwaysplitter .
docker run -p 5000:5000 railwaysplitter
```

### Railway平台部署

直接从GitHub仓库部署到Railway平台。