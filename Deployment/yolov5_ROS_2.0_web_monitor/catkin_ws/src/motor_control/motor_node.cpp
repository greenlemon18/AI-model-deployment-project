#include <rclcpp/rclcpp.hpp>
#include <std_msgs/msg/float32.hpp>
#include <stdlib.h>
#include <stdio.h>

#define R1 8
#define R2 9
#define L1 13
#define L2 14

static void motor_raw(int r_a,int r_b,int l_a,int l_b) {
    char c[128];
    snprintf(c,sizeof(c),"gpio write %d %d;gpio write %d %d;gpio write %d %d;gpio write %d %d",
             R1,r_a,R2,r_b,L1,l_a,L2,l_b);
    system(c);
}
static void motor_stop(){ motor_raw(0,0,0,0); }

class MotorNode : public rclcpp::Node {
public:
    MotorNode() : Node("motor_control") {
        system("gpio mode 8 out;gpio mode 9 out;gpio mode 13 out;gpio mode 14 out");
        motor_stop();
        g_last_ = this->now();
        sub_ = this->create_subscription<std_msgs::msg::Float32>("/ball/cx", 10,
            std::bind(&MotorNode::cb, this, std::placeholders::_1));
        wd_ = this->create_wall_timer(std::chrono::milliseconds(200),
            std::bind(&MotorNode::watchdog, this));
    }
private:
    rclcpp::Subscription<std_msgs::msg::Float32>::SharedPtr sub_;
    rclcpp::TimerBase::SharedPtr wd_;
    rclcpp::Time g_last_;
    int deadzone_ = 50;

    void cb(const std_msgs::msg::Float32::SharedPtr m) {
        g_last_ = this->now();
        float cx = m->data;
        if (cx < 0) { motor_stop(); return; }
        float d = cx - 320.0f;
        if      (d < -deadzone_) 
        {
            motor_raw(0,1,0,1);   // 左转
        }
        else if (d >  deadzone_) 
        {
            motor_raw(1,0,1,0);   // 右转 
        }
        else              
        {
            motor_raw(0,1,1,0);
        }

        rclcpp::sleep_for(std::chrono::milliseconds(50));
        motor_stop();
        return;
    }
    void watchdog() {
        if ((this->now() - g_last_).seconds() > 1.0) motor_stop();
    }
};

int main(int argc, char **argv) {
    rclcpp::init(argc, argv);
    rclcpp::spin(std::make_shared<MotorNode>());
    return 0;
}
