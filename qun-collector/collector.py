import os
import random
from lxml import etree
import requests as req
from multiprocessing import Pool

def generate_html():
    with open("output.txt", "r", encoding="utf-8") as file:
        data = file.readlines()

    html_content = "<html><head><title>QQ Group Messages</title></head><body>"

    for item in data:
        item_data = eval(item)
        qq_name = item_data["qq_name"]
        content = item_data["content"]

        html_content += f"<p><b>{qq_name}:</b>"

        for msg in content:
            if msg.startswith("http"):
                img_name = os.path.basename(msg)
                html_content += f'<br><img src="img/{img_name}" alt="{img_name}">'
            else:
                html_content += f"<br>{msg}"

        html_content += "</p>"

    html_content += "</body></html>"

    with open("messages.html", "w", encoding="utf-8") as html_file:
        html_file.write(html_content)

    print("HTML generate finished.")

def download_image(url):
    try:
        filename = url.split('/')[-1]
        img_data = req.get(url, timeout=10).content
        with open(os.path.join('img', filename), 'wb') as f:
            f.write(img_data)
    except Exception as e:
        print(f"Error downloading {url}: {e}")

def download_images_multiprocess(img_urls, num_processes=4):
    if not os.path.exists('img'):
        os.makedirs('img')
    
    with Pool(num_processes) as pool:
        for _ in pool.imap_unordered(download_image, img_urls):
            pass

def random_len(length):
    return random.randrange(int('1' + '0' * (length - 1)), int('9' * length))

def generate_meta_data(p_skey, skey, qq_account, group_id) -> list:
    url = f'https://qun.qq.com/essence/indexPc?gc={group_id}&seq={random_len(8)}&random={random_len(10)}'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) QQ/9.6.5.28778 '
                      'Chrome/43.0.2357.134 Safari/537.36 QBCore/3.43.1298.400 QQBrowser/9.0.2524.400',
        'Host': 'qun.qq.com',
        'Cookie': f'p_skey={p_skey}; p_uin=o{qq_account}; uin=o{qq_account}; skey={skey}'
    }

    response = req.get(url, headers=headers)
    response.encoding = 'UTF-8'
    data = etree.HTML(response.text)
    totalData = []
    download_list = []

    for i in range(1, len(data.xpath('//*[@id="app"]/div[2]/*'))):
        essence = {"qq_account": '', "qq_name": '', "send_time": '', "content": []}
        current_pos = f'//*[@id="app"]/div[2]/div[{i}]'
        essence["qq_account"] = data.xpath(current_pos + '/div[1]/@style')[0][10:-2].split('/')[5]
        essence["qq_name"] = data.xpath(current_pos + '/div[2]')[0].text.strip()
        essence["send_time"] = data.xpath(current_pos + '/div[3]')[0].text.strip()

        content_node_class = data.xpath(current_pos + '/div[last()-1]/@class')
        if len(content_node_class) > 0 and content_node_class[0] == 'short':
            for j in data.xpath(current_pos + '/div[last()-1]/*'):
                if j.tag == 'span':
                    content = j.text
                    essence["content"].append(content)
                elif j.tag == 'img':
                    img_url = j.attrib.get('src')[:-10]
                    essence["content"].append(img_url)
                    download_list.append(img_url)
        else:
            inside_node_class = data.xpath(current_pos + '/div[last()-1]/div/@class')
            if inside_node_class:
                if inside_node_class[0] == 'img_wrap':
                    img_url = data.xpath(current_pos + '/div[last()-1]/div/img/@src')[0]
                    filename = data.xpath(current_pos + '/div[last()-1]/div/div[last()]')[0].text.strip()
                    essence["content"].append(img_url)
                    download_list.append(img_url)
                    essence["content"].append(filename)
                elif inside_node_class[0] == 'doc_wrap':
                    title = data.xpath(current_pos + '/div[last()-1]/div/div[1]')[0].text.strip()
                    img_url = data.xpath(current_pos + '/div[last()-1]/div/i/@style')[0][21:].split(')')[0]
                    source = data.xpath(current_pos + '/div[last()-1]/div/div[2]')[0].text.strip()
                    essence["content"].append(title)
                    essence["content"].append(img_url)
                    download_list.append(img_url)
                    essence["content"].append(source)
                else:
                    print(f"error: inside_node_class but class: {inside_node_class[0]}")
            else:
                img_url = data.xpath(current_pos + '/div[last()-1]/div/img/@src')[0][:-10]
                essence["content"].append(img_url)
                download_list.append(img_url)

        totalData.append(essence)

    with open("output.txt", "w", encoding="utf-8") as file:
        for item in totalData:
            file.write(repr(item))
            file.write('\n')
    
def check_args(**kwargs):
    for key, value in kwargs.items():
        if not value:
            raise ValueError(f"The argument '{key}' is empty")

if __name__ == "__main__":
    
    params = {
        "p_skey": "",  # You can obtain this parameter by capturing network packets.
        "skey": "",
        "qq_account": "",
        "group_id": ""
    }
    
    try:
        check_args(**params)
    except ValueError as e:
        raise
    
    download_list = generate_meta_data(**params)
    download_images_multiprocess(download_list)
    generate_html()
