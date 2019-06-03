#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by charles on 2019-05-24
# Function:
import datetime
import pymysql
import logging
from log_config import log_config
from flask import Flask
host = "127.0.0.1"
# host = "47.75.10.215"
port=3306
db="huobi"
user = "huobi"
password="nishengri@huobi"
app = Flask(__name__)

log_config.init_log_config()
logger = logging.getLogger()

@app.route('/huobi/<key>', methods=['GET'])
def huobi_verify(key):

    try:
        logger.info("huobi verify key={}".format(key))
        if not key or len(key) < 10:
            logger.error("invalid key 201, key={}".format(key))
            return "invalid key, key={}".format(key), 201

        conn = pymysql.connect(
            host=host,
            port=port,
            db=db,
            user=user,
            password=password,
            charset='utf8'
        )
        cursor = conn.cursor()
        cursor.execute("""
        select account, expire_date from `users` where access_key=%s""", key)
        ret = cursor.fetchone()
        if not ret:
            logger.error("user does not exist 202, key={}".format(key))
            return "user does not exist.key={}".format(key), 202

        if ret[1]:
            if ret[1] > datetime.datetime.now():
                logger.info("verify 200, key={}".format(key))
                return ret[1].strftime("%Y-%m-%d %H:%M:%S"), 200
            else:
                logger.error("expired 203, key={}".format(key))
                return ret[1].strftime("%Y-%m-%d %H:%M:%S"), 203
        cursor.close()
        conn.close()
    except Exception as e:
        logger.info("exception 204, key={}, e={}".format(key, e))
        return "exception={}".format(e), 204

@app.route('/notify/<key>', methods=['GET'])
def huobi_notify(key):
    try:
        logger.info("huobi notify key={}".format(key))
        # return "我想对所有人说的话", 200
        if not key or len(key) < 10:
            logger.error("invalid key 201, key={}".format(key))
            return "invalid key, key={}".format(key), 201

        conn = pymysql.connect(
            host=host,
            port=port,
            db=db,
            user=user,
            password=password,
            charset='utf8'
        )
        cursor = conn.cursor()
        cursor.execute("""
        select account, expire_date from `users` where access_key=%s""", key)
        ret = cursor.fetchone()
        if not ret:
            logger.error("user does not exist 202, key={}".format(key))
            return "user does not exist.key={}".format(key), 202
        if ret[1]:
            # if ret[0] == "kanyun":
            #     return "阚胖胖, 用的爽不爽？嘿嘿！", 200
            # else:
            #     return "", 201

            left = (ret[1]-datetime.datetime.now()).total_seconds()
            if left <= 0:
                return u"您的使用期限已经到期, 系统将在24小时内停止工作, 为了避免影响您的收益, 请您尽快联系管理员进行续费！ 联系方式: 15691820861", 200
            if left/3600/24 < 3:
                return u"您的使用期限将在 {} 到期, 为了避免影响您的正常使用, 请您尽快联系管理员进行续费！ 联系方式: 15691820861".format(ret[1].strftime("%Y-%m-%d %H:%M:%S")), 200

        cursor.close()
        conn.close()
        return "", 200
    except Exception as e:
        logger.info("exception 204, key={}, e={}".format(key, e))
        return "exception={}".format(e), 204


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
