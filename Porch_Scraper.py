import csv
import datetime
import json
import sys
import threading
import time
import tkinter as tk
from multiprocessing import freeze_support
from tkinter import filedialog as fd
from tkinter import ttk
from urllib.parse import urlparse

import requests
import sv_ttk


def scrape_links(i, new_businesses, keywords):
    global info_text

    url = "https://pro.porch.com/api-frontend-seo/"

    payload = json.dumps({
        "requests": {
            "g0": {
                "resource": "publishCompanyService",
                "operation": "read",
                "params": {
                    "companyId": i
                }
            }
        },
        "context": {
            "lang": "en-US"
        }
    })
    headers = {
        'authority': 'pro.porch.com',
        'accept': '*/*',
        'accept-language': 'en-US,en;q=0.9,tr-TR;q=0.8,tr;q=0.7',
        'cache-control': 'no-cache',
        'content-type': 'application/json',
        'origin': 'https://pro.porch.com',
        'pragma': 'no-cache',
        'referer': 'https://pro.porch.com/',
        'sec-ch-ua': '"Chromium";v="116", "Not)A;Brand";v="24", "Google Chrome";v="116"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
        'x-requested-with': 'XMLHttpRequest'
    }

    try:
        response = requests.request("POST", url, headers=headers, data=payload)

        data = json.loads(response.text)
        print(f"response: {data}")
        business = {}
        if data != None:
            if 'id' not in data["g0"]["data"]:
                return "not found"

        business["Name"] = data["g0"]["data"]["name"]

        business["Link"] = data["g0"]["data"]["companyProfileUrl"]
        parsed_url = urlparse(business["Link"])
        path_parts = parsed_url.path.split("/")

        business["Category"] = path_parts[2].replace("-", " ")
        # if business["Category"] == 'unknown':
        #     return

        if data["g0"]["data"]["phoneNumberE164"] is not None:
            business["Phone Number"] = str(
                data["g0"]["data"]["phoneNumberE164"])

        business["ID"] = i
        business["Uuid"] = data["g0"]["data"]["uuid"]
        business["SchemaVersion"] = data["g0"]["data"]["schemaVersion"]
        business["hasAccount"] = data["g0"]["data"]["hasAccount"]
        business["AccountStatus"] = data["g0"]["data"]["accountStatus"]
        business["SeoUrl"] = data["g0"]["data"]["seoUrl"]
        business["ValidUseCases"] = str(data["g0"]["data"]["validUseCases"])
        business["SubscriptionTypes"] = str(
            data["g0"]["data"]["subscriptionTypes"])

        global keywords_filepath
        if keywords_filepath != '' and len(keywords) > 0:
            contains_keyword = False

            for keyword in keywords:
                if keyword.lower() in business["Category"].lower():
                    contains_keyword = True

            if contains_keyword:

                new_businesses.append(business)
                return "found"

            else:
                return "not in keywords"

        else:
            new_businesses.append(business)
            return "found"

    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")


def main():
    global startbot
    global info_text

    startbot.config(state="disabled", text="Started...")

    keywords = []
    if keywords_filepath != '':
        with open(keywords_filepath, 'r') as f:
            for line in f:
                cleaned_line = line.strip()

                if cleaned_line:
                    keywords.append(cleaned_line)

    new_businesses = []
    total_count = 0

    try:
        with open("last_id.txt", 'r') as f:
            last_id = int(f.read())
    except FileNotFoundError:
        info_text.config(text="Last ID txt file cannot found!")
        return

    last_found_id = last_id
    info_text.config(text=f"Found: 0")

    while True:
        result = scrape_links(last_found_id + 1, new_businesses, keywords)

        current_datetime = datetime.datetime.now()
        csv_file = f"Porch Scrape - {current_datetime.strftime('%d-%m-%Y %H_%M_%S')}.csv"

        if result == "found":
            last_found_id += 1
            last_id = last_found_id
            total_count += 1
            print(f"Total Count: {total_count}")
            info_text.config(text=f"Found: {int(total_count)}")
           
            with open(csv_file, mode="w", newline="", encoding="utf-8") as file:
                fieldnames = ["Name", "Category", "Phone Number", "Link", "ID", "AccountStatus",
                              "SubscriptionTypes", "Uuid", "SchemaVersion", "ValidUseCases", "SeoUrl", "hasAccount"]
                writer = csv.DictWriter(file, fieldnames=fieldnames)

                writer.writeheader()
                sorted_data = sorted(new_businesses, key=lambda x: x["ID"])
                for business in sorted_data:
                    writer.writerow(business)

            with open("last_id.txt", 'w') as f:
                f.write(str(last_id))
            time.sleep(0.5)
        elif result == "not in keywords":
            last_found_id += 1
            last_id = last_found_id
            time.sleep(0.5)
        else:
            if last_found_id - last_id < 100:
                last_found_id += 1
                time.sleep(0.5)
            else:
                break

    startbot.config(state="enabled")
    info_text.config(text="Completed!")


if __name__ == '__main__':
    freeze_support()

    app = tk.Tk()
    app.title(f'Porch Scraper')
    app.geometry('400x400')
    app.minsize(400, 400)
    app.maxsize(400, 400)

    ttk.Frame(app, height=30).pack()
    title = tk.Label(app, text='Porch Scraper', font=("Calibri", 24, "bold"))
    title.pack(pady=20)

    def select_file():
        global keywords_filepath

        file_path = fd.askopenfilename()
        file_path_short = file_path[file_path.rindex('/') + 1:]

        keywords_element.config(text=file_path_short)
        keywords_filepath = file_path

    keywords_filepath = ''

    keywords_info = ttk.Labelframe(app, text='Keywords (Optional)')
    keywords_info.pack(padx=60, pady=20)
    keywords_element = ttk.Button(keywords_info, text='Select file', width=40,
                                  command=lambda: select_file())
    keywords_element.pack(padx=10, pady=10, fill=tk.X)

    startbot = ttk.Button(app, text='Start Bot', style='Accent.TButton', width=15,
                          command=lambda: threading.Thread(target=main).start())
    startbot.pack(pady=10)

    info_text = ttk.Label(app, text='', justify=tk.CENTER)
    info_text.pack(pady=5)

    sv_ttk.set_theme('dark')
    app.mainloop()
