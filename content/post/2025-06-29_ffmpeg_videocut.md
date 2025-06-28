---
layout:		 single
title:       "使用 FFmpeg 截取视频片段时的精度问题"
subtitle:    ""
description: " "
date:        2025-06-29T02:15:32+08:00
author: LiYixian
image:       ""
tags:        ["cs", "tricks"]
categories:  ["Life" ]
URL: "/2025/06/ffmpeg-videocut/"
math: False
---

使用 FFmpeg 截取视频片段时，一般使用的命令如下：

```bash
ffmpeg -i video.mp4 -ss 00:01:23.4 -to 00:05:56.7 -c copy output.mp4 // 开始时间和结束时间
ffmpeg -i video.mp4 -ss 00:01:23.4 -t 00:04:33.3 -c copy output.mp4 // 开始时间和持续时间
```

但有时这样截取出的片段不够精准，会有几秒的误差（画面固定不动、或者提前结束），原因是 FFmpeg 截取时会从片段首尾附近的关键帧读取。对于精度要求不是很高的情况，可以先查看一下视频的关键帧：

```bash
ffprobe -v error -select_streams v:0 -show_entries frame=key_frame,pkt_pts_time -of csv -skip_frame nokey video.mp4
```

其中各项参数的含义是：
- `-v error`
  - 仅显示错误信息
- `-select_streams v:0`
  - 选择第一个视频流（`v:0`）
- `-show_entries frame=key_frame,best_effort_timestamp_time`
  - 提取每帧的以下字段：
    - `key_frame`：是否为关键帧（`1`=是，`0`=否）
    - `pkt_pts_time`：帧时间戳
- `-of csv`
  - 以 csv 格式输出
- `-skip_frame nokey`
  - 跳过非关键帧（仅输出关键帧）

理想情况下，命令行会输出所有带时间戳的关键帧列表，如下：

```
frame,1,0.000000
frame,1,3.750000
frame,1,7.500000
...
```

但某些版本或编码方式下，视频关键帧的时间戳字段可能会缺失或者没有被正确读取，此时可以尝试换一个字段取代 pkt_pts_time：

（best_effort_time 是 FFmpeg 估算的时间戳，在视频包的 PTS（Presentation Timestamp）不可用时可以备用，精度会略差一点。）

```bash
ffprobe -v error -select_streams v:0 -show_entries frame=key_frame,best_effort_timestamp_time -of csv -skip_frame nokey video.mp4
```

之后，在想要截取的时间点附近选一个关键帧裁剪，就能规避精度问题。