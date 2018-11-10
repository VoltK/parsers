import bs4
import requests
import os

os.makedirs('habr_links', exist_ok=True)


def parse_title(url):
    while not url.endswith('50/'):
        page = requests.get(url)
        page.raise_for_status()

        page_html = bs4.BeautifulSoup(page.text, features="html.parser")
        page_title = page_html.select("h2 a")
        for a in page_title:
            link_text = a.text
            link = a.get('href')
            all_links = {
                "link": link,
                "content": link_text
            }

            with open(os.path.join('habr_links', 'all_links.txt'), 'a', encoding='utf-8') as file:
                for key, val in all_links.items():
                    file.write(key + ": " + val + " ")
                file.write('\n')

            try:
                if link == page_title[-1].get('href'):
                    next_link = page_html.find('a', id='next_page')
                    print("Moving to next page: https://habr.com" + next_link.get('href'))
                    url = 'https://habr.com' + next_link.get('href')
            except AttributeError:
                spans = page_html.find('div', class_='tabs').find_all('span')
                all_a = [span.parent.get('href') for span in spans]
                url = all_a[1]


parse_title("https://habr.com")