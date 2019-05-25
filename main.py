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
port=3306
db="huobi"
user = "huobi"
password="nishengri"
app = Flask(__name__)

log_config.init_log_config()
logger = logging.getLogger()
@app.route('/huobi/<key>', methods=['GET'])
def huobi_verify(key):

    try:
        logger.info("huobi verify key={}".format(key))
        if not key or len(key) < 10:
            logger.error("invalid key 201, key={}".format(key))
            return "invalid key--{}".format("unknown"), 201

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
        select account, expire_date from keys where access_key=%s""", key)
        ret = cursor.fetchone()
        if not ret:
            logger.error("user does not exist 202, key={}".format(key))
            return "user does not exist.", 202

        if ret[1]:
            if ret[1] > datetime.datetime.now():
                logger.info("verify 200, key={}".format(key))
                return ret[1].stftime("%Y-%m-%d %H:%M:%S"), 200
            else:
                logger.error("expired 203, key={}".format(key))
                return ret[1].stftime("%Y-%m-%d %H:%M:%S"), 203
        cursor.close()
        conn.close()
    except Exception as e:
        logger.info("exception 204, key={}, e={}".format(key, e))
        return "exception", 204


if __name__ == '__main__':
    app.run()
