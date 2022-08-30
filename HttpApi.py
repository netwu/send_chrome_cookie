# -*- coding:utf-8 -*-
import socket
import requests
from configparser import ConfigParser


class HttpApi(object):
    headers = {}
    userAgent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.93 Safari/537.36'

    def pushCookieToServer(self, cookieStr, localHostName, localIp, cookiePushTo):
        reqData = {}
        reqData["hostname"] = localHostName
        reqData["ip"] = localIp
        reqData["cookie"] = cookieStr
        reqData["userAgent"] = self.userAgent
        response = self.requestApi(
            "POST", cookiePushTo, param=reqData, header=self.headers)
        return response

    def getLocalPcNameAndAddr(self):
        hostname = socket.gethostname()
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        return hostname, ip

    def requestApi(self,
                   method='GET',
                   url_path='',
                   param={},
                   header={}):  # 以GET或POST请求API（签名验证的形式）返回结果的字典格式
        try:
            s = requests.Session()
            print(header, url_path, param)
            # s.keep_alive = False  # 关闭多余连接
            r = None
            if method == 'GET':
                r = s.get(url_path, headers=header, params=param)
            if method == 'POST':
                r = s.post(url_path,
                           json=param,
                           headers=header)
            return r.text
        except Exception as e:
            print(repr(e))
            return []  # 出错返回空，以便len(res)
