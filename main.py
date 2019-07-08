#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by charles on 2019-05-24
# Function:
import json
import datetime
import pymysql
import logging
from log_config import log_config
from flask import Flask, request, Response
host = "127.0.0.1"
# host = "47.75.10.215"
port=3306
db="huobi"
db_user = "huobi"
db_password="nishengri@huobi"
app = Flask(__name__)

log_config.init_log_config()
logger = logging.getLogger()

def get_conn():
    conn = pymysql.connect(
        host=host,
        port=port,
        db=db,
        user=db_user,
        password=db_password,
        charset='utf8'
    )

    return conn


@app.route('/huobi/login/', methods=["POST"])
def huobi_login():
    account = request.json.get("account", "")
    password = request.json.get("password", "")
    ret = login(account, password)
    return Response(json.dumps(ret), mimetype='application/json')


@app.route('/huobi/logout/', methods=["POST"])
def huobi_logout():
    account = request.json.get("account", "")
    ret = logout(account)
    return Response(json.dumps(ret), mimetype='application/json')


@app.route('/huobi/heart/', methods=["POST"])
def huobi_heart():
    account = request.json.get("account", "")
    ret = heart(account)
    return Response(json.dumps(ret), mimetype='application/json')



def login(account, password):
    try:
        conn = None
        cursor = None
        logger.info("valid_login={}".format(account))
        if not account or len(account) < 6 or not password or len(password)<6:
            logger.error("invalid account or password, account={}".format(account))
            return {"code": -1, "data": "", "msg": u"账号无效!"}

        if str(account).startswith("15691820861110"):
            return {"code": 1, "data": "2020-02-02 02:02:02", "msg": u"登录成功！"}

        conn = get_conn()
        cursor = conn.cursor()
        cursor.execute("""
           select expire_date, in_use, last_use from `users` where account=%s and password=%s""", (account, password))
        ret = cursor.fetchone()

        if not ret:
            logger.error("wrong account or password, account={}".format(account))
            return {"code": -1, "data": "", "msg": u"用户名或密码错误!"}

        expire_date, in_use, last_user = ret
        if expire_date:
            if expire_date <= datetime.datetime.now():
                logger.warning("expired. account={}, expired={}".format(account, ret[0].strftime("%Y-%m-%d %H:%M:%S")))
                return {"code": 0, "data": expire_date.strftime("%Y-%m-%d %H:%M:%S"), "msg": u"抱歉！您的账号已过期, 请联系客服续费！"}

            # in use??
            if in_use == 1:
                # 已经在用，也有可能是程序异常退出了导致没有及时注销，　再判断心跳时间时不是已经超过300秒了，如果已经过了，也可以登录
                if last_user:
                    if (datetime.datetime.now() - ret[2]).total_seconds() > 180:
                        cursor.execute("update `users` set in_use=1, last_use=%s where account=%s",
                                       (datetime.datetime.now(), account))
                        conn.commit()
                        return {"code": 1, "data": expire_date.strftime("%Y-%m-%d %H:%M:%S"), "msg": u"登录成功！"}
                    else:
                        logger.warning("in user and last use near 300s")
                        return {"code": 2, "data": expire_date.strftime("%Y-%m-%d %H:%M:%S"), "msg": u"登录失败, 不允许同一账号重复登录, 请3分钟后重试！"}
                else:
                    logger.warning("in use and last use near 300s")
                    return {"code": 2, "data": expire_date.strftime("%Y-%m-%d %H:%M:%S"),
                            "msg": u"登录失败, 不允许同一账号重复登录, 请3分钟后重试！"}

            else:
                cursor.execute("update `users` set in_use=1, last_use=%s where account=%s",
                               (datetime.datetime.now(), account))
                conn.commit()
                return {"code": 1, "data": expire_date.strftime("%Y-%m-%d %H:%M:%S"), "msg": u"登录成功！"}
        else:
            return {"code": 0, "data": "", "msg": u"登录失败, 未知的有效期!"}
    except Exception as e:
        logger.info("login exception, account={}, e={}".format(account, e))
        return {"code": -1, "data": "", "msg": "登录服务器异常, 请稍后重试!"}
    finally:
        if cursor and conn:
            cursor.close()
            conn.close()


def heart(account):
    try:
        conn = get_conn()
        cursor = conn.cursor()
        cursor.execute("update `users` set last_use=%s where account=%s", (datetime.datetime.now(), account))
        conn.commit()

        cursor.execute("""
           select expire_date from `users` where account=%s""", (account, ))
        ret = cursor.fetchone()
        if ret:
            expire_date = ret[0]
            return {"code": 1, "data": expire_date.strftime("%Y-%m-%d %H:%M:%S"), "msg": u"心跳发送成功!"}
        else:
            return {"code": 0, "data": "", "msg": u"未找到当前账号信息!"}

        cursor.close()
        conn.close()
    except Exception as e:
        logger.error("heart failed, account={}, e={}".format(account, str(e)))
        return {"code": -1, "data": "", "msg": "心跳服务器异常, 请稍后重试!"}


def logout(account):
    try:
        conn = get_conn()
        cursor = conn.cursor()
        cursor.execute("update `users` set in_use=0 where account=%s", (account, ))
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        logger.error("logout faild, account={}".format(account))
        return {"code": -1, "data": "", "msg": "注销服务器异常, 请稍后重试!"}

    return {"code": 1, "data": "", "msg": "注销成功!"}



@app.route('/huobi/<key>', methods=['GET'])
def huobi_verify(key):

    try:
        logger.info("huobi verify key={}".format(key))
        if not key or len(key) < 10:
            logger.error("invalid key 201, key={}".format(key))
            return "invalid key, key={}".format(key), 201

        conn = get_conn()
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
