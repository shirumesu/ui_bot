import sqlite3

from loguru import logger


class SQL_service:
    """操作SQL数据库

    将四个主要操作(insert,update,delect,select)变为可以随意插入数据的函数
    需要额外实现的sql函数将会在插件单独增加sql_extension.py中

    Attrrbuts:
        conn = SQL.connect()
        curs = conn.cursor()
    """

    def __enter__(self):
        """使用with语法进入 连接数据库"""
        self.conn = sqlite3.connect("user_data.db")
        self.curs = self.conn.cursor()
        return self

    def insert(
        self, table_name: str, columns: list[str], values: list[str / int]
    ) -> None:
        """插入语句

        Args:
            table_name: 数据库表单名字
            columns: 要插入的栏位名,格式list[str,str]
            values: 对应栏位的数据,格式list[str/int,str/int]
        """
        columns = [str(x).strip() if x != "null" else None for x in columns.split(",")]
        values = [str(x).strip() for x in values.split(",")]
        text_col = str(columns)[1:-1]
        text_val = str(values)[1:-1]
        self.curs.execute(f"insert into {table_name}({text_col}) values ({text_val})")

    def update(
        self,
        table_name: str,
        columns: list[str],
        values: list[str / int],
        condition: str,
    ) -> None:
        """更新语句

        Args:
            table_name: 数据库表单名字
            columns: 要更新的栏位名,格式list[str,str]
            values: 对应栏位的数据,格式list[str/int,str/int]
            condition: 条件,为sql语句中where后的所有文本
        """
        text = ""
        for column, value in zip(columns.split(","), values.split(",")):
            text += f"{column} = {value},"
            text = text[:-1]
        self.curs.execute(f"update {table_name} set {text} where {condition}")

    def delect(self, table_name: str, condition: str):
        """删除语句

        Args:
            table_name: 数据库表单名字
            condition: 条件,为sql语句中where后的所有文本
        """
        self.curs.execute(f"delect from {table_name} where {condition}")

    def select(
        self,
        pros: str,
        table_name: str,
        condition_0: bool = None,
        condition_1=None,
        tof: bool = False,
    ):
        """Select语句

        Args:
            pros： 要select的东西 示例:select pros from ···
            table_name: 数据库表单名字
            condition_[0|1]: 条件 示例:select ··· where condition_0 = condition_1
            tof: True -> 精准搜索,各条件之间用and连接
                 False -> 模糊搜索,各条件之间用or连接
        """
        text_list = []
        if condition_0:
            for con1, con2 in zip(condition_0.split(","), condition_1.split(",")):
                text_list.append(f"{con1.strip()} = '{con2.strip()}'")
            text = " and ".join(text_list) if tof else "or".join(text_list)
            self.curs.execute(
                f"select {pros} from {table_name} where {'' if not condition_0 else text}"
            )
        else:
            self.curs.execute(f"select {pros} from {table_name}")
        return self.curs

    def __exit__(self, r, s, d):
        try:
            self.curs.close()
            self.conn.commit()
            self.conn.close()
        except sqlite3.ProgrammingError as e:
            logger.warning(f"读写数据库时发生错误:{e}")
