# steam-broadcast

---

## 描述

steam-broadcast是为Steam直播间增加人气的脚本。

https://steamcommunity.com/?subsection=broadcasts


---

## 可修改的参数说明

- STEAM_ID：直播间ID，即直播间地址最后的64位ID。（如https://steamcommunity.com/broadcast/watch/76561199576320486就是76561199576320486）
- HEARTBEAT_COUNT：每个观众心跳次数，即进入一次直播间维持多久在线。心跳30s/次。
- VIEWER_COUNT：单个脚本执行需要伪装的观众数量，建议值不大于200。
- TOTAL_VIEWER_COUNT：总观众数，用于控制总体观众数不超过这个数值。

---

## 启动方式

```
python broadcast.py
```
```
python3 broadcast.py
```

---

## 补充
仅供个人娱乐、测试、学习使用。