# 教学仪器

本页对应线上入口：[https://bigcow2018.github.io/instruments/](https://bigcow2018.github.io/instruments/)

将文档放入 `files/` 目录。若需分类，在 `files/` 下建立子目录后再放入文件。添加或调整文件后，在仓库根目录运行：

```bash
python3 instruments/build-manifest.py
```

脚本会按名称中的编号排序（开头的数字编号，或末尾的日期加序号且序号按数值排列），更新 `manifest.json` 和页面列表。请保持原始文件名。
