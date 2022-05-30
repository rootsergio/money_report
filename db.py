import sqlite3


async def db_crud(sql: str, params: tuple):
    conn = sqlite3.connect('data.db')
    cur = conn.cursor()
    cur.execute(sql, params)
    conn.commit()
    conn.close()


async def db_select():
    conn = sqlite3.connect('data.db')
    cur = conn.cursor()
    cur.execute("SELECT * FROM money")
    result = cur.fetchall()
    conn.close()
    return [row for row in cur.description], result
