import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import csv

def get_data(response):
    soup = BeautifulSoup(response.text, "lxml")

    ip = soup.find("div", {"class": "column"}).find("div", {"class": "heading"}).find("strong", {"class": "your-ip"}).text
    ua = soup.find("span", {"class": "cont browser-ua-headers"}).text
    anon = soup.find("div", id="anonym_level").find("a").text
    data = {"ip": ip, "user-agent": ua, "anon": anon}

    return data

def save_csv(data):
    with open("valid_proxy.csv", "a") as f:
        writer = csv.writer(f)
        writer.writerow((data['ip'], data['user-agent'], data['anon']))


def check():
    url = "https://whoer.net/"
    user_agent = UserAgent()
    with open("us_proxy.txt", "r") as proxies:
        for proxy in proxies.readlines():
            proxy = proxy.strip()
            addr = {'http': "http://" + proxy, 'https': "https://" + proxy}

            try:
                response = requests.get(url, headers={"User-Agent": user_agent.random}, proxies=addr)
            except:
                print(f"Dead proxy: ({proxy}). Failed to connect.")
                continue

            if response.status_code == 200:
                save_csv(get_data(response))
                print(f"{proxy} is valid and saved to valid_proxy.csv")
            else:
                print(f"Returned error code. Not valid proxy: {proxy}")

    print("Finished.")

