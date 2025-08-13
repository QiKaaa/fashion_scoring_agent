# 智能穿搭分析Agent API使用指南

本文档提供智能穿搭分析Agent系统的API使用指南，帮助开发者快速集成和使用系统功能。

## 1. API概览

智能穿搭分析Agent提供以下核心API端点：

| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/v1/unified/process` | POST | 统一处理接口，自动识别意图并调用相应服务 |
| `/api/v1/intent/detect` | POST | 意图识别，判断用户意图类型 |
| `/api/v1/analysis/analyze` | POST | 穿搭分析，提供多维度评分 |
| `/api/v1/recommendations/get` | POST | 穿搭推荐，提供个性化穿搭建议 |

## 2. 认证方式

API使用Bearer Token认证：

```
Authorization: Bearer <your_access_token>
```

获取访问令牌：

```
POST /api/v1/auth/token
```

请求体：
```json
{
  "username": "your_username",
  "password": "your_password"
}
```

响应：
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 604800
}
```

## 3. 统一处理接口

### 3.1 请求格式

```
POST /api/v1/unified/process
```

请求体：
```json
{
  "message": "这套穿搭怎么样？",
  "image_path": "data/images/outfit1.jpg",
  "user_id": "user123",
  "preferences": {
    "preferred_styles": ["休闲", "商务"],
    "preferred_colors": ["蓝色", "黑色", "白色"],
    "budget_range": {"min": 1000, "max": 5000}
  }
}
```

参数说明：
- `message`: 用户消息，用于意图识别
- `image_path`: 图像路径（可选）
- `image_url`: 图像URL（可选，与image_path二选一）
- `user_id`: 用户ID（可选）
- `preferences`: 用户偏好（可选）

### 3.2 响应格式

```json
{
  "intent_type": "outfit_scoring",
  "confidence": 0.95,
  "result": {
    // 根据intent_type返回不同的结果结构
    // 如果是outfit_scoring，返回OutfitAnalysisResponse
    // 如果是outfit_recommendation，返回OutfitRecommendation
  },
  "processing_time": 2.5
}
```

## 4. 意图识别API

### 4.1 请求格式

```
POST /api/v1/intent/detect
```

请求体：
```json
{
  "message": "这套穿搭怎么样？",
  "image_path": "data/images/outfit1.jpg",
  "user_id": "user123"
}
```

### 4.2 响应格式

```json
{
  "intent_type": "outfit_scoring",
  "confidence": 0.95,
  "reasoning": "用户询问穿搭评价，使用了'怎么样'这样的评价性词语，表明希望获得对穿搭的评分和分析。",
  "raw_content": "完整的模型响应内容..."
}
```

## 5. 穿搭分析API

### 5.1 请求格式

```
POST /api/v1/analysis/analyze
```

请求体：
```json
{
  "image_path": "data/images/outfit1.jpg",
  "user_id": "user123",
  "budget_focus": false,
  "preferences": {
    "preferred_styles": ["休闲", "商务"],
    "preferred_colors": ["蓝色", "黑色", "白色"]
  }
}
```

参数说明：
- `image_path`: 图像路径（可选）
- `image_url`: 图像URL（可选，与image_path二选一）
- `user_id`: 用户ID（可选）
- `budget_focus`: 是否关注预算维度（默认false）
- `preferences`: 用户偏好（可选）

### 5.2 响应格式

```json
{
  "analysis_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "outfit_description": "这套穿搭由黑色修身西装外套、白色衬衫、深蓝色牛仔裤和棕色皮鞋组成，搭配简约黑色皮带。",
  "color_palette": ["黑色", "白色", "深蓝色", "棕色"],
  "style_type": "商务休闲",
  "scores": {
    "color_coordination": {
      "score": 8.5,
      "reasoning": "黑、白、蓝、棕的经典配色组合协调自然，色彩过渡平滑。",
      "improvement_suggestions": ["可以添加一个亮色口袋巾增加亮点"]
    },
    "style_consistency": {
      "score": 9.0,
      "reasoning": "各单品风格统一，都符合商务休闲风格。",
      "improvement_suggestions": []
    },
    "occasion_suitability": {
      "score": 8.0,
      "reasoning": "适合办公室、商务会议等场合，但略显正式。",
      "improvement_suggestions": ["可根据具体场合调整正式程度"]
    },
    "fashion_sense": {
      "score": 7.5,
      "reasoning": "整体搭配得体但缺乏时尚亮点。",
      "improvement_suggestions": ["可以尝试更有设计感的衬衫款式"]
    },
    "personal_style": {
      "score": 7.0,
      "reasoning": "搭配安全但个人特色不够突出。",
      "improvement_suggestions": ["添加个性配饰如独特袖扣或领带"]
    }
  },
  "overall_score": 8.0,
  "improvement_suggestions": [
    "添加一个亮色口袋巾增加整体亮点",
    "选择更有设计感的衬衫提升时尚度",
    "添加个性配饰如独特袖扣或领带展现个人风格",
    "可以考虑更修身的剪裁提升整体轮廓"
  ],
  "created_at": "2025-08-13T11:30:00.000Z",
  "user_id": "user123"
}
```

