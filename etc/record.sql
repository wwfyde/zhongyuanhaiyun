CREATE DATABASE IF NOT EXISTS custom_data_capture default character set utf8mb4;
CREATE TABLE IF NOT EXISTS records(
    id int not null primary key auto_increment comment '主键',  -- 主键
    record_file_flag varchar(2) comment '录音文件标记', -- 录音文件状态标记 0 初始状态 -2录音文件为空, -1 录音文件/地址不存在, 1 录音文件下载成功
    business_data_flag varchar(2) comment '业务数据标记', -- 业务数据匹配状态 0 初始状态
    call_id varchar(30) comment '通话id',
    call_time varchar(60) comment '通话时间',
    insert_time varchar(60) comment '插入时间',
    business_type varchar(16) comment '业务类型',
    call_state varchar(16) comment '通话状态',
    department_name varchar(16) comment '部门名称',
    phone varchar(20) comment '手机号码',
    agent varchar(20) comment '坐席名称',
    start_time varchar(60) comment '开始时间',
    end_time varchar(60) comment '结束时间',
    workflow varchar(60) comment '呼叫方向',
    hanguper varchar(60) comment '挂机方向'
)