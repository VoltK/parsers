import requests
import bs4
from fake_useragent import UserAgent
import csv
from datetime import datetime
import argparse


def get_arguments():
    parse = argparse.ArgumentParser()
    parse.add_argument('-j', '--job', nargs='?', const="python", type=str, action='store', help='job title: -j python developer')
    parse.add_argument('-p', '--period', nargs='?', const="7", help='job listing period: -p 1 | -p 3 | -p 7 | -p 30')

    args_list = parse.parse_args()
    return args_list


def get_page(session, url, headers):
    response = session.get(url, headers=headers)
    soup = bs4.BeautifulSoup(response.text, 'html.parser')

    return soup

def get_links(divs):
    links = []
    for div in divs:
        link = div.find('a', attrs={"data-qa": "vacancy-serp__vacancy-title"}).get("href")
        links.append(link)
    return links

def get_data(soup):
    try:
        title = soup.find("h1").text
    except:
        title = ""
    try:
        salary = soup.find("p", class_="vacancy-salary").text
    except:
        salary = ""
    try:
        company = soup.find("span", attrs={"itemprop": "name"}).text
    except:
        company = ""
    try:
        experience = soup.find("span", attrs={"data-qa": "vacancy-experience"}).text
    except:
        experience = ""

    data = {"job": title, "salary": salary, "company": company, "experience": experience}

    return data

def write_csv(data, link, job):
    with open(f"{job}_job_info.csv", "a", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow((data['job'], data['salary'], data['experience'], data['company'], link))
        print(data['job'], data['company'], " were saved to file")

def main():
    user_agent = UserAgent()
    headers = {"accept": "*/*", "user-agent": user_agent.random}

    start_time = datetime.now()

    arguments = get_arguments()
    job = arguments.job
    period = arguments.period

    base = "https://hh.ru"
    url = f"https://hh.ru/search/vacancy?area=1&clusters=true&enable_snippets=true&search_period={period}&text={job}&page=0"

    session = requests.Session()
    counter = 0

    print(f"Start parsing {job.upper()} jobs offers for last {period} days in Moscow")
    while True:
        soup = get_page(session, url, headers)

        divs = soup.find_all("div", class_="vacancy-serp-item ")
        links = get_links(divs)

        for link in links:
            details_soup = get_page(session, link, headers)
            data = get_data(details_soup)
            write_csv(data, link, job)
            counter += 1

        pager = soup.find('a', attrs={"data-qa": "pager-next"})
        if pager is None:
            break
        else:
            url = base + pager.get("href")

    total_time = datetime.now() - start_time
    print(f"Total {counter} jobs were saved in {total_time}")

if __name__ == '__main__':
    main()