## 6. 穿搭推荐API

### 6.1 请求格式

```
POST /api/v1/recommendations/get
```

请求体：
```json
{
  "user_id": "user123",
  "occasion": "商务会议",
  "style_preference": "商务休闲",
  "color_preference": ["蓝色", "灰色", "黑色"],
  "budget_range": {"min": 2000, "max": 5000},
  "season": "春季",
  "reference_image_path": "data/images/reference.jpg",
  "preferences": {
    "preferred_styles": ["商务", "休闲"],
    "preferred_colors": ["蓝色", "灰色", "黑色"],
    "preferred_brands": ["优衣库", "无印良品", "H&M"]
  }
}
```

参数说明：
- `user_id`: 用户ID（可选）
- `occasion`: 场合（可选）
- `style_preference`: 风格偏好（可选）
- `color_preference`: 颜色偏好（可选）
- `budget_range`: 预算范围（可选）
- `season`: 季节（可选）
- `reference_image_path`: 参考图片路径（可选）
- `preferences`: 用户偏好（可选）

### 6.2 响应格式

```json
{
  "recommendation_id": "r1e2c3o4-m5m6-7890-abcd-ef1234567890",
  "outfit_items": [
    {
      "item_type": "上衣",
      "description": "浅蓝色牛津纺衬衫，修身剪裁，带有细微条纹",
      "color": "浅蓝色",
      "style": "商务休闲",
      "estimated_price_range": {"min": 300, "max": 600},
      "brand_suggestions": ["优衣库", "Gap", "无印良品"]
    },
    {
      "item_type": "下装",
      "description": "深卡其色修身休闲裤，直筒剪裁",
      "color": "深卡其色",
      "style": "商务休闲",
      "estimated_price_range": {"min": 400, "max": 800},
      "brand_suggestions": ["优衣库", "H&M", "Zara"]
    },
    {
      "item_type": "鞋履",
      "description": "棕色皮革德比鞋，圆头设计",
      "color": "棕色",
      "style": "商务休闲",
      "estimated_price_range": {"min": 600, "max": 1200},
      "brand_suggestions": ["Clarks", "Ecco", "Geox"]
    },
    {
      "item_type": "配饰",
      "description": "深棕色皮带，简约金属扣",
      "color": "深棕色",
      "style": "商务休闲",
      "estimated_price_range": {"min": 200, "max": 500},
      "brand_suggestions": ["优衣库", "Zara", "H&M"]
    }
  ],
  "style_description": "这是一套商务休闲风格的穿搭，色彩协调，既正式又不失休闲感，适合日常办公和轻商务场合。",
  "occasion_suitability": ["办公室日常", "商务会议", "休闲聚会", "周末约会"],
  "estimated_total_budget": {"min": 1500, "max": 3100},
  "styling_tips": [
    "衬衫可以卷起袖子增加休闲感",
    "衬衫下摆可以塞入裤子增加整洁感",
    "可以添加简约手表提升整体质感",
    "鞋子和皮带颜色应该协调一致"
  ],
  "created_at": "2025-08-13T11:35:00.000Z",
  "user_id": "user123"
}
```

## 7. 图像上传API

### 7.1 请求格式

```
POST /api/v1/images/upload
```

请求体（multipart/form-data）：
- `file`: 图像文件
- `user_id`: 用户ID（可选）

### 7.2 响应格式

