CREATE TABLE IF NOT EXISTS credit_review(
 id int not null primary key auto_increment comment '主键',
 order_no varchar(40) comment '申请编号',
 id_card_no varchar(20) comment '身份证号',
 record_id varchar(100) comment '录音ID',
 record_path varchar(200) comment '录音地址',
 record_time varchar(40) comment '录音时间',
 customer_phone varchar(40) comment '客户号码',
 record_flag varchar(2) comment '录音标记'
)