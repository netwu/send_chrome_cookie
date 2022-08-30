# -*- coding:utf-8 -*-
import time
import datetime
import logging
from HttpApi import HttpApi
from WMUChromeCookie import WMUChromeCookie
from configparser import ConfigParser
cp = ConfigParser()
# 以.cfg结尾的配置文件
cp.read('config.cfg')
# 以.ini结尾的配置文件
log_dir = cp.get('server', 'log_dir')
LOG_FILE_NAME = log_dir+"/log.log"
# 得到 logger 对象
logger = logging.getLogger()

# 初始化 logger


def log_init():
    # 输出的格式
    formatter = logging.Formatter(
        fmt='%(asctime)s  %(filename)s  [line:%(lineno)d]  %(levelname)s :%(message)s',
        datefmt='%Y-%m-%d %H:%M:%S')

    # 设置级别
    logger.setLevel(logging.DEBUG)

    # 控制台的输出
    ch = logging.StreamHandler()
    ch.setFormatter(formatter)

    # log文件的记录
    fh = logging.FileHandler(LOG_FILE_NAME)
    fh.setFormatter(formatter)

    # 将输出的流 添加给logger
    logger.addHandler(ch)
    logger.addHandler(fh)

# 得到yyyy-mm-dd hh:ss:nn格式的字符串


def fmt_now_time():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


if __name__ == '__main__':
    log_init()
    HttpApi = HttpApi()
    cp = ConfigParser()
    cp.read('config.cfg')
    sleepTime = cp.get('server', 'sleep_time')
    cookieHost = cp.get('server', 'cookie_host')
    cookiePushTo = cp.get('server', 'cookie_push_to')
    localHostName, localIp = HttpApi.getLocalPcNameAndAddr()
    print(localHostName, localIp)
    while True:
        try:
            ChromeCookie = WMUChromeCookie()
            newCookiesStr = ChromeCookie.get_cookies(cookieHost)
            ret = HttpApi.pushCookieToServer(
                newCookiesStr, localHostName, localIp, cookiePushTo)
            logger.info("pushCookieToServer ret:%s" % ret)
        except Exception as e:
            logger.error(e)
        time.sleep(int(sleepTime))
