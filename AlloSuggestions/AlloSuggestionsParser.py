"""
Parse all suggestions from allo.ua for combinations of letters (2 and 3 chars long)
Save results to SQLite
format: id|query|suggestion
[!] Total Time Taken: 598.68 seconds
"""

from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException
from selenium import webdriver
from concurrent.futures import ThreadPoolExecutor, as_completed
from sqlite3 import Error
import sqlite3
import itertools
import platform
import string
import time
import sys
import os


def create_db_connection():
    try:
        conn = sqlite3.connect("allo_db.sqlite3")
        print("[+] Connected to database")
        return conn
    except Error as e:
        sys.exit(f"[-] Error: {e}\nFailed to connect to db and to create it")


def create_table(connection):
    try:
        cursor = connection.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS suggestions (
                 query text NOT NULL,
                 result text NOT NULL 
                 );
        """)

    except Error as e:
        sys.exit("[-] Failed to create table. Exiting...")


def generate_queries(connection):
    try:
        cursor = connection.cursor()
        # get all queries that were saved except those that don't have any results
        cursor.execute("SELECT DISTINCT query FROM suggestions")
    except Error as e:
        sys.exit("[-] Failed to execute query. Exiting...")
    else:
        # convert list of tuples to list of strings
        saved = [query[0] for query in cursor.fetchall()]
        # all possible combinations (there is no results for single char in search bar -> skip it)
        # combinations/combinations_with_replacement/permutations/product?
        # merge 2 lists
        combinations = []
        for i in range(2):
            combinations.extend(list(map("".join, itertools.combinations(string.ascii_lowercase, 2 + i))))

        # find difference between all possible combinations and already saved
        queries = list(set(combinations).symmetric_difference(saved))
        size = len(queries)
        print(f"Queries to run: {size}")
        if size == 0:
            sys.exit(1)
        
        return queries


# for some reason not all selenium instances quit after driver.quit() call
# make sure that nothing left on a background
def quit_left_threads():
    # if there is nothing left it will return an error msg from cmd
    # but there is no point to catch it -> it does't effect the script
    if platform.system().lower() == "windows":
        os.system("taskkill /F /IM firefox.exe")
    # it should work for both unix/mac (100% on unix, can't test on Mac)
    else:
        os.system("pkill -f firefox")


def make_headless():
    options = Options()
    # set it to headless mode
    options.headless = True
    return options


def create_browser():
    driver = webdriver.Firefox(options=HEADLESS_OPTION)
    driver.set_page_load_timeout(15)
    return driver


def get_suggestion(queries):
    driver = create_browser()
    try:
        driver.get("https://allo.ua/")
    except TimeoutException:
        return

    search_bar = driver.find_element_by_id("search")
    output = []
    for query in queries:

        try:
            search_bar.send_keys(query)
            # wait till <li> with suggestions appear
            wait = WebDriverWait(driver, 2)
            wait.until(EC.visibility_of_all_elements_located((By.CLASS_NAME, 'search-suggest-word')))
            # find <ul> which contains <li> with results
            ul = driver.find_element_by_id("search-suggest-query")
        except TimeoutException:
            print("[-] Nothing was found")
            # mark query as empty if it doesn't return any result
            output.append({query: "EMPTY"})
        except StaleElementReferenceException:
            print("[-] Frozen element")
            output.append({query: "EMPTY"})
        # if there wasn't Timeout error else code will be executed
        else:
            # populate list with suggestion results
            output.extend([{query: link.text} for link in ul.find_elements_by_class_name("search-suggest-word")])
            print(f"[*] {query} was processed and is waiting for saving")
        finally:
            # clear input field
            search_bar.clear()
            # it's necessary to click on any random spot to make JS suggestion pop up disappear
            driver.find_element_by_class_name("line").click()
    # close driver instance
    driver.close()
    driver.quit()
    return output

# TODO find the way to optimize a step
def get_step(size):
    if size < MAX_WORKERS:
        step = 1
    else:
        step = size // MAX_WORKERS
    return step


def main(search_queries, connection):
    # cursor for db
    cursor = connection.cursor()

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:

        queries_size = len(search_queries)
        step = get_step(queries_size)

        print("Starting threads...")
        results = [executor.submit(get_suggestion, search_queries[x:x+step]) for x in range(0, queries_size, step)]
        # wait for completion of all tasks
        for data in as_completed(results):
            data = data.result()
            if data is not None:
                for query_result in data:
                    for key, val in query_result.items():
                        try:
                            cursor.execute("""INSERT INTO suggestions (query, result) 
                                               VALUES (?, ?);""", (key, val))
                            connection.commit()
                            print(f"[+] Successfully added {key}:{val} into table")
                        except Error as e:
                            print(e)

    # close db connection and cursor
    cursor.close()
    connection.close()


if __name__ == '__main__':
    # add args to set threads?
    MAX_WORKERS = 10
    start_time = time.time()
    HEADLESS_OPTION = make_headless()
    try:
        # db config phase
        db_connection = create_db_connection()
        create_table(db_connection)
        # main phase
        all_search_queries = generate_queries(db_connection)
        main(all_search_queries, db_connection)
    except KeyboardInterrupt:
        print("[*] Ctrl+C was pressed. Exiting")
    except Exception as e:
        print(e)
    # end phase
    finally:
        quit_left_threads()
        total_time = time.time() - start_time
        print(f"[!] Total Time Taken: {total_time:.2f} seconds")
        print("[!] End of program")
        os._exit(1)
