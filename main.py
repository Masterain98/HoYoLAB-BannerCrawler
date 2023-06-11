import idlelib.debugger_r
import time
import json
from bs4 import BeautifulSoup
import re
import unidecode
import requests


def crawler():
    wish_ann = []
    count = 1
    wish_pool_count = 0
    uid_list = ["1015537", "1015611", "1015613"]
    for uid in uid_list:
        trigger = True
        offset_value = 0
        while trigger:
            url = "https://bbs-api-os.hoyolab.com/community/post/wapi/userPost?size=50&uid=%s&offset=%s" % \
                  (uid, offset_value)
            this_post_list = json.loads(requests.get(url, headers={
                "X-Rpc-Language": "en-us",
                "Accept-Language": "en-US;q=0.9;en;q=0.8"
            }).content.decode("utf-8"))["data"]["list"]
            last_post_id = -1
            for post in this_post_list:
                #if "活动祈愿中获得更多" in str(post):
                if "Boosted Drop Rate for" in str(post):
                    wish_ann.append(post)
                    wish_pool_count += 1
                    print(post)
                last_post_id = int(post["post"]["post_id"])

            if last_post_id == 0 or len(this_post_list) == 0:
                trigger = False
            else:
                offset_value = last_post_id
                print("last_post_id is {}, offset value set to {}, length of post is {}, current step is {}, "
                      "current number of pool is {}".format
                      (last_post_id, offset_value, len(this_post_list), count, wish_pool_count))
            count += 1

        print("total count: {}".format(count))
        with open("wish.json", "w+", encoding="utf-8") as file:
            json.dump(wish_ann, file, indent=2, ensure_ascii=False)


def parser(post_id: str):
    print("parsing post id：{}".format(post_id))
    url = "https://bbs-api-os.hoyolab.com/community/post/wapi/getPostFull?post_id={}&read=1".format(post_id)
    result = json.loads(requests.get(url, headers={
        "X-Rpc-Language": "zh-cn",
        "Accept-Language": "zh-CN;q=0.9;zh;q=0.8"
    }).content.decode("utf-8"))["data"]["post"]["post"]["content"]

    # Modern design; Multiple pools in one article
    soup = BeautifulSoup(result, 'html.parser')
    pool_list = []

    # print(soup.prettify())
    h4_list = soup.find_all('h4')
    if len(h4_list) == 0:
        h4_list = soup.find_all('h2')
        if len(h4_list) == 0:
            h4_list = soup.find_all(lambda tag: tag.name == "p" and "组建" in tag.text)
            if "「" not in h4_list[0]:
                h4_list = soup.find_all(lambda tag: tag.name == "p" and "概率UP" in tag.text)
    for h4_title in h4_list:
        if len(h4_title.text) < 3:
            break
        this_pool = {}
        try:
            title_name = re.search(r"「.+」(活动)?祈愿", h4_title.text)[0].replace("「", "").replace("」祈愿", "") \
                .replace("」活动", "")
        except TypeError:
            title_name = re.match(r"「.+」(活动)?祈愿", h4_title.text)[0].replace("「", "").replace("」祈愿", "") \
                .replace("」活动", "")
        this_pool["title"] = title_name

        this_slice = h4_title
        while True:
            this_slice = this_slice.next_sibling
            if this_slice is None:
                break
            if "<4" in str(this_slice):
                break
            if "~" in this_slice.text:
                print("Find pool time")
                this_time = re.finditer(r"(\d\.\d版本更新后|\d{4}\/\d{1,2}\/\d{1,2}(\s){1,2}\d{2}:\d{2}(:\d{2})?)(\s)?~(\s)?"
                                        r"(\d{4}\/\d{1,2}\/\d{1,2}(\s){1,2}\d{2}:\d{2}(:\d{2})?)", this_slice.text)
                this_pool["time"] = unidecode.unidecode(''.join(i.group(0) for i in this_time).replace("~", " ~ ")
                                                        .replace("  ~  ", " ~ "))\
                    .replace("Ban Ben Geng Xin Hou ", "版本更新后")
            if title_name == "神铸赋形":
                # 武器池单池两个限定UP
                if "活动期间" in this_slice.text and ("五星武器" in this_slice.text or "5星武器" in this_slice.text):
                    print("Find 5 star character")
                    this_up_5_character = re.finditer(r"(限定)?(5|五)星武器「[^祈愿]{5,}」", this_slice.text)
                    this_up_5_character = ''.join(i.group(0) for i in this_up_5_character).split("」「")
                    this_pool["5-star"] = [
                        c.replace("「", "").replace("」", "").replace("5星武器", "").replace("五星武器", "")
                        .replace("限定", "")
                        for c in this_up_5_character]
                    print(this_pool["5-star"])
                if "活动期间" in this_slice.text and ("四星武器" in this_slice.text or "4星武器" in this_slice.text):
                    print("Find 4 star character")
                    this_up_4_character = re.finditer(r"(限定)?(4|四)星武器「[^祈愿]{5,}」「[^祈愿]{5,}」", this_slice.text)
                    this_up_4_character = ''.join(i.group(0) for i in this_up_4_character).split("」「")
                    this_pool["4-star"] = [
                        c.replace("「", "").replace("」", "").replace("4星武器", "").replace("四星武器", "")
                        .replace("限定", "")
                        for c in this_up_4_character]
                    print(this_pool["4-star"])
            else:
                # 角色池
                if "活动期间" in this_slice.text and ("五星角色" in this_slice.text or "5星角色" in this_slice.text):
                    print("Find 5 star character")
                    this_up_5_character = re.finditer(r"(限定)?(5|五)星角色「[^祈愿]{5,}」", this_slice.text)
                    this_pool["5-star"] = ''.join(i.group(0) for i in this_up_5_character).replace("限定", "") \
                        .replace("5星角色「", "").replace("」", "").replace("五星角色", "")
                if "活动期间" in this_slice.text and ("四星角色" in this_slice.text or "4星角色" in this_slice.text):
                    print("Find 4 star character")
                    this_up_4_character = re.finditer(r"(限定)?(4|四)星角色「[^祈愿]{5,}」", this_slice.text)
                    this_up_4_character = ''.join(i.group(0) for i in this_up_4_character).split("」「")
                    this_pool["4-star"] = [
                        c.replace("「", "").replace("」", "").replace("4星角色", "").replace("四星角色", "")
                        for c in this_up_4_character]
                    print(this_pool["4-star"])
        pool_list.append(this_pool)
    print(pool_list)
    return pool_list


def clean():
    new_list = []
    with open("wish.json", encoding="utf-8") as f:
        data = json.load(f)
    for pool in data:
        #parser_result = parser(pool["post"]["post_id"])
        try:
            cleaned_pool = {
                "post_id": pool["post"]["post_id"],
                "created_at": pool["post"]["created_at"],
                "subject": pool["post"]["subject"],
                "content": pool["post"]["content"],
                "is_multi_language": pool["post"]["is_multi_language"],
                "image_list": [image["url"] for image in pool["image_list"]],
                #"data": parser_result
            }
            new_list.append(cleaned_pool)
        except KeyError as e:
            print(e)
            print(pool)
    with open("wish_parser.json", "w+", encoding="utf-8") as file:
        json.dump(new_list, file, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    crawler()
    clean()
