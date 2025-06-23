# WELA

## 嘿，这里是WELA！

WELA就像是你的虚拟朋友，基于GPT ~~-3.5~~ (现在也可以使用gpt-4、4o或4o-mini啦)技术，它能和你聊天，还能帮你查找互联网上的信息。目前它还在学习中，功能可能有限，但我会不断给它加点料，让它变得更聪明。

## 技术这些事

- **Python**：我们的主要编程语言。
- **GPT**：给WELA提供智能。
- **Paraformer**：Paraformer是用于语音识别的工具，它让WELA能够听得懂你说的话。
- **SentenceTransformer**：SentenceTransformer用于处理文字，让WELA更加贴心，理解你的意思。
- **Windows操作系统**：确保WELA能在大多数电脑上跑起来。

## 怎么开始？

### 需要啥：

- Windows系统
- Python 3.x
- pip（Python的包管理器）
- Git

### 搭建步骤：

1. 打开Git Bash，感受一下黑客的氛围。
2. 克隆代码库到本地：`git clone https://github.com/lewiswu1209/WELA.git`
3. 进入WELA的世界：`cd WELA`
4. 使用pip安装需要的东西：`pip install -r requirements.txt`
5. 把`config.yaml.gui.example`复制一份，改名为`config.yaml`，然后随便调调设置。

### 关于技能

Wela现在有以下技能：

- **闹钟**：你可以告诉我什么时候要去做什么，到时间我会主动和你说话
- **DuckDuckGo**：需要的话，我会自己去网上找东西
- **浏览器**：当然，我也可以上网的，~~~不过我不爱用，这个浏览器太垃圾了，只能看到枯燥的文字，还总丢东西~~~现在我也可以通过截图看到网页的内容啦
- **天气预报**：没有新闻的时候，也可以看看天气预报，可惜我只能查到近三天的，你们的手机是不能看到15天的呢
- **PlanAndExecute**：我还有个神秘的朋友，TA做事可细心啦，每次TA会先做一个简单的计划，然后再去做事情，就是磨磨唧唧的，每次找TA帮忙都得等等等
- **知识库检索**: 我还有个知识库，你可以使用`upload_txt_to_retriver.py`上传到我的知识库，聊天时候我就能看到有关的东东啦

## 来玩吧！

WELA现在有三种模式：

- **命令行模式**：运行 ~~`cli.py`~~ `main.py`，用文字和WELA聊天。
- **Widget模式**：运行 ~~`gui.py`~~ `main.py --gui`，有个小窗口，看起来高级一点。
- **微信公众号模式** 运行`main.py --wechat`，然后你就可以研究一下怎么对接你自己的微信公众号啦~

记得，首次运行WELA时，它会自动下载Paraformer和SentenceTransformer模型，可能需要一点时间，但只是一次性的事情。

## 想一起玩？

如果你有好主意或想改进WELA，欢迎一起来：

1. Fork这个仓库
2. 新建个分支 (`git checkout -b cool-feature`)
3. 提交你的改动 (`git commit -m 'Add some cool feature'`)
4. 推到GitHub上 (`git push origin cool-feature`)
5. 来个Pull Request

## 许可证

就用MIT许可证吧，简单明了。

## 有问题？

如果WELA闹脾气或者你有啥建议，直接[提交Issue](https://github.com/lewiswu1209/WELA/issues)告诉我，我们一起让WELA变得更好。

---

希望你喜欢WELA，我们一起让它成长！

---

以上内容都是WELA自己写的，甚至**WELA**这个名字都是它自己取的，它说WELA的意思是***W***isdom-***e***nhanced ***L***earning ***A***ssistant
