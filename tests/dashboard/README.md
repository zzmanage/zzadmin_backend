# Dashboard 测试脚本说明

本目录包含了用于测试和初始化dashboard应用的脚本文件。

## 脚本列表

### 1. add_gender_items.py
- 功能：为ID为3的"性别"字典添加"男"和"女"两个子字典项
- 用途：初始化系统中常用的性别字典数据
- 运行方式：`python add_gender_items.py`

### 2. check_dictionary.py
- 功能：检查ID为3的字典是否存在，并显示其基本信息和子字典项
- 用途：验证字典数据是否正确初始化
- 运行方式：`python check_dictionary.py`

### 3. test_dictionary_api.py
- 功能：通过API测试字典项接口的功能，包括登录认证和数据获取
- 用途：验证字典API接口的正确性
- 运行方式：`python test_dictionary_api.py`

## 注意事项
- 所有脚本需要在项目根目录下运行
- 确保Django服务器已经启动（对于API测试脚本）