"""
Parse muz-tv top hits and add them to mysql database
"""

import requests
from bs4 import BeautifulSoup
from mysql.connector import MySQLConnection, Error
from read_config import read_db_config


def get_html(url):
    page = requests.get(url)
    page.raise_for_status()
    html = BeautifulSoup(page.text, 'lxml')

    return html


def check_db_table(curs):
    try:
        # if there isn't this db -> create one
        curs.execute('CREATE DATABASE IF NOT EXISTS music;')

        curs.execute("USE music;")

        # create table if doesn't exist and add unique constraint at song/link
        curs.execute("CREATE TABLE IF NOT EXISTS top " +
                       "(id INT AUTO_INCREMENT, " +
                       "singer VARCHAR(255) NOT NULL, " +
                       "song VARCHAR(255) NOT NULL," +
                       "link VARCHAR(255) NOT NULL," +
                       "likes int NOT NULL, " +
                       "PRIMARY KEY (id), CONSTRAINT U_SONG UNIQUE(song, link)) " +
                       "DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;")
    except Error as e:
        print(e)
    finally:
        print("Database and table are set up and ready")


def main():
    # get configs for db
    db_config = read_db_config()
    url = 'http://muz-tv.ru/hit-online/'

    try:
        mydb = MySQLConnection(**db_config)
        cursor = mydb.cursor()
        print("Successfully connected to %s" % db_config['host'])

        check_db_table(cursor)

        p_number = 1
        while not url.endswith("=31"):

            html = get_html(url)

            divs = html.find('div', class_='b-music-list').find_all('div', class_='b-block b-clearbox x-hit-item')

            for div in divs:
                h3 = div.find_all('h3')

                # link to detail page
                link = "muz-tv.ru"+(h3[0].find('a').get('href'))

                like = div.find('div', class_='b-but_text').find('span').text.strip('()')

                # get singer name and song
                info = {h3[0].text: h3[1].text.strip()}

                # insert into db
                for singer, song in info.items():

                    try:
                        sql = "INSERT INTO top(singer, song, link, likes) VALUES(%s, %s, %s, %s);"
                        val = singer, song, link, like
                        cursor.execute(sql, val)
                        mydb.commit()
                        print(singer, song, link, like, "Successfully added to table")
                    # exception for duplicates
                    except:
                        print(singer, song, "already exists in db. Moving to the next one")
                        break


                # move to next page checking last div on page
                if div == divs[-1]:
                    p_number += 1
                    url = f"http://muz-tv.ru/hit-online/?page={p_number}"
                    print(f'Last item on a page. Going to the next one: {url}')

        print("\nFinished")

    except Error as e:
            print(e)

    finally:
        cursor.close()
        mydb.close()


if __name__ == '__main__':
    main()