cmake_minimum_required(VERSION 3.10)

project(yolov5)

message (STATUS "CMAKE_C_COMPILER = ${CMAKE_C_COMPILER}")
message (STATUS "CMAKE_SYSTEM_NAME = ${CMAKE_SYSTEM_NAME}")

set(SYS_ARCH linux_aarch64)
    
find_package(OpenCV REQUIRED)
find_package(catkin REQUIRED COMPONENTS roscpp std_msgs)

set(VIP_LIBS NBGlinker VIPhal)


# Add the source in project root directory
aux_source_directory(. DIRSRCS)
aux_source_directory(../libawnn_viplite NPULIB_DIRSRCS)

# Add header file include directories
include_directories(./ ../libawnn_viplite ../libawutils ${catkin_INCLUDE_DIRS})

# Add block directories

# Target
add_executable(yolov5 ${DIRSRCS} ${NPULIB_DIRSRCS})
target_link_libraries(yolov5 ${catkin_LIBRARIES} ${OpenCV_LIBS} ${VIP_LIBS})

