import psycopg2

conn = psycopg2.connect(database = "ocr", user = "postgres", password = "admin", host = "127.0.0.1", port = "5432")


def fetch_files():
    with conn.cursor() as cursor:
        get_files_query = "SELECT file_name FROM files where status_code= 0"
        cursor.execute(get_files_query)
        file_obj = cursor.fetcall()
    print(file_obj)
    return file_obj

def fetch_template():
    with conn.cursor() as cursor:
        #cursor.execute("UPDATE bar SET foo = 1 WHERE baz = %s", [self.baz])
        query = "SELECT rules FROM templates where template_name=\'{}\'".format('thyrocare')
        cursor.execute(query)
        row = cursor.fetchone()
    print(row)
    return row


