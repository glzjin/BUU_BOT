### 一、什么是联大小助？
联大小助是一个运行在微信公众平台上的机器人，以微信订阅号为接口对外提供校园卡，教务系统，图书馆系统查询等相关功能。

![https://www.zhaoj.in/wp-content/uploads/2018/07/5a3445f6a62a053c81302ec303e4cfb6.png](https://www.zhaoj.in/wp-content/uploads/2018/07/5a3445f6a62a053c81302ec303e4cfb6.png)

![https://www.zhaoj.in/wp-content/uploads/2018/07/3f6ff537aeda0430d235504ca686471b.png](https://www.zhaoj.in/wp-content/uploads/2018/07/3f6ff537aeda0430d235504ca686471b.png)

![https://www.zhaoj.in/wp-content/uploads/2018/07/7a42d1d91dcf60d01e0b95a4906702e5.png](https://www.zhaoj.in/wp-content/uploads/2018/07/7a42d1d91dcf60d01e0b95a4906702e5.png)

![https://www.zhaoj.in/wp-content/uploads/2018/07/e0387eee9c3d5a61baac52dd06a3d322.png](https://www.zhaoj.in/wp-content/uploads/2018/07/e0387eee9c3d5a61baac52dd06a3d322.png)

![https://www.zhaoj.in/wp-content/uploads/2018/07/bec2b93bb244665e734b8114da875de9.png](https://www.zhaoj.in/wp-content/uploads/2018/07/bec2b93bb244665e734b8114da875de9.png)

### 二、运行环境
先来说一下运行环境。

- Mysql
- Redis
- tesseract 相关文件，用于识别验证码
- Python3

然后来说说校园内相关系统的概况。

- VPN 相关，是深信服的 Easyconnect，这个我拿台 Windows  的机器来开 Socks 代理做跳板，这样就可以跳回学校内网了。
- 以下业务均需要内网访问。
  - 统一门户，似乎是某个开源的 CASLOGIN
  - 校园卡，哈尔滨新中新的系统。
  - 教务系统，正方。
  - 图书馆，北创软件。

地址均写死- -可以自己改- –

然后需要运行的话，还需要 buu_config.py.example 里提到的相关服务也要申请。

### 三、部署方法
1、先准备好上面的环境。

2、pip install -i requirements.txt

3、把 buu_config.py.example 改名为 buu_config.py ，把里面的东西配置好。

4、 开个 screen，然后 python3 buu.py 运行吧。

### 四、演示
![https://www.zhaoj.in/wp-content/uploads/2018/07/372f7a83d002fbe39e7b23b82b40388f.png](https://www.zhaoj.in/wp-content/uploads/2018/07/372f7a83d002fbe39e7b23b82b40388f.png)
