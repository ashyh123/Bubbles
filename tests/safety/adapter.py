"""把安全用例接到 demo 的真实代码上。

``check_url`` 和 ``open_browser`` 由测试注入，产品代码不在这里联网或打开浏览器。
"""

from bubble.actions import execute, process
from bubble.safety import build_bilibili_url

__all__ = ["build_bilibili_url", "execute", "process"]
