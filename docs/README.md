# 技术文档资料下载

本页对应线上入口：[https://bigcow2018.github.io/docs/](https://bigcow2018.github.io/docs/)

将 PDF 放入 `files/` 目录。若需分类，在 `files/` 下建立子目录后再放入文件。添加或调整文件后，在仓库根目录运行：

```bash
python3 docs/build-manifest.py
```

脚本会按名称末尾的编号（`YYYYMMDDNNN`）排序，更新 `manifest.json` 和页面列表。没有编号的条目排在有编号的后面。请保持原始文件名，不要改编号缺号。
