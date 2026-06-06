# 考试调整 API 文档（重考/续考/补时/强制交卷/重新激活）

## 概述

这些管理功能用于管理员对考生的考试会话进行特殊操作，适用于各种异常情况。通过管理页面 `http://localhost:8000/admin.html` 或 API 直接调用。

## 版本信息

- **版本号**: V2.0
- **更新日期**: 2026年6月4日
- **新增功能**: 重考、续考、补时、强制交卷、重新激活考试

## 快速访问

管理页面地址: `http://localhost:8000/admin.html`（需管理员登录）

---

## 接口列表

### 1. 重置考试 (重考)

**接口地址**: `POST /api/monitor/sessions/{session_id}/reset`

**权限要求**: 管理员

**功能说明**: 将已交卷考生的会话重置为未开始状态，清空答题记录和分数

**适用场景**: 
- 考生误点交卷
- 考试过程中出现特殊原因需要重新作答

**前置条件**: 会话状态为 `submitted` / `force_submitted` / `auto_submitted`

**响应示例**:
```json
{
  "code": 0,
  "data": null,
  "message": "重置成功，考生可以重新作答"
}
```

---

### 2. 恢复续考

**接口地址**: `POST /api/monitor/sessions/{session_id}/resume`

**权限要求**: 管理员

**功能说明**: 将已交卷/超时的考生会话恢复为答题中状态，**保留**答题记录

**适用场景**:
- 考生掉线后重连
- 网络故障导致自动提交

**前置条件**: 会话状态为 `submitted` / `force_submitted` / `auto_submitted`

**响应示例**:
```json
{
  "code": 0,
  "data": null,
  "message": "续考成功，考生可以继续答题"
}
```

---

### 3. 补时

**接口地址**: `POST /api/monitor/sessions/{session_id}/extra-time`

**权限要求**: 管理员

**功能说明**: 为正在答题的考生增加额外考试时间

**适用场景**:
- 考试机器故障
- 考生需要额外时间

**前置条件**: 会话状态为 `in_progress`

**请求体**:
```json
{
  "extra_minutes": 30
}
```

**响应示例**:
```json
{
  "code": 0,
  "data": { "extra_time": 30 },
  "message": "补时成功，已增加 30 分钟"
}
```

---

### 4. 强制交卷

**接口地址**: `POST /api/monitor/sessions/{session_id}/force-submit`

**权限要求**: 管理员

**功能说明**: 强制提交考生试卷，结束考试

**适用场景**:
- 考试时间结束
- 需要提前收卷

**前置条件**: 会话状态为 `in_progress`

**请求体**:
```json
{
  "reason": "管理员强制交卷"
}
```

---

### 5. 重新激活考试

**接口地址**: `POST /api/exams/{exam_id}/reactivate`

**权限要求**: 管理员

**功能说明**: 将已结束或已归档的考试重新激活为"已发布"状态，同时：
- 更新考试开始时间为当前时间
- 删除该考试所有旧的答题记录
- 将所有考生会话重置为"未开始"状态

**适用场景**:
- 已结束的考试需要重新进行
- 考试出现问题后需要全员重来

**前置条件**: 考试状态为 `ended` 或 `archived`

**响应示例**:
```json
{
  "code": 0,
  "data": { "id": 3, "status": "published", ... },
  "message": "考试已重新激活，状态变为已发布，已重置 5 名考生会话"
}
```

---

## 监控数据查询

### 考试监控总览

**接口地址**: `GET /api/monitor/exams/{exam_id}/overview`

**响应示例**:
```json
{
  "code": 0,
  "data": {
    "total_students": 30,
    "in_progress_count": 25,
    "submitted_count": 3,
    "not_started_count": 2,
    "status": "ongoing",
    "duration": 60
  }
}
```

### 考生列表

**接口地址**: `GET /api/monitor/exams/{exam_id}/students`

返回每个考生的会话状态、答题进度、切屏次数、剩余时间等。

---

## WebSocket 推送

管理端操作会通过 WebSocket 实时推送通知：

| 事件类型 | 说明 |
|----------|------|
| `session_reset` | 考生被重置（重考） |
| `session_resume` | 考生被恢复（续考） |
| `extra_time_added` | 考生获得补时 |
| `session_force_submit` | 考生被强制交卷 |
| `student_update` | 考生状态更新 |

---

## 数据库字段说明

`exam_sessions` 表关键字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| status | ENUM | not_started / in_progress / submitted / force_submitted / auto_submitted |
| extra_time | INTEGER | 额外增加的时间（秒），默认 0 |
| time_used | INTEGER | 已用时间（秒） |
| total_score | INTEGER | 得分 |

---

## 后端实现文件

- **模型**: `app/models/session.py`、`app/models/exam.py`
- **服务**: `app/services/session_service.py`、`app/services/exam_service.py`、`app/services/monitor_service.py`
- **路由**: `app/routers/monitor.py`、`app/routers/exam.py`
- **Schema**: `app/schemas/monitor.py`

---

## 注意事项

1. **重考**会清空所有答题记录，操作前需谨慎确认
2. **续考**会保留答题记录，但会重置开始时间
3. **补时**只能对正在答题的会话操作，额外时间会累加
4. **重新激活**会删除所有旧的答题记录并重置全部考生会话
5. 所有操作都会记录到监控日志和操作日志中
