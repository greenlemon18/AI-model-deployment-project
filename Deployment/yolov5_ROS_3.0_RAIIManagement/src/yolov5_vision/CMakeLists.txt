cmake_minimum_required(VERSION 3.10)
project(yolov5_vision)

find_package(OpenCV REQUIRED)
find_package(JPEG REQUIRED)
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(std_msgs REQUIRED)

set(VIP_LIBS NBGlinker VIPhal)

include_directories(./ ../libawnn_viplite ../libawutils ${JPEG_INCLUDE_DIR})

set(NPU_SRCS
    ${CMAKE_SOURCE_DIR}/../libawnn_viplite/awnn_lib.c
    ${CMAKE_SOURCE_DIR}/../libawnn_viplite/awnn_quantize.c
    ${CMAKE_SOURCE_DIR}/../libawutils/image_utils.c
)

add_executable(vision_node vision_node.cpp yolov5_post_process.cpp yolov5_pre_process.cpp ${NPU_SRCS})
ament_target_dependencies(vision_node rclcpp std_msgs)
target_link_libraries(vision_node ${OpenCV_LIBS} ${VIP_LIBS} ${JPEG_LIBRARIES})

install(TARGETS vision_node DESTINATION lib/${PROJECT_NAME})
ament_package()
install(DIRECTORY launch DESTINATION share/${PROJECT_NAME})
