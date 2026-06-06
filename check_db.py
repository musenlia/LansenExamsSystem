# -*- coding: utf-8 -*-
import sqlite3

try:
    conn = sqlite3.connect('data/exam_system.db')
    print('数据库连接成功')
    
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    
    print('表数量:', len(tables))
    print('表列表:')
    for table in tables:
        print('  -', table[0])
    
    # 检查关键表是否存在
    required_tables = ['users', 'exams', 'questions', 'exam_sessions']
    print('\n关键表检查:')
    for table in required_tables:
        cursor.execute("SELECT COUNT(*) FROM {}".format(table))
        count = cursor.fetchone()[0]
        print('  {}: {} 条记录'.format(table, count))
    
    conn.close()
    print('\n数据库检查完成，所有关键表都正常！')
    
except Exception as e:
    print('数据库连接失败:', str(e))