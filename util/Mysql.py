#!/usr/bin/env python
# encoding: utf-8

"""
@file: Mysql.py
@time: 2018/5/11 18:32
@desc: 数据库操作类
@author: hongquanpro@126.com
@note:
1、执行带参数的 SQL 时，请先用sql语句指定需要输入的条件列表，然后再用 tuple/list 进行条件批配
２、在格式 SQL 中不需要使用引号指定数据类型，系统会根据输入参数自动识别
３、在输入的值中不需要使用转意函数，系统会自动处理
"""

import pymysql
from pymysql.cursors import DictCursor
from DBUtils.PooledDB import PooledDB
from jianshu.util.DBConfig import *


class Mysql(object):
    """
    MYSQL数据库对象，负责产生数据库连接 , 此类中的连接采用连接池实现
    获取连接对象：conn = Mysql.getConn()
    释放连接对象;conn.close()或del conn
    """

    # 连接池对象
    __pool = None

    def __init__(self):
        """
        数据库构造函数，从连接池中取出连接，并生成操作游标
        """
        self._conn = Mysql.__get_conn()
        self._cursor = self._conn.cursor()

    @staticmethod
    def __get_conn():
        """
        @summary: 静态方法，从连接池中取出连接
        @return MySQLdb.connection
        """
        if Mysql.__pool is None:
            __pool = PooledDB(creator=pymysql, mincached=1, maxcached=20,
                              host=DBConfig.DBHOST, port=DBConfig.DBPORT, user=DBConfig.DBUSER, passwd=DBConfig.DBPWD,
                              db=DBConfig.DBNAME, use_unicode=False, charset=DBConfig.DBCHAR, cursorclass=DictCursor)
        return __pool.connection()

    def get_all(self, sql, param=None):
        """
        @summary: 执行查询，并取出所有结果集
        @param sql:查询SQL，如果有查询条件，请只指定条件列表，并将条件值使用参数[param]传递进来
        @param param: 可选参数，条件列表值（元组/列表）
        @return: result list/boolean 查询到的结果集
        """
        if param is None:
            count = self._cursor.execute(sql)
        else:
            count = self._cursor.execute(sql, param)
        if count > 0:
            result = self._cursor.fetchall()
        else:
            result = False
        return result

    def get_one(self, sql, param=None):
        """
        @summary: 执行查询，并取出第一条
        @param sql:查询SQL，如果有查询条件，请只指定条件列表，并将条件值使用参数[param]传递进来
        @param param: 可选参数，条件列表值（元组/列表）
        @return: result list/boolean 查询到的结果集
        """
        if param is None:
            count = self._cursor.execute(sql)
        else:
            count = self._cursor.execute(sql, param)
        if count > 0:
            result = self._cursor.fetchone()
        else:
            result = False
        return result

    def get_many(self, sql, num, param=None):
        """
        @summary: 执行查询，并取出num条结果
        @param sql:查询SQL，如果有查询条件，请只指定条件列表，并将条件值使用参数[param]传递进来
        @param num:取得的结果条数
        @param param: 可选参数，条件列表值（元组/列表）
        @return: result list/boolean 查询到的结果集
        """
        if param is None:
            count = self._cursor.execute(sql)
        else:
            count = self._cursor.execute(sql, param)
        if count > 0:
            result = self._cursor.fetchmany(num)
        else:
            result = False
        return result

    def insert_one(self, sql, value):
        """
        @summary: 向数据表插入一条记录
        @param sql:要插入的SQL格式
        @param value:要插入的记录数据tuple/list
        @return: insert_id 受影响的行数
        """
        insert_id = 0
        try:
            self._cursor.execute(sql, value)
            self._conn.commit()
            insert_id = self.__get_insert_id()
        except:
            self._conn.rollback()
        return insert_id

    def insert_many(self, sql, values):
        """
        @summary: 向数据表插入多条记录
        @param sql:要插入的SQL格式
        @param values:要插入的记录数据tuple(tuple)/list[list]
        @return: count 受影响的行数
        """
        try:
            count = self._cursor.executemany(sql, values)
            self._conn.commit()
        except:
            self._conn.rollback()
        return count

    def __get_insert_id(self):
        """
        获取当前连接最后一次插入操作生成的id,如果没有则为０
        """
        self._cursor.execute("SELECT @@IDENTITY AS id")
        result = self._cursor.fetchall()
        return result[0]['id']

    def __query(self, sql, param=None):
        if param is None:
            count = self._cursor.execute(sql)
        else:
            count = self._cursor.execute(sql, param)
        return count

    def update(self, sql, param=None):
        """
        @summary: 更新数据表记录
        @param sql: SQL格式及条件，使用(%s,%s)
        @param param: 要更新的  值 tuple/list
        @return: count 受影响的行数
        """
        try:
            result = self.__query(sql, param)
            self._conn.commit()
        except:
            self._conn.rollback()
        return result

    def delete(self, sql, param=None):
        """
        @summary: 删除数据表记录
        @param sql: SQL格式及条件，使用(%s,%s)
        @param param: 要删除的条件 值 tuple/list
        @return: count 受影响的行数
        """
        try:
            result = self.__query(sql, param)
            self._conn.commit()
        except:
            self._conn.rollback()
        return result

    def dispose(self, is_end=1):
        """
        @summary: 释放连接池资源
        """
        if is_end == 1:
            self._conn.commit()
        else:
            self._conn.rollback()
        self._cursor.close()
        self._conn.close()
