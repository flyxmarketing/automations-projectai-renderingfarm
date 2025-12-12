import psycopg2
import psycopg2.extras

def db_connect():
    db_link = psycopg2.connect(
        database="vwM8xdFDLiPD",
        user="vwM8xdFDLiPD",
        password="cGpgHqjnnQk3a3iuc9",
        host="95.216.9.152",
        port="47523",
        sslmode="require"
    )
    db_link.autocommit = True
    return db_link

def db_cursor():
    db_link = db_connect()
    db_cursor = db_link.cursor(
        cursor_factory = psycopg2.extras.RealDictCursor
    )
    return db_cursor

def db_execute(db_cursor, query, params=()):
    db_cursor.execute(query, params)
    return db_cursor

def db_close(db_cursor):
    db_link = db_cursor.connection
    db_link.commit()
    db_cursor.close()
    db_link.close()

#
# Example execution
# -> Why like this?
# ->-> Connect-Link-Execute-Return-Close ( 1 link for 1 task )
#
# query = db_execute("SELECT * FROM pg_user;")
# users = query.fetchall()
# for user in users:
#     user_details = dict(user)
#     print(f"{user_details['usename']}")
# db_close(query)
#
