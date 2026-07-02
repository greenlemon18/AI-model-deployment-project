#include <rclcpp/rclcpp.hpp>
#include <std_msgs/msg/float32.hpp>
#include <fstream>
#include <string>
#include <thread>
#include <chrono>

#define R1PIN 139
#define R2PIN 354
#define L1PIN 96
#define L2PIN 129

class Gpio {
    int pin_number;
public:
    Gpio(int number) : pin_number(number) {
        char command[64];
        snprintf(command, sizeof(command), "sudo sh -c 'echo %d > /sys/class/gpio/export'", number);
        system(command);
        usleep(50000);
        snprintf(command, sizeof(command), "sudo sh -c 'echo out > /sys/class/gpio/gpio%d/direction'", number);
        system(command);
    }
    void write(bool level) {
        std::ofstream("/sys/class/gpio/gpio" + std::to_string(pin_number) + "/value") << (level ? "1" : "0");
    }
    ~Gpio() {
        char command[64];
        snprintf(command, sizeof(command), "sudo sh -c 'echo %d > /sys/class/gpio/unexport'", pin_number);
        system(command);
    }
};

class Motor {
    Gpio R1, R2, L1, L2;
public:
    Motor() : R1(R1PIN), R2(R2PIN), L1(L1PIN), L2(L2PIN) 
    { 
        stop(); 
    }
    void stop()    
    { 
        raw(0, 0, 0, 0); 
    }
    void forward() 
    { 
        raw(0, 1, 1, 0); 
    }
    void left()    
    { 
        raw(1, 0, 1, 0);
        
    }
    void right()   
    { 
        raw(0, 1, 0, 1); 
    }
private:
    void raw(int r1, int r2, int l1, int l2) 
    {
        R1.write(r1); R2.write(r2);
        L1.write(l1); L2.write(l2);
    }
};

class MotorNode : public rclcpp::Node {
public:
    MotorNode() : Node("motor_control") 
    {
        motor.stop();
        g_last_ = this->now();
        g_cooldown_ = this->now();
        sub_ = this->create_subscription<std_msgs::msg::Float32>("/ball/cx", 10,
            std::bind(&MotorNode::cb, this, std::placeholders::_1));
        wd_ = this->create_wall_timer(std::chrono::milliseconds(200),
            std::bind(&MotorNode::watchdog, this));
    }
private:
    Motor motor;
    rclcpp::Subscription<std_msgs::msg::Float32>::SharedPtr sub_;
    rclcpp::TimerBase::SharedPtr wd_;
    rclcpp::Time g_last_, g_cooldown_;
    int deadzone_ = 50, 
    cooldown_ms_ = 200;

    void cb(const std_msgs::msg::Float32::SharedPtr m) {
        g_last_ = this->now();
        float cx = m->data;
        float d = cx - 320.0f;

        if ((this->now() - g_cooldown_).seconds() * 1000 < cooldown_ms_) 
        {
            motor.stop(); 
            return;
        }
        
        if (cx < 0) 
        { 
            motor.stop(); 
            return; 
        }
        
        if (d < -deadzone_) {
            motor.left();
            rclcpp::sleep_for(std::chrono::milliseconds(20));
            motor.stop();
            g_cooldown_ = this->now();
        } else if (d > deadzone_) {
            motor.right();
            rclcpp::sleep_for(std::chrono::milliseconds(20));
            motor.stop();
            g_cooldown_ = this->now();
        } else {
            motor.forward();
        }
    }
    void watchdog() 
    {
        if ((this->now() - g_last_).seconds() > 1.0)
        {
            motor.stop();
        }
    }
};

int main(int argc, char **argv) {
    rclcpp::init(argc, argv);
    rclcpp::spin(std::make_shared<MotorNode>());
    return 0;
}