import psycopg2

try:
    conn = psycopg2.connect(database="ocr", user="postgres", password="admin", host="127.0.0.1", port="5432")
except Exception as e:
    print("Exception occured in db_layer ", e.__doc__ )


def fetch_files():
    """
    get_files_query : str
        query string
    file_obj : List
        query result is list of tuple
    """

    with conn.cursor() as cursor:
        get_files_query = "SELECT file_name, id FROM files where status_code= 0"
        cursor.execute(get_files_query)
        file_obj = cursor.fetchall()
    return file_obj


def fetch_template(template_name):
    """
    param template_name : str
    return: Tuple
    """
    with conn.cursor() as cursor:
        query = "SELECT rules FROM templates where template_name=\'{}\'".format(template_name)
        cursor.execute(query)
        row = cursor.fetchone()
    return row


def update_status_if_exist(file_id):
    """

    """
    with conn.cursor() as cursor:
        query = """UPDATE files SET status_code = 1 where id = %s"""
        cursor.execute(query, (str(file_id)))
        conn.commit()

    return None

def update_status_if_not_exist(file_id, status_code, error_message):
    """

    """
    with conn.cursor() as cursor:
        query = """UPDATE files SET status_code = %s , error_message = %s where id = %s"""
        cursor.execute(query, (str(status_code), error_message, str(file_id)))
        conn.commit()

    return None

if __name__ == "__main__":
    print(fetch_files())
    # # print(fetch_template('thyrocare'))
    # update_status_if_not_exist(1)