# 技术文档资料下载

本页对应线上入口：[https://bigcow2018.github.io/docs/](https://bigcow2018.github.io/docs/)

将 PDF 放入 `files/` 目录。若需分类，在 `files/` 下建立子目录后再放入文件。添加或调整文件后，在仓库根目录运行：

```bash
python3 docs/build-manifest.py
```

脚本会把各子目录中的文件合并为一份清单（不显示文件夹分组标题），按名称末尾编号排序：日期（`YYYYMMDD`）之后的序号按数值排列（例如 100、101、102、103），位数可变；然后更新 `manifest.json` 和页面列表。页面按默认每页 10 条分页显示，总数变化时页码自动更新。请保持原始文件名，不要改编号缺号。
