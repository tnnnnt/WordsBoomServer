# wordsboom库
create database wordsboom default charset utf8 collate utf8_general_ci;
# 进入wordsboom库
use wordsboom;
# 用户表
CREATE TABLE users (
    phone_number VARCHAR(11) PRIMARY KEY,
    password VARCHAR(16),
    reg_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    nickname VARCHAR(12),
    avatar_num TINYINT UNSIGNED DEFAULT 0,
    max_favorites INT UNSIGNED DEFAULT 20,
    modify_phone_times TINYINT UNSIGNED DEFAULT 1,
    modify_password_times TINYINT UNSIGNED DEFAULT 1,
    vocabulary INT UNSIGNED DEFAULT 0
)default charset=utf8;
# 单词表
CREATE TABLE words (
    word VARCHAR(25) PRIMARY KEY,
    chinese VARCHAR(180),
    example_sentence1 VARCHAR(200),
    translation1 VARCHAR(150),
    example_sentence2 VARCHAR(200),
    translation2 VARCHAR(150),
    example_sentence3 VARCHAR(200),
    translation3 VARCHAR(150),
    pepxiaoxue TINYINT UNSIGNED DEFAULT 0,
    pepchuzhong TINYINT UNSIGNED DEFAULT 0,
    pepgaozhong TINYINT UNSIGNED DEFAULT 0,
    waiyanshechuzhong TINYINT UNSIGNED DEFAULT 0,
    beishigaozhong TINYINT UNSIGNED DEFAULT 0,
    chuzhong_2 TINYINT UNSIGNED DEFAULT 0,
    chuzhong_3 TINYINT UNSIGNED DEFAULT 0,
    gaozhong_2 TINYINT UNSIGNED DEFAULT 0,
    cet4_1 TINYINT UNSIGNED DEFAULT 0,
    cet4_2 TINYINT UNSIGNED DEFAULT 0,
    cet4_3 TINYINT UNSIGNED DEFAULT 0,
    cet6_1 TINYINT UNSIGNED DEFAULT 0,
    cet6_2 TINYINT UNSIGNED DEFAULT 0,
    cet6_3 TINYINT UNSIGNED DEFAULT 0,
    kaoyan_1 TINYINT UNSIGNED DEFAULT 0,
    kaoyan_2 TINYINT UNSIGNED DEFAULT 0,
    kaoyan_3 TINYINT UNSIGNED DEFAULT 0,
    level4_1 TINYINT UNSIGNED DEFAULT 0,
    level4_2 TINYINT UNSIGNED DEFAULT 0,
    level8_1 TINYINT UNSIGNED DEFAULT 0,
    level8_2 TINYINT UNSIGNED DEFAULT 0,
    ielts_2 TINYINT UNSIGNED DEFAULT 0,
    ielts_3 TINYINT UNSIGNED DEFAULT 0,
    toefl_2 TINYINT UNSIGNED DEFAULT 0,
    toefl_3 TINYINT UNSIGNED DEFAULT 0,
    sat_2 TINYINT UNSIGNED DEFAULT 0,
    sat_3 TINYINT UNSIGNED DEFAULT 0,
    gre_2 TINYINT UNSIGNED DEFAULT 0,
    gre_3 TINYINT UNSIGNED DEFAULT 0,
    gmat_2 TINYINT UNSIGNED DEFAULT 0,
    gmat_3 TINYINT UNSIGNED DEFAULT 0,
    bec_2 TINYINT UNSIGNED DEFAULT 0,
    bec_3 TINYINT UNSIGNED DEFAULT 0
)default charset=utf8;
# 个人单词表
CREATE TABLE personal_words (
    phone_number VARCHAR(11),
    word VARCHAR(25),
    weight INT UNSIGNED DEFAULT 10000,
    collection TINYINT UNSIGNED DEFAULT 0,
    mnemonic VARCHAR(100) DEFAULT '',
    PRIMARY KEY (phone_number, word),
    FOREIGN KEY (phone_number) REFERENCES users(phone_number),
    FOREIGN KEY (word) REFERENCES words(word)
)default charset=utf8;
# 反馈表
CREATE TABLE feedback (
    ID INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    phone_number VARCHAR(11),
    content VARCHAR(100),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (phone_number) REFERENCES users(phone_number)
)default charset=utf8;
# 邮件表
CREATE TABLE email (
    ID INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    phone_number VARCHAR(11),
    content VARCHAR(200),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (phone_number) REFERENCES users(phone_number)
)default charset=utf8;