```json
{
  "image_path": "data/images/user123/outfit_20250813_123456.jpg",
  "file_name": "outfit_20250813_123456.jpg",
  "content_type": "image/jpeg",
  "file_size": 1024567,
  "upload_time": "2025-08-13T12:34:56.000Z",
  "user_id": "user123"
}
```

## 8. 用户偏好API

### 8.1 获取用户偏好

```
GET /api/v1/users/{user_id}/preferences
```

响应：
```json
{
  "user_id": "user123",
  "preferred_styles": ["休闲", "商务"],
  "preferred_colors": ["蓝色", "黑色", "白色"],
  "preferred_brands": ["优衣库", "无印良品", "H&M"],
  "budget_range": {"min": 1000, "max": 5000},
  "occasion_preferences": {
    "工作": ["商务", "商务休闲"],
    "休闲": ["街头", "运动休闲"]
  },
  "disliked_styles": ["嘻哈", "朋克"],
  "disliked_colors": ["荧光绿", "亮粉色"],
  "body_type": "标准",
  "skin_tone": "中性偏暖",
  "age_range": "25-35",
  "gender": "男",
  "season_preferences": {
    "春": 0.8,
    "夏": 0.6,
    "秋": 1.0,
    "冬": 0.7
  },
  "updated_at": "2025-08-10T15:30:00.000Z"
}
```

### 8.2 更新用户偏好

```
PUT /api/v1/users/{user_id}/preferences
```

请求体：
```json
{
  "preferred_styles": ["休闲", "商务", "街头"],
  "preferred_colors": ["蓝色", "黑色", "白色", "灰色"],
  "budget_range": {"min": 1500, "max": 6000}
}
```

响应：
```json
{
  "user_id": "user123",
  "preferred_styles": ["休闲", "商务", "街头"],
  "preferred_colors": ["蓝色", "黑色", "白色", "灰色"],
  "preferred_brands": ["优衣库", "无印良品", "H&M"],
  "budget_range": {"min": 1500, "max": 6000},
  "occasion_preferences": {
    "工作": ["商务", "商务休闲"],
    "休闲": ["街头", "运动休闲"]
  },
  "disliked_styles": ["嘻哈", "朋克"],
  "disliked_colors": ["荧光绿", "亮粉色"],
  "body_type": "标准",
  "skin_tone": "中性偏暖",
  "age_range": "25-35",
  "gender": "男",
  "season_preferences": {
    "春": 0.8,
    "夏": 0.6,
    "秋": 1.0,
    "冬": 0.7
  },
  "updated_at": "2025-08-13T12:45:00.000Z"
}
```

## 9. 错误处理

API使用标准HTTP状态码表示请求状态：

- `200 OK`: 请求成功
- `400 Bad Request`: 请求参数错误
- `401 Unauthorized`: 未授权访问
- `403 Forbidden`: 禁止访问
- `404 Not Found`: 资源不存在
- `422 Unprocessable Entity`: 请求格式正确但语义错误
- `500 Internal Server Error`: 服务器内部错误

错误响应格式：

```json
{
  "detail": "错误详情描述"
}
```

或更详细的错误信息：

```json
{
  "detail": [
    {
      "loc": ["body", "image_path"],
      "msg": "必须提供image_path或image_url",
      "type": "value_error"
    }
  ]
}
```

## 10. 示例代码

### 10.1 Python示例

```python
import requests
import json

# API基础URL
BASE_URL = "http://localhost:8000/api/v1"

# 获取访问令牌
def get_token(username, password):
    response = requests.post(
        f"{BASE_URL}/auth/token",
        data={"username": username, "password": password}
    )
    return response.json()["access_token"]

# 统一处理接口
def process_unified_request(message, image_path=None, user_id=None, preferences=None, token=None):
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    data = {
        "message": message,
        "image_path": image_path,
        "user_id": user_id,
        "preferences": preferences
    }
    
    response = requests.post(
        f"{BASE_URL}/unified/process",
        headers=headers,
        json=data
    )
    
    return response.json()

# 上传图像
def upload_image(file_path, user_id=None, token=None):
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    files = {"file": open(file_path, "rb")}
    data = {}
    if user_id:
        data["user_id"] = user_id
    
    response = requests.post(
        f"{BASE_URL}/images/upload",
        headers=headers,
        files=files,
        data=data
    )
    
    return response.json()

# 使用示例
if __name__ == "__main__":
    # 获取令牌
    token = get_token("user", "password")
    
    # 上传图像
    image_result = upload_image("outfit.jpg", "user123", token)
    image_path = image_result["image_path"]
    
    # 用户偏好
    preferences = {
        "preferred_styles": ["休闲", "商务"],
        "preferred_colors": ["蓝色", "黑色", "白色"]
    }
    
    # 发送统一请求
    result = process_unified_request(
        "这套穿搭怎么样？",
        image_path,
        "user123",
        preferences,
        token
    )
    
    print(json.dumps(result, indent=2, ensure_ascii=False))
```

### 10.2 JavaScript示例

```javascript
// API基础URL
const BASE_URL = "http://localhost:8000/api/v1";

// 获取访问令牌
async function getToken(username, password) {
  const response = await fetch(`${BASE_URL}/auth/token`, {
    method: "POST",
    headers: {
      "Content-Type": "application/x-www-form-urlencoded"
    },
    body: new URLSearchParams({
      username,
      password
    })
  });
  
  const data = await response.json();
  return data.access_token;
}

// 统一处理接口
async function processUnifiedRequest(message, imagePath = null, userId = null, preferences = null, token = null) {
  const headers = {
    "Content-Type": "application/json"
  };
  
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  
  const response = await fetch(`${BASE_URL}/unified/process`, {
    method: "POST",
    headers,
    body: JSON.stringify({
      message,
      image_path: imagePath,
      user_id: userId,
      preferences
    })
  });
  
  return await response.json();
}

// 上传图像
async function uploadImage(file, userId = null, token = null) {
  const headers = {};
  
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  
  const formData = new FormData();
  formData.append("file", file);
  
  if (userId) {
    formData.append("user_id", userId);
  }
  
  const response = await fetch(`${BASE_URL}/images/upload`, {
    method: "POST",
    headers,
    body: formData
  });
  
  return await response.json();
}

// 使用示例
async function example() {
  try {
    // 获取令牌
    const token = await getToken("user", "password");
    
    // 上传图像
    const fileInput = document.querySelector("#fileInput");
    const file = fileInput.files[0];
    const imageResult = await uploadImage(file, "user123", token);
    const imagePath = imageResult.image_path;
    
    // 用户偏好
    const preferences = {
      preferred_styles: ["休闲", "商务"],
      preferred_colors: ["蓝色", "黑色", "白色"]
    };
    
    // 发送统一请求
    const result = await processUnifiedRequest(
      "这套穿搭怎么样？",
      imagePath,
      "user123",
      preferences,
      token
    );
    
    console.log(result);
    
    // 显示结果
    if (result.intent_type === "outfit_scoring") {
      displayAnalysisResult(result.result);
    } else {
      displayRecommendationResult(result.result);
    }
    
  } catch (error) {
    console.error("Error:", error);
  }
}

// 显示分析结果
function displayAnalysisResult(result) {
  // 实现显示分析结果的逻辑
}

// 显示推荐结果
function displayRecommendationResult(result) {
  // 实现显示推荐结果的逻辑
}
```

## 11. 常见问题解答

### 11.1 如何处理大图像文件？

对于大于10MB的图像文件，建议在客户端进行压缩后再上传。可以使用前端库如`compressorjs`（JavaScript）或`Pillow`（Python）进行图像压缩。

### 11.2 如何处理API超时问题？

对于复杂的分析或推荐请求，处理时间可能较长。建议设置较长的请求超时时间（至少30秒），并在前端实现加载状态提示。

### 11.3 如何提高意图识别准确率？

提供更明确的用户消息和更清晰的图像可以提高意图识别准确率。如果识别结果不准确，可以直接调用特定的服务API（分析或推荐）而不使用统一处理接口。

### 11.4 如何处理多语言支持？

系统默认支持中文和英文。如需支持其他语言，请在请求中添加`language`参数指定语言代码（如`en`、`zh-CN`等）。

### 11.5 如何获取历史分析或推荐结果？

可以通过以下API获取历史结果：

```
GET /api/v1/users/{user_id}/history/analysis
GET /api/v1/users/{user_id}/history/recommendations
```

## 12. 联系与支持

如有问题或需要技术支持，请联系：

- 技术支持邮箱：support@fashion-scoring-agent.com
- API文档：http://localhost:8000/docs
- GitHub仓库：https://github.com/your-org/fashion-scoring-agent