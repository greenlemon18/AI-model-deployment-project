# C++ Coding Style Guide

## Naming

| Rule | Good | Bad |
|------|------|-----|
| 变量名：完整英文单词，下划线连接 | `camera_id`, `input_data`, `latency_ms` | `cam`, `inp`, `ms` |
| 类名：大驼峰 | `VisionNode`, `MotorNode`, `Gpio` | `vision_node`, `GPIO` |
| 函数名：小写+下划线 | `get_frame()`, `write_value()` | `GetFrame()`, `Write()` |
| 成员变量：不加前缀/后缀下划线 | `publisher`, `camera`, `frame` | `publisher_`, `camera_`, `m_frame` |
| 全局变量：`g_` 前缀 | `g_ball_center_x` | `ball_center_x` |
| 常量/宏：全大写+下划线 | `DEADZONE`, `TIMEOUT_S` | `deadzone`, `timeout` |

## 代码布局

```cpp
// include 组：无空行
#include <rclcpp/rclcpp.hpp>
#include <opencv2/opencv.hpp>
#include <awnn_lib.h>

class ClassName {
private:
    // ⬇ 成员变量在前
    Type variable_name1;
    Type variable_name2;

    // ⬇ 成员函数在后
    void private_method() {
    }

public:
    // 构造函数
    ClassName() {
    }
    // 析构函数
    ~ClassName() {
    }
};
```

## 变量声明

所有变量必须在函数最开头声明。包括数组、stream 对象。声明与赋值分离：

```cpp
void func() {
    clock_t       start_clock = clock();
    unsigned int  file_size;
    unsigned char *data;
    std_ofstream  temp_file;          // 声明时不打开

    data = get_data();
    if (!data) { return; }

    temp_file.open("/tmp/out.json");  // 确认前面都成功后，才打开文件写
}
```

## 花括号

```cpp
// 正确：{ 在同一行，每条语句占一行，} 独占一行（哪怕只有一条语句也要分行）
if (condition) {\n    do_something();\n}

// 错误：一行挤不下或 { 在下一行
if (condition) { return; }  // 禁止：单条语句挤在一行

```


## RAII 原则

- 资源获取在构造函数，释放在析构函数
- 永远不要裸指针管理资源
- 永远不用 `system("gpio write")`——用 sysfs `ofstream`
- 永远不用 `malloc/free`——如果有必须用的 C 库，在 `free()` 前 `return` 的所有分支加 `free()`

## 函数设计

| Rule | Good | Bad |
|------|------|-----|
| 公有接口清晰 | `motor.stop()`, `motor.forward()` | `motor_raw(1,0,0,1)` |
| 私有实现封装 | `raw()` 放在 private | `system("gpio write 8 1")` 散落各处 |
| 比较时常量在左、变量在右，防止把 `==` 误写成 `=` 编译器不报错

```cpp
// 正确
if (0.3f < probability)     // 常量在左边
if (0 == result)            // 把 == 写成 = 会编译报错

// 错误
if (probability > 0.3f)     // 变量在左边
if (result == 0)
```


### 长行处理
snprintf 和日志类格式化调用允许超长单行——拆散反而破坏可读性。
```cpp
// 允许
snprintf(command, sizeof(command), "sudo sh -c 'echo %d > /sys/class/gpio/export'", number);
// 拆散反而不清晰——不要求拆。
```


### snprintf / 格式化字符串

```cpp
// 正确：格式串直接写在参数里，同一行
snprintf(command, sizeof(command), "sudo sh -c 'echo %d > /sys/class/gpio/export'", number);

// 错误：没必要换行（格式串很短，换行反而难读）
snprintf(command, sizeof(command),
    "sudo sh -c 'echo %d > /sys/class/gpio/export'", number);
```
### 每个函数单一职责 | `loop()` 只管调度 | `loop()` 里既推理又写文件又画框 |

## 文件组织

每个源文件只包含紧密相关的内容。GPIO 和 Motor 在一个文件里可以接受（Motor 直接依赖 Gpio）。Vision 和 Motor 必须分开——它们通过 ROS topic 通信，不应该出现在同一个编译单元。

## 多线程/进程共享资源操作

某个共享资源必须符合原子性，保证调用顺序的先后以及数据在各线程或进程眼里是同步的，不能出现某个线程还完成修改之前，其他线程又读取数据。搭配锁和信号量保证同步性。



