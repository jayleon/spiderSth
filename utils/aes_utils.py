#! /usr/bin/env python
# -*- coding: utf-8 -*-

from binascii import b2a_hex
from binascii import a2b_hex

from Crypto.Cipher import AES

prefix = 'xy'
secret_dict = {'20160926': ('key......', 'iv......')}
cur_index = '20160926'


class Aes(object):
    def __init__(self, mode=AES.MODE_CBC):
        """AES encrypt and decrypt algorithm.

        :param secret_dict: {index: (key, iv), ...}
        :param cur_index: current index using in secret_dict
        :param mode: AES encrypt mode
        :param prefix: prefix to add after encrypt
        """
        self.secret_dict = secret_dict
        self.cur_index = cur_index
        self.mode = mode
        self.prefix = prefix

        self.block_size = AES.block_size

    def encrypt(self, raw_text):
        """AES encrypt algorithm.

        :param raw_text: text to be encrypted
        :returns: encrypted text (added prefix and secret index)
        """
        key = self.secret_dict[self.cur_index][0]
        iv = self.secret_dict[self.cur_index][1]

        cryptor = AES.new(key, self.mode, iv)
        padding_text = self.__padding(raw_text)
        cipher_text = cryptor.encrypt(padding_text)
        return self.prefix + b2a_hex(cipher_text) + self.cur_index

    def decrypt(self, cipher_text):
        """AES decrypt algorithm.

        If cipher text does not match the prefix, return itself.
        If secret index not in secret_dict, return itself.
        If decrypt process has error, return itself.
        If result of AES decrypt is '', return ''.

        :param cipher_text: encrypted text
        :returns: decrypted text
        """
        if not cipher_text.startswith(self.prefix):
            return cipher_text

        index = cipher_text[-8:]
        if index not in self.secret_dict:
            print('[-] Secret index not exist: {0}'.format(cipher_text))
            return cipher_text

        key = self.secret_dict[index][0]
        iv = self.secret_dict[index][1]

        cryptor = AES.new(key, self.mode, iv)
        try:
            padding_text = cryptor.decrypt(
                a2b_hex(cipher_text[len(self.prefix): -8]))
        except BaseException as e:
            print('[-] Decrypt failed ({0}): {1}'.format(cipher_text, e))
            return cipher_text
        return self.__unpadding(padding_text)

    def __padding(self, s):
        """PKCS#5 padding.

        Raw text should be 16x (because block_size is 16).
        If len(s) is rl, then the padding_length is (16 - rl % 16),
        we should add chr(padding_length) for padding_length times.

        >>> raw_text = '12345678901'
        >>> rl = len(raw_text)  # rl = 11
        >>> padding_length = 16 - rl % 16  # padding_length = 5
        >>> padding_text  # '12345678901\x05\x05\x05\x05\x05'
        """
        padding_length = self.block_size - len(s) % self.block_size
        return s + padding_length * chr(padding_length)

    def __unpadding(self, s):
        """PKCS#5 unpadding.

        Strip suffix of padding_text.
        """
        return s[0: -ord(s[-1])]

def load_normal_mobile(path):
    normal_mobile_list = []
    file_object = open(path, 'rb')
    for line in file_object:
        line = line.replace('\r', '').replace('\n', '')
        print line
        if line.strip():
            normal_mobile_list.append(line)
    return normal_mobile_list


if __name__ == "__main__":

    aes = Aes()

    # Encrypt
    # Input: 11122222
    # Output: xye7944a671526b829c24c102d7433f4e020160926
    print aes.encrypt('11122222')

    # Decrypt
    # Input: xye7944a671526b829c24c102d7433f4e020160926
    # Output: 11122222
    block_value = 'xy1ce61091db6e9f71f3dbe758b55b3c3920160926'
    if block_value.startswith('xy'):
        block_value = aes.decrypt(block_value)
    print block_value
