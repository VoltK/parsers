import requests
import bs4
from fake_useragent import UserAgent
from checkProxy import check

def get_page(url, headers):
    response = requests.get(url, headers=headers)
    soup = bs4.BeautifulSoup(response.text, 'html.parser')
    return soup

def write_txt(proxies):
    with open("us_proxy.txt", 'w') as f:
        f.writelines(proxies)

def get_proxies(soup):
    trs = soup.find('table', id='proxylisttable').find('tbody').find_all('tr')
    proxies = []
    for tr in trs:
        tds = tr.find_all('td')
        proxies.append(":".join(td.text for td in tds[:2]) + "\n")

    return proxies

def main():
    url = "https://us-proxy.org/"
    user_agent = UserAgent()
    headers = {"accept": "*/*", "user-agent": user_agent.random}

    soup = get_page(url, headers)
    print("Start parsing proxies")

    proxies = get_proxies(soup)

    write_txt(proxies)
    print("All proxies are saved to file")

if __name__ == '__main__':
    main()
    check()