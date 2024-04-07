# coding:utf-8
import asyncio
import pymysql
import os
import random
from alibabacloud_dysmsapi20170525.client import Client as Dysmsapi20170525Client
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_dysmsapi20170525 import models as dysmsapi_20170525_models
from alibabacloud_tea_util import models as util_models
from alibabacloud_tea_util.client import Client as UtilClient

# 以下为一些配置信息
version = '1.0'  # 最新版本
IP = ''  # 服务器的IP地址，留空表示绑定所有可用的网络接口
PORT = 11451  # 服务器监听的端口号
BUFLEN = 8192  # 一次最多读取的字节数
code_map = {}  # 用于存储验证码的字典

# 从环境变量中获取数据库和阿里云短信服务的相关信息
port = int(os.environ.get('MYSQL_PORT'))
user = os.environ.get('MYSQL_USER_WORDSBOOM')
passwd = os.environ.get('MYSQL_PASSWORD_WORDSBOOM')
admin_account = os.environ.get('ADMIN_ACCOUNT')
admin_passwd = os.environ.get('ADMIN_PASSWORD')
alibaba_cloud_access_key_id = os.environ.get('ALIBABA_CLOUD_ACCESS_KEY_ID')
alibaba_cloud_access_key_secret = os.environ.get('ALIBABA_CLOUD_ACCESS_KEY_SECRET')

# 创建阿里云短信客户端
config = open_api_models.Config(
    access_key_id=alibaba_cloud_access_key_id,
    access_key_secret=alibaba_cloud_access_key_secret
)
config.endpoint = 'dysmsapi.aliyuncs.com'
client = Dysmsapi20170525Client(config)
runtime = util_models.RuntimeOptions()

# 用于存储每个手机号对应的删除任务
delete_tasks = {}

# 数据库连接和游标
conn = None
cursor = None


async def del_code(phone_number):
    """
    异步删除验证码的任务，将在5分钟后执行。
    """
    await asyncio.sleep(300)
    if phone_number in code_map:
        del code_map[phone_number]
    if phone_number in delete_tasks:
        del delete_tasks[phone_number]


async def connect_db():
    """
    异步连接数据库的操作。
    """
    global conn, cursor
    conn = pymysql.connect(host='localhost', port=port, user=user, passwd=passwd, charset='utf8', db='wordsboom')
    cursor = conn.cursor()


async def close_db():
    """
    异步关闭数据库的操作。
    """
    global conn, cursor
    if cursor:
        cursor.close()
    if conn:
        conn.close()


async def execute_sql(sql, params=None):
    """
    异步执行SQL语句的操作。
    """
    global cursor
    cursor.execute(sql, params)


async def commit():
    """
    异步提交数据库的操作。
    """
    global conn
    conn.commit()


async def fetchone():
    """
    异步获取一行数据的操作。
    """
    global cursor
    return cursor.fetchone()


async def fetchall():
    """
    异步获取所有数据的操作。
    """
    global cursor
    return cursor.fetchall()


