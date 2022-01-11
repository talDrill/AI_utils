import mysql.connector as sql
import logging


def db_connection(host="192.168.1.203", user='israel', pwd="Israel0508!", db='drill_dev'):
    my_db = sql.connect(
        host=host,
        user=user,
        password=pwd,
        database=db,
        auth_plugin='mysql_native_password'
    )
    return my_db


def execute_sql_query(query, db='drill_dev'):
    my_db = db_connection(db)
    my_cursor = my_db.cursor()
    my_cursor.execute(query)
    response = my_cursor.fetchall()
    my_db.commit()
    return response


def register_video_to_db(uuid, name, date, hour, supermarket, city, camera, duration, fps):
    my_db = db_connection()
    my_cursor = my_db.cursor()
    my_cursor.execute("""INSERT IGNORE INTO video (uuid, name, date, hour, supermarket, city, camera, duration, fps) 
            VALUES %s""" % ((uuid, name, date, hour, supermarket, city, camera, duration, fps), ))
    my_db.commit()


def build_video_name(date, hour, camera):
    return date + '_' + hour.replace(':', '-') + '_' + 'camera{}'.format(camera)


def inject_event(buyer_id, key, value):
    assert buyer_id is not None
    my_db = db_connection()
    my_cursor = my_db.cursor()
    my_query = """INSERT IGNORE INTO events (buyer_id, name, name_value) VALUES %s""" % ((buyer_id, key, value), )
    logging.info("DB drill: {}".format(my_query))
    my_cursor.execute(my_query)
    my_db.commit()
