import mysql.connector
from datetime import datetime
import configparser

# 读取配置文件
config = configparser.ConfigParser()
config.read('config.ini')

# 配置数据库列表
databases = {section: dict(config[section]) for section in config.sections()}

# 备份目录
backup_dir = "E:\\WorkspacePython\\MySqlBackup\\scripts"


def backup_database(database_config):
    try:
        # 连接到数据库
        with mysql.connector.connect(**database_config) as connection, connection.cursor() as cursor:
            # 获取当前时间作为备份文件名
            backup_file = f"{backup_dir}/{database_config['database']}_{datetime.now().strftime('%Y%m%d')}.sql"

            # 执行备份命令
            with open(backup_file, 'w', encoding='utf-8') as file:
                # 获取创建数据库sql
                # cursor.execute("SHOW CREATE DATABASE `{}`".format(config['database']))
                # create_database_sql = cursor.fetchone()[1]
                file.write("""/*
     Python backup script
        
     Source Server : {user}@{host}:{port}
        
     Date          : {date}
    */\n\n""".format(user=database_config['user'], host=database_config['host'], port=database_config['port'],
                     date=datetime.now().strftime('%Y-%m-%d %H:%M:%S')))

                # 指定字符集
                file.write("SET NAMES utf8mb4;\n")
                # 关闭外键检查
                file.write("SET FOREIGN_KEY_CHECKS = 0;\n")

                cursor.execute(
                    "SELECT * FROM information_schema.TABLES WHERE TABLE_SCHEMA='{}'".format(database_config['database']))
                tables = cursor.fetchall()
                for table in tables:
                    table_name = table[2]
                    file.write("""
    -- ----------------------------
    -- Table structure for {}
    -- ----------------------------\n\n""".format(table_name))
                    # 表存在则删除
                    file.write("DROP TABLE IF EXISTS `{}`;\n".format(table_name))
                    # 建表语句
                    cursor.execute("SHOW CREATE TABLE {}".format(table_name))
                    create_table_sql = cursor.fetchone()[1]
                    file.write(create_table_sql + ";\n\n")

                    # 获取表数据
                    data_cursor = connection.cursor()
                    data_cursor.execute(f"SELECT * FROM {table_name}")
                    rows = data_cursor.fetchall()
                    column_names = [desc[0] for desc in data_cursor.description]

                    if len(rows) > 0:
                        file.write("""-- ----------------------------
    -- Records of {}
    -- ----------------------------\n\n""".format(table_name))

                        for row in rows:
                            str_row = [str(item).replace('\n', '\\n').replace('\t', '\\t').replace('\r', '\\r') for item in
                                       row]
                            values = tuple(str_row)
                            insert_sql = f"INSERT INTO `{table_name}` ({', '.join(column_names)}) VALUES ({', '.join(['%s'] * len(values))});\n"
                            file.write(insert_sql % values)

                # 开启外键检查
                file.write("\n\nSET FOREIGN_KEY_CHECKS = 1;\n")

            print(f"Write to file successfully: {backup_file}")
    except mysql.connector.Error as err:
        print(f"Error: {err}")


if __name__ == "__main__":
    for section, db_config in databases.items():
        print('{}: Backup'.format(section))
        backup_database(db_config)
        print('{}: Done\n'.format(section))