# 定义处理客户端请求的协程函数
async def handle_client(reader, writer):
    """
    这个协程函数处理与单个客户端的通信。
    它从客户端读取数据，处理数据，并发送响应。
    参数:
    reader: 用于从客户端读取数据的 asyncio StreamReader 对象。
    writer: 用于向客户端写入数据的 asyncio StreamWriter 对象。
    """
    while True:
        response = '0'
        data = await reader.read(BUFLEN)  # 从客户端读取数据（每次最多读取 BUFLEN 字节）
        if not data:
            break
        message = data.decode()
        flag = message[0:2]
        if flag == '00':
            phone_number = message[2:13]
            await connect_db()
            await execute_sql("SELECT COUNT(*) FROM users WHERE phone_number=%s", [phone_number])
            response = str((await fetchone())[0])
            await close_db()
        elif flag == '01':
            phone_number = message[2:13]
            code = ''
            for i in range(6):
                code += str(random.randint(0, 9))
            send_sms_request = dysmsapi_20170525_models.SendSmsRequest(
                sign_name='单词弹弹弹',
                template_code='SMS_464521317',
                phone_numbers=phone_number,
                template_param='{"code":"' + code + '"}'
            )
            try:
                await client.send_sms_with_options_async(send_sms_request, runtime)
                response = '1'
            except Exception as e:
                response = '0'
                # 错误 message
                print(e.message)
                # 诊断地址
                print(e.data.get("Recommend"))
                UtilClient.assert_as_string(e.message)
            finally:
                # 取消之前的删除任务
                if phone_number in delete_tasks:
                    delete_tasks[phone_number].cancel()
                # 创建新删除任务
                delete_tasks[phone_number] = asyncio.create_task(del_code(phone_number))
                code_map[phone_number] = code
        elif flag == '02':
            phone_number = message[2:13]
            code = message[13:19]
            if phone_number in code_map and code_map[phone_number] == code:
                response = '1'
                del code_map[phone_number]
            else:
                response = '0'
        elif flag == '03':
            phone_number = message[2:13]
            password = message[13:]
            # 随机生成昵称
            nick_name = random.choice(['甜心波波', '三硝基甲苯', 'crush', 'IceSugarS2-', 'VARY', 'Noah', 'Rāmāṉujan', '修', 'Johnny', '0 分战士', 'logeek', '纯真的电灯泡', '椰云拿铁.', '心态', 'N', '朔月', 'hello', 'ASAP', '哈', '朵', '瞳眸氵', '大黑帽', '^0^', '能跑', 'Z。', '间歇性踌躇满志', '123xz', 'Yoona', '樂', '梵', '#%d', 'timer', '韵沐', '冷裤猪脚', '刘峥', 'igg', '。', '水泽木兰', '澈', '一種不羈於世的Feelヾ', '荆舟', 'DyDyDyD', 'ljw'])
            await connect_db()
            await execute_sql("INSERT INTO users(phone_number,password,nickname) VALUES(%s,%s,%s)", [phone_number, password, nick_name])
            await commit()
            await execute_sql("SELECT word FROM words")
            words = await fetchall()
            for word in words:
                await execute_sql("INSERT INTO personal_words(phone_number,word) VALUES(%s,%s)", [phone_number, word])
            await commit()
            await close_db()
        elif flag == '04':
            phone_number = message[2:13]
            await connect_db()
            await execute_sql("SELECT modify_password_times FROM users WHERE phone_number=%s", [phone_number])
            response = str((await fetchone())[0])
            if response == '1':
                await execute_sql("UPDATE users SET modify_password_times=0 WHERE phone_number=%s", [phone_number])
                await commit()
            await close_db()
        elif flag == '05':
            phone_number = message[2:13]
            password = message[13:]
            await connect_db()
            await execute_sql("UPDATE users SET password=%s WHERE phone_number=%s", [password, phone_number])
            await commit()
            await close_db()
            response = '1'
        elif flag == '06':
            phone_number = message[2:13]
            password = message[13:]
            await connect_db()
            await execute_sql("SELECT COUNT(*) FROM users WHERE phone_number=%s and password=%s", [phone_number, password])
            response = str((await fetchone())[0])
            await close_db()
        elif flag == '07':
            phone_number = message[2:13]
            await connect_db()
            await execute_sql("SELECT reg_time FROM users WHERE phone_number=%s", [phone_number])
            response = str((await fetchone())[0])
            await close_db()
        elif flag == '08':
            phone_number = message[2:13]
            await connect_db()
            await execute_sql("SELECT nickname FROM users WHERE phone_number=%s", [phone_number])
            response = (await fetchone())[0]
            await close_db()
        elif flag == '09':
            phone_number = message[2:13]
            await connect_db()
            await execute_sql("SELECT avatar_num FROM users WHERE phone_number=%s", [phone_number])
            response = str((await fetchone())[0])
            await close_db()
        elif flag == '10':
            phone_number = message[2:13]
            avatar_num = int(message[13:])
            await connect_db()
            await execute_sql("UPDATE users SET avatar_num=%s WHERE phone_number=%s", [avatar_num, phone_number])
            await commit()
            await close_db()
        elif flag == '11':
            phone_number = message[2:13]
            nickname = message[13:]
            await connect_db()
            await execute_sql("UPDATE users SET nickname=%s WHERE phone_number=%s", [nickname, phone_number])
            await commit()
            await close_db()
        elif flag == '12':
            phone_number = message[2:13]
            await connect_db()
            await execute_sql("DELETE FROM feedback WHERE phone_number=%s", [phone_number])
            await execute_sql("DELETE FROM email WHERE phone_number=%s", [phone_number])
            await execute_sql("DELETE FROM personal_words WHERE phone_number=%s", [phone_number])
            await execute_sql("DELETE FROM users WHERE phone_number=%s", [phone_number])
            await commit()
            await close_db()
        elif flag == '13':
            phone_number = message[2:13]
            await connect_db()
            await execute_sql("SELECT modify_phone_times FROM users WHERE phone_number=%s", [phone_number])
            response = str((await fetchone())[0])
            if response == '1':
                await execute_sql("UPDATE users SET modify_phone_times=0 WHERE phone_number=%s", [phone_number])
                await commit()
            await close_db()
        elif flag == '14':
            phone_number = message[2:13]
            new_phone_number = message[13:24]
            await connect_db()
            await execute_sql("INSERT INTO users(phone_number,password,reg_time,nickname,avatar_num,max_favorites,modify_phone_times,modify_password_times) SELECT %s,password,reg_time,nickname,avatar_num,max_favorites,modify_phone_times,modify_password_times FROM users WHERE phone_number=%s", [new_phone_number, phone_number])
            await execute_sql("UPDATE email SET phone_number=%s WHERE phone_number=%s", [new_phone_number, phone_number])
            await execute_sql("UPDATE feedback SET phone_number=%s WHERE phone_number=%s", [new_phone_number, phone_number])
            await execute_sql("UPDATE personal_words SET phone_number=%s WHERE phone_number=%s", [new_phone_number, phone_number])
            await execute_sql("DELETE FROM users WHERE phone_number=%s", [phone_number])
            await commit()
            await close_db()
            response = '1'
        elif flag == '15':
            phone_number = message[2:13]
            vocab_name, vocab_num = message[13:].split(",")
            vocab_num = int(vocab_num)
            await connect_db()
            await execute_sql("UPDATE personal_words INNER JOIN words ON personal_words.word=words.word SET personal_words.weight=10000 WHERE personal_words.phone_number=%s AND {}=%s AND personal_words.weight!=10000".format(vocab_name), [phone_number, vocab_num])
            await commit()
            await close_db()
        elif flag == '16':
            phone_number = message[2:13]
            word = message[13:]
            await connect_db()
            await execute_sql("SELECT chinese,collection FROM personal_words INNER JOIN words ON personal_words.word=words.word WHERE phone_number=%s AND words.word=%s", [phone_number, word])
            response = str(await fetchone())
            await close_db()
        elif flag == '17':
            phone_number = message[2:13]
            word = message[13:-2]
            change_w = message[-2:]
            await connect_db()
            await execute_sql("UPDATE personal_words SET weight=GREATEST(weight{},1) WHERE phone_number=%s AND word=%s".format(change_w), [phone_number, word])
            await commit()
            await close_db()
        elif flag == '18':
            phone_number = message[2:13]
            word = message[13:]
            await connect_db()
            await execute_sql("UPDATE personal_words SET collection=1-collection WHERE phone_number=%s AND word=%s", [phone_number, word])
            await commit()
            await close_db()
        elif flag == '19':
            phone_number = message[2:13]
            vocab_name, vocab_num, words_per_popup = message[13:].split(",")
            vocab_num = int(vocab_num)
            words_per_popup = int(words_per_popup)
            await connect_db()
            await execute_sql("SELECT words.word FROM words INNER JOIN personal_words ON personal_words.word=words.word WHERE phone_number=%s AND {}=%s ORDER BY RAND() * weight DESC LIMIT %s".format(vocab_name), [phone_number, vocab_num, words_per_popup])
            response = str(await fetchall())
            await close_db()
        elif flag == '20':
            phone_number = message[2:13]
            await connect_db()
            await execute_sql("SELECT COUNT(*) FROM personal_words WHERE collection=1 AND phone_number=%s", [phone_number])
            num_collection = (await fetchone())[0]
            await execute_sql("SELECT max_favorites FROM users WHERE phone_number=%s", [phone_number])
            max_favorites = (await fetchone())[0]
            if num_collection < max_favorites:
                response = '1'
            else:
                response = '0'
            await close_db()
        elif flag == '21':
            word = message[2:]
            await connect_db()
            await execute_sql("SELECT COUNT(*) FROM words WHERE word=%s", [word])
            response = str((await fetchone())[0])
            await close_db()
        elif flag == '22':
            word = message[2:]
            await connect_db()
            await execute_sql("SELECT example_sentence1,example_sentence2,example_sentence3,translation1,translation2,translation3 FROM words WHERE word=%s", [word])
            response = str(await fetchone())
            await close_db()
        elif flag == '23':
            word = message[2:]
            await connect_db()
            await execute_sql("SELECT mnemonic,nickname FROM personal_words INNER JOIN users ON personal_words.phone_number=users.phone_number WHERE word=%s AND mnemonic!='' ORDER BY RAND() LIMIT 1", [word])
            response = str(await fetchone())
            await close_db()
        elif flag == '24':
            phone_number = message[2:13]
            word = message[13:]
            await connect_db()
            await execute_sql("SELECT mnemonic FROM personal_words WHERE phone_number=%s AND word=%s", [phone_number, word])
            response = (await fetchone())[0]
            await close_db()
        elif flag == '25':
            phone_number = message[2:13]
            word, mnemonic = message[13:].split(",", 1)
            await connect_db()
            await execute_sql("UPDATE personal_words SET mnemonic=%s WHERE phone_number=%s AND word=%s", [mnemonic, phone_number, word])
            await commit()
            await close_db()
        elif flag == '26':
            phone_number = message[2:13]
            await connect_db()
            await execute_sql("SELECT words.word,chinese FROM personal_words INNER JOIN words ON personal_words.word=words.word WHERE phone_number=%s AND collection=1", [phone_number])
            response = str(await fetchall())
            await close_db()
        elif flag == '27':
            phone_number = message[2:13]
            await connect_db()
            await execute_sql("SELECT vocabulary FROM users WHERE phone_number=%s", [phone_number])
            response = str((await fetchone())[0])
            await close_db()
        elif flag == '28':
            await connect_db()
            await execute_sql("SELECT word,chinese FROM words ORDER BY RAND() LIMIT 5")
            response = str(await fetchall())
            await close_db()
        elif flag == '29':
            word = message[2:]
            await connect_db()
            await execute_sql("SELECT chinese FROM words WHERE word!=%s ORDER BY RAND() LIMIT 3", [word])
            response = str(await fetchall())
            await close_db()
        elif flag == '30':
            phone_number = message[2:13]
            n = int(message[13:])
            await connect_db()
            await execute_sql("UPDATE users SET vocabulary=%s WHERE phone_number=%s", [n, phone_number])
            await commit()
            await close_db()
        elif flag == '31':
            await connect_db()
            await execute_sql("SELECT avatar_num,nickname,vocabulary FROM users ORDER BY vocabulary DESC LIMIT 100")
            response = str(await fetchall())
            await close_db()
        elif flag == '32':
            await connect_db()
            await execute_sql("SELECT avatar_num,nickname,SUM(CASE WHEN mnemonic='' THEN 0 ELSE 1 END)AS mnemonic_count FROM personal_words INNER JOIN users ON personal_words.phone_number=users.phone_number GROUP BY personal_words.phone_number ORDER BY mnemonic_count DESC LIMIT 100")
            response = str(await fetchall())
            await close_db()
        elif flag == '33':
            phone_number = message[2:13]
            await connect_db()
            await execute_sql("SELECT r FROM(SELECT phone_number,RANK() OVER (ORDER BY vocabulary DESC) AS r FROM users)AS t WHERE phone_number=%s", [phone_number])
            response = str((await fetchone())[0])
            await close_db()
        elif flag == '34':
            phone_number = message[2:13]
            await connect_db()
            await execute_sql("SELECT n,r FROM(SELECT phone_number,SUM(CASE WHEN mnemonic='' THEN 0 ELSE 1 END)AS n,RANK()OVER(ORDER BY SUM(CASE WHEN mnemonic='' THEN 0 ELSE 1 END)DESC)AS r FROM personal_words GROUP BY phone_number)AS t WHERE phone_number=%s", [phone_number])
            response = str(await fetchone())
            await close_db()
        elif flag == '35':
            phone_number = message[2:13]
            content = message[13:]
            await connect_db()
            await execute_sql("INSERT INTO feedback(phone_number,content) VALUES(%s,%s)", [phone_number, content])
            await commit()
            await close_db()
        elif flag == '36':
            phone_number = message[2:13]
            await connect_db()
            await execute_sql("SELECT ID,content,timestamp FROM email WHERE phone_number=%s", [phone_number])
            response = str(await fetchall())
            await close_db()
        elif flag == '37':
            id = int(message[2:])
            await connect_db()
            await execute_sql("DELETE FROM email WHERE id=%s", [id])
            await commit()
            await close_db()
        elif flag == '38':
            response = version
        elif flag == '50':
            account = message[2:]
            if account == admin_account:
                response = '1'
        elif flag == '51':
            pwd = message[2:]
            if pwd == admin_passwd:
                response = '1'
        elif flag == '52':
            phone_number = message[2:13]
            await connect_db()
            await execute_sql("SELECT password,nickname,max_favorites,reg_time,vocabulary FROM users WHERE phone_number=%s", [phone_number])
            response = str(await fetchone())
            await close_db()
        elif flag == '53':
            phone_number = message[2:13]
            n = int(message[13:])
            await connect_db()
            await execute_sql("UPDATE users SET max_favorites=%s WHERE phone_number=%s", [n, phone_number])
            await commit()
            await close_db()
        elif flag == '54':
            await connect_db()
            await execute_sql("SELECT phone_number,word,mnemonic FROM personal_words WHERE mnemonic!='' ORDER BY RAND() LIMIT 1")
            response = str(await fetchone())
            await close_db()
        elif flag == '55':
            await connect_db()
            await execute_sql("SELECT * FROM feedback LIMIT 1")
            response = str(await fetchone())
            await close_db()
        elif flag == '56':
            id = int(message[2:])
            await connect_db()
            await execute_sql("DELETE FROM feedback WHERE ID=%s", [id])
            await commit()
            await close_db()
        elif flag == '57':
            phone_number = message[2:13]
            content = message[13:]
            await connect_db()
            await execute_sql("INSERT INTO email(phone_number,content) VALUES(%s,%s)", [phone_number, content])
            await commit()
            await close_db()
        writer.write(response.encode())  # 将处理后的消息发送回客户端
        await writer.drain()  # 确保数据被写入客户端的套接字缓冲区
        writer.close()  # 关闭与客户端的连接
        await writer.wait_closed()  # 等待连接完全关闭


async def main():
    """
    这是主协程函数，创建TCP服务器并开始服务客户端。
    """
    server = await asyncio.start_server(handle_client, IP, PORT)  # 创建一个在本地监听指定端口的TCP服务器
    async with server:
        await server.serve_forever()  # 保持服务器运行状态，处理客户端连接

# 运行主协程函数以启动服务器
asyncio.run(main())
