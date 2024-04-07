# coding:utf-8
import os
import pymysql
import schedule
import time

# 从环境变量中获取 MySQL 的端口、用户名和密码
port = int(os.environ.get('MYSQL_PORT'))
user = os.environ.get('MYSQL_USER_WORDSBOOM')
passwd = os.environ.get('MYSQL_PASSWORD_WORDSBOOM')


# 重置用户权限
def reset():
    # 连接数据库
    conn = pymysql.connect(host='localhost', port=port, user=user, passwd=passwd, charset='utf8', db='wordsboom')
    cursor = conn.cursor()
    # 更新用户表中的modify_phone_times和modify_password_times
    cursor.execute("UPDATE users SET modify_phone_times=1, modify_password_times=1")
    conn.commit()
    cursor.close()
    conn.close()


# 定义每周一早上0点执行reset任务
schedule.every().monday.at("00:00").do(reset)
while True:
    # 检查是否有任务需要执行
    schedule.run_pending()
    time.sleep(60)  # 每隔一分钟检查一次
