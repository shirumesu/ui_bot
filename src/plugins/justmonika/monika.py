class JustMonika:

    __cj = [
        "j",
        "𝔍",
        "𝕵",
        "𝕁",
        "Ĵ",
        "ɟ",
        "ʄ",
        "ᴊ",
    ]
    __cu = [
        "Ù",
        "Ű",
        "ű",
        "Ų",
        "𝓾",
        "𝖀",
        "𝕌",
    ]
    __cs = [
        "Ṧ",
        "Ṡ",
        "Ş",
        "Ṣ",
        "ᵴ",
        "ᶊ",
        "ʂ",
        "ȿ",
    ]
    __ct = [
        "ẗ",
        "ᵵ",
        "ƫ",
        "ȶ",
        "ƾ",
        "ʇ",
        "ᴛ",
        "ʨ",
        "ᵺ",
    ]
    __cm = [
        "𝕞",
        "𝓜",
        "𝔐",
        "𝕄",
        "𝕸",
    ]
    __co = [
        "𝓞",
        "𝔒",
        "ɵ",
        "ɔ",
        "œ",
        "ᴔ",
    ]
    __cn = [
        "𝔫",
        "𝕟",
        "𝔑",
        "ℕ",
        "𝕹",
        "𝖭",
    ]
    __ci = [
        "Ɩ",
        "ɩ",
        "ᵼ",
        "ᴉ",
        "ɿ",
    ]
    __ck = [
        "𝓀",
        "𝓴",
        "Ⱪ",
        "ⱪ",
        "ᶄ",
        "ĸ",
        "ʞ",
        "ᴋ",
    ]
    __ca = [
        "𝕒",
        "ᶏ",
        "ẚ",
        "ᶐ",
        "ᴀ",
    ]

    __sj = len(__cj)
    __su = len(__cu)
    __ss = len(__cs)
    __st = len(__ct)
    __sm = len(__cm)
    __so = len(__co)
    __sn = len(__cn)
    __si = len(__ci)
    __sk = len(__ck)
    __sa = len(__ca)

    __ska = __sk * __sa
    __sika = __si * __ska
    __snika = __sn * __sika
    __sonika = __so * __snika
    __smonika = __sm * __sonika
    __stmonika = __st * __smonika
    __sstmonika = __ss * __stmonika
    __sustmonika = __su * __sstmonika

    def __encodeShort(self, i: int) -> str:
        """
        双字节编码
        """
        r = [
            self.__cj[i // self.__sustmonika],
            self.__cu[i % self.__sustmonika // self.__sstmonika],
            self.__cs[i % self.__sstmonika // self.__stmonika],
            self.__ct[i % self.__stmonika // self.__smonika],
            self.__cm[i % self.__smonika // self.__sonika],
            self.__co[i % self.__sonika // self.__snika],
            self.__cn[i % self.__snika // self.__sika],
            self.__ci[i % self.__sika // self.__ska],
            self.__ck[i % self.__ska // self.__sa],
            self.__ca[i % self.__sa],
        ]
        return "".join(r)

    def __decodeShort(self, s: str) -> int:
        """
        解码成双字节
        """
        try:
            idx = [
                self.__cj.index(s[0]),
                self.__cu.index(s[1]),
                self.__cs.index(s[2]),
                self.__ct.index(s[3]),
                self.__cm.index(s[4]),
                self.__co.index(s[5]),
                self.__cn.index(s[6]),
                self.__ci.index(s[7]),
                self.__ck.index(s[8]),
                self.__ca.index(s[9]),
            ]
        except:
            return 0
        r = (
            idx[0] * self.__sustmonika
            + idx[1] * self.__sstmonika
            + idx[2] * self.__stmonika
            + idx[3] * self.__smonika
            + idx[4] * self.__sonika
            + idx[5] * self.__snika
            + idx[6] * self.__sika
            + idx[7] * self.__ska
            + idx[8] * self.__sa
            + idx[9]
        )
        return r

    def encodeBytes(self, bs: bytes) -> str:
        """
        字节编码
        参数:
            bs: 字节数据
        返回:
            str: 密文
        """
        r = []
        l = len(bs) >> 1
        for i in range(0, l):
            r.append(self.__encodeShort((bs[i * 2] << 8) | bs[i * 2 + 1]))
        return "".join(r)

    def encode(self, s: str, encoding: str = "utf-8") -> str:
        """
        文本编码
        参数:
            s: 明文
            encoding: 字符串编码方式
        返回:
            str: 密文
        """
        bs = s.encode(encoding)
        r = self.encodeBytes(bs)
        return r

    def decodeBytes(self, s: str) -> bytes:
        """
        解码为字节
        参数:
            s: 密文
        返回:
            bytes: 二进制数据
        """
        r = []
        l = len(s) >> 2
        for i in range(0, l):
            value = self.__decodeShort(s[i * 10 : i * 10 + 10])
            r.append(bytes([value >> 8]))
            r.append(bytes([value & 0xFF]))
        return b"".join(r)

    def decode(self, s: str, encoding: str = "utf-8") -> str:
        """
        解码为文本
        参数:
            s: 密文
            encoding: 字符串编码方式
        返回:
            str: 明文
        """
        r = self.decodeBytes(s).decode(encoding)
        return r
