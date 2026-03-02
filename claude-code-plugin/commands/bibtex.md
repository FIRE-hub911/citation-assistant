---
description: 通过 DOI 获取 BibTeX 引用格式
argument-hint: DOI 字符串
allowed-tools: Bash
---

# /citation:bibtex

通过 DOI 内容协商 API 获取标准 BibTeX 格式。

## 参数

**$ARGUMENTS**: DOI 字符串（可包含 https://doi.org/ 前缀）

## 执行

```bash
DOI="$ARGUMENTS"; \
DOI=$(echo "$DOI" | sed 's|https://doi.org/||g; s|http://doi.org/||g; s|doi.org/||g; s|^ *||; s| *$||'); \
if [ -z "$DOI" ]; then
  echo "错误：请提供 DOI 参数"
  echo "用法: /citation:bibtex 10.1148/radiol.2020191075"
  exit 1
fi; \
echo "获取 DOI: $DOI 的 BibTeX..."; \
echo; \
curl -sLH "Accept: text/bibliography; style=bibtex" "https://doi.org/${DOI}" | \
python3 -c "
import sys
bibtex = sys.stdin.read().strip()
if not bibtex or bibtex.startswith('<'):
    print('错误：无法获取 BibTeX，请检查 DOI 是否正确')
    sys.exit(1)
print(bibtex)
"
```

## 输出示例

```bibtex
@article{Wu_2020,
  doi = {10.1148/radiol.2020191075},
  url = {https://doi.org/10.1148/radiol.2020191075},
  year = 2020,
  month = {apr},
  publisher = {Radiological Society of North America ({RSNA})},
  volume = {295},
  number = {3},
  pages = {605--617},
  author = {Joy T. Wu and Justin Wong and William Hsu},
  title = {{CheXpert}: A Large Chest Radiograph Dataset},
  journal = {Radiology}
}
```

## 注意事项

- DOI 可以是完整 URL (https://doi.org/...) 或纯 DOI 字符串
- 内容协商 API 由 CrossRef/DataCite 提供
- 部分 DOI 可能返回空或格式不规范，可尝试访问 https://doi.org/xxx 手动获取
