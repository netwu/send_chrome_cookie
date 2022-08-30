# -*- coding=utf-8 -*-
import os
import sys
import sqlite3
import json
import base64
import aesgcm
import keyring


def dpapi_decrypt(encrypted):
    import ctypes
    import ctypes.wintypes

    class DATA_BLOB(ctypes.Structure):
        _fields_ = [('cbData', ctypes.wintypes.DWORD),
                    ('pbData', ctypes.POINTER(ctypes.c_char))]

    p = ctypes.create_string_buffer(encrypted, len(encrypted))
    blobin = DATA_BLOB(ctypes.sizeof(p), p)
    blobout = DATA_BLOB()
    retval = ctypes.windll.crypt32.CryptUnprotectData(
        ctypes.byref(blobin), None, None, None, None, 0, ctypes.byref(blobout))
    if not retval:
        raise ctypes.WinError()
    result = ctypes.string_at(blobout.pbData, blobout.cbData)
    ctypes.windll.kernel32.LocalFree(blobout.pbData)
    return result


def unix_decrypt(encrypted):
    if sys.platform.startswith('linux'):
        password = b'peanuts'
        iterations = 1
    elif sys.platform.startswith('darwin'):
        password = keyring.get_password('Chrome Safe Storage', 'Chrome')
        password = password.encode('utf8')

        iterations = 1003
    else:
        raise NotImplementedError

    from Crypto.Cipher import AES
    from Crypto.Protocol.KDF import PBKDF2

    salt = b'saltysalt'
    iv = ' ' * 16
    length = 16
    key = PBKDF2(password, salt, length, iterations)
    cipher = AES.new(key, AES.MODE_CBC, IV=iv)
    decrypted = cipher.decrypt(encrypted[3:]).decode('utf-8')
    return decrypted
    # return decrypted[:-ord(decrypted[-1])]


def get_key_from_local_state():
    jsn = None
    with open(os.path.join(os.environ['LOCALAPPDATA'],
                           r"Google\Chrome\User Data\Local State"), encoding='utf-8', mode="r") as f:
        jsn = json.loads(str(f.readline()))
    return jsn["os_crypt"]["encrypted_key"]


def aes_decrypt(encrypted_txt):
    encoded_key = get_key_from_local_state()
    encrypted_key = base64.b64decode(encoded_key.encode())
    encrypted_key = encrypted_key[5:]
    key = dpapi_decrypt(encrypted_key)
    nonce = encrypted_txt[3:15]
    cipher = aesgcm.get_cipher(key)
    return aesgcm.decrypt(cipher, encrypted_txt[15:], nonce)


def chrome_decrypt(encrypted_txt):
    if sys.platform == 'win32':
        try:
            if encrypted_txt[:4] == b'\x01\x00\x00\x00':
                decrypted_txt = dpapi_decrypt(encrypted_txt)
                return decrypted_txt.decode()
            elif encrypted_txt[:3] == b'v10':
                decrypted_txt = aes_decrypt(encrypted_txt)
                return decrypted_txt[:-16].decode()
        except WindowsError:
            return None
    else:
        try:
            return unix_decrypt(encrypted_txt)
        except NotImplementedError:
            return None


def to_epoch(chrome_ts):
    if chrome_ts:
        return chrome_ts - 11644473600 * 000 * 1000
    else:
        return None


class WMUChromeCookie(object):
    # def __init__(self, cookie_file):
    def get_cookie_file(self):
        cookie_file = ''
        if sys.platform == 'win32':
            cookie_file = os.path.join(
                os.environ['USERPROFILE'],
                r'AppData\Local\Google\Chrome\User Data\default\Cookies')
            '''
            AppData\\Local\\Google\\Chrome\\User Data\\Profile [n]\\Cookies
            '''
            if not os.path.exists(cookie_file):
                cookie_file = os.path.join(
                    os.environ['USERPROFILE'],
                    r'AppData\Local\Google\Chrome\User Data\Default\Network\Cookies')
            '''
            AppData\\Local\\Google\\Chrome\\User Data\\Profile [n]\\Cookies
            '''
        elif sys.platform.startswith('linux'):
            cookie_file = os.path.expanduser(
                '~/.config/google-chrome/Default/Cookies')
            if not os.path.exists(cookie_file):
                cookie_file = os.path.expanduser(
                    '~/.config/chromium/Default/Cookies')
        else:
            cookie_file = os.path.expanduser(
                '~/Library/Application Support/Google/Chrome/Default/Cookies')

        if not os.path.exists(cookie_file):
            cookie_file = None

        return cookie_file

    def query_cookies(self, host_key=''):
        with sqlite3.connect(self.get_cookie_file()) as conn:
            result = conn.execute(
                "select host_key, name, encrypted_value,path from cookies where host_key like '%"+host_key+"%'").fetchall()
        return result

    def get_cookies(self, cookie_host):
        res = self.query_cookies(cookie_host)
        cookies = ''
        cookiesDict = {}
        for i in res:
            str = chrome_decrypt(i[2])
            if i[1] == 'JSESSIONID':
                cookies += i[1]+'=' + str+'; '
                cookiesDict[i[1]] = str
            else:
                cookies += i[1]+'=' + str+'; '
                cookiesDict[i[1]] = str
        return cookies
