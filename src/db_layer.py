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
        query result is list 0f tuple
    """

    with conn.cursor() as cursor:
        get_files_query = "SELECT file_name FROM files where status_code= 0"
        cursor.execute(get_files_query)
        file_obj = cursor.fetchall()
    print(file_obj)
    return file_obj


def fetch_template(template_name):
    """
    param template_name : str
    return: Tuple
    """
    with conn.cursor() as cursor:
        # cursor.execute("UPDATE bar SET foo = 1 WHERE baz = %s", [self.baz])
        query = "SELECT rules FROM templates where template_name=\'{}\'".format(template_name)
        cursor.execute(query)
        row = cursor.fetchone()
    print(row)
    return row


if __name__ == "__main__":
    print(fetch_files())
    print(fetch_template('thyrocare'))