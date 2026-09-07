# 今日头条深度文章 Skill

从实时选题、事实核验到图文 DOCX 和授权发布的一套工作流。每次只围绕一个读者问题展开，不做多条热点拼盘，不承诺阅读量或收益。

## 能力

- 比较候选选题，区分事实、评论与推断，保留核验记录。
- 评估五个标题，检查清晰度、读者相关性和正文是否兑现标题。
- 生成带本地配图的 DOCX，正文不重复总标题，来源与审核记录单独保存。
- 通过创作页面的文档导入发布，核对完整预览并如实记录审核中或已发布。
- 使用 SQLite 台账防止重复提交，处理中断恢复和明确授权的额外文章。

## 安装与运行

把本目录安装到个人 skills 目录，目录名保持 `daily-hotspot-toutiao`。在支持 skills 的助手中调用 `$daily-hotspot-toutiao`，说明主题偏好及是否允许发布。

Python 3.10 或以上版本，安装 DOCX 依赖：

```sh
python -m pip install -r requirements.txt
python -m unittest discover -s scripts -p "test_*.py" -v
```

完整工作流还需要助手具备实时检索、原创图片生成、DOCX 渲染检查，以及支持文件上传的已登录浏览器操作能力。这些外部能力不由本仓库提供。安装 skill 不会自动建立定时任务；每日运行时间、时区和通知应在宿主调度器单独配置。

## 文件生成

输入格式见 [artifacts.md](references/artifacts.md)，文章写作与审核要求见 [editorial.md](references/editorial.md)。

```sh
python scripts/build_article.py --input /absolute/path/article.json --out-dir /absolute/path/output
```

产出 DOCX、按顺序保存的图片及审核 JSON。脚本只检查结构，不替代事实核验或视觉检查；生成后的审核状态仍为待检查。

## 发布边界

默认只准备文件。用户明确授权后才能发布；持续授权可以包含最后一次确认发布点击，不应因按钮名称反复索取同一授权。账号、位置、发布授权保存在用户本地，不能沿用其他人的配置。

首次声明默认关闭；如实披露 AI 使用。登录失效、验证码、内容缺失或平台拦截时停止，不绕过安全机制。提交结果不明时先核对原文章，不盲目重发。细节见 [publishing.md](references/publishing.md)。

`prepare_toutiao_pack.py` 仅保留用于明确请求的旧版汇总转换，不是默认工作流。合规检查是内容质量控制，不是敏感词替换或审核规避。

本目录不包含账号凭据、浏览器会话、生成文章、发布台账或个人运行记录。
