from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
from lxml import etree
import time
import requests
import os
import json

tag_do_img = input('\n是否下载图片？(1-是，其他-否)：')
page_from = input('从第几页开始？(默认为第1页)：')
page_to = input('操作几页？(默认为1页)：')
has_baidu = False
it_save = False
baidu_infos = []

driver = webdriver.Chrome()


# 初始化操作内容
def init():
    global page_from, page_to

    if page_from is not None and page_from != '':
        page_from = int(page_from)
        if page_from < 1:
            page_from = 1
    else:
        page_from = 1

    if page_to is not None and page_to != '':
        page_to = int(page_to)
        if page_to < 1:
            page_to = 1
    else:
        page_to = 1

    if page_from != 1:
        next_page(page_from)


# 登录，使用你的账号与密码
def login():
    global driver

    elem = driver.find_element_by_xpath('//button[@class="empty"]')
    elem.click()
    elem_user = driver.find_element_by_xpath('//input[@class="phone-email"]')
    elem_user.send_keys('账号')
    elem_pwd = driver.find_element_by_xpath('//input[@class="pass"]')
    elem_pwd.send_keys('密码')
	
	# 验证码，已废弃
    '''elem_yan_bu = driver.find_element_by_xpath('//div[@class="fd mouh pos-r"]')
    elem_yan_bu.click()

    elem_yan = driver.find_element_by_xpath('//input[@class="checkcode fd"]')
    a = input('请输入验证码：')
    elem_yan.send_keys(a)'''
    elem = driver.find_element_by_xpath('//button[@type="submit"]')
    elem.click()


# 利用接口获取指定页码所有作品链接，选用
def get_articles(page):
    target = 'http://www.jdlingyu.mobi/wp-admin/admin-ajax.php?action=zrz_load_more_posts'
    headers = {'Accept': 'application/json, text/plain, */*',
               'Accept-Encoding': 'gzip, deflate',
               'Content-Type': 'application/x-www-form-urlencoded',
               'Referer': 'http://www.jdlingyu.mobi/tuji/',
               'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                             'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.62 Safari/537.36', }
    data = {
        'type': 'catL1514',
        'paged': page
    }
    try:
        req = requests.post(url=target, headers=headers, data=data, timeout=10)
    except Exception:
        print('Connect timeout')
    else:
        text = req.text
        if text.startswith(u'\ufeff'):
            text = text.encode('utf8')[3:].decode('utf8')
        text = json.loads(text, encoding='utf8')
        selector = etree.HTML(text['msg'].replace('\\', ''))
        urls = selector.xpath('//a[@class="link-block"]/@href')
        for url in urls:
            print(url)
        return urls


# 翻页
def next_page(page):
    elem_next = driver.find_element_by_xpath('//div[@class="jump-page fl"]/input')
    elem_next.clear()
    elem_next.send_keys(page)
    elem_next.send_keys(Keys.ENTER)
    time.sleep(1)


# 下载图片
def do_img(img_list, title):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/'
                             '537.36 (KHTML, like Gecko) Chrome/67.0.3396.62 Safari/537.36',
               'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
               'Referer': 'http://www.jdlingyu.mobi/tuji/',
               'Accept-Encoding': 'gzip, deflate',
               'Accept-Language': 'zh-CN,zh;q=0.9,zh-TW;q=0.8,en-US;q=0.7,en;q=0.6',
               }

    if '绝对领域' not in os.listdir(os.path.abspath('.')):
        os.makedirs('绝对领域')
    path = os.path.abspath('.') + '\绝对领域\\'
    if title not in os.listdir(path):
        os.makedirs(path + title)

    i = 1
    img_count = len(img_list)
    print('已找到，共%s张.' % (img_count,))
    for img in img_list:
        if 'src' in img.attrs:
            img_url = img.attrs['src']
            filename = title + '_' + str(i) + '.jpg'
            file_all = path + title + '\\' + filename
            ir = requests.get(img_url, headers=headers, stream=True)
            if ir.status_code == 304 or ir.status_code == 200:
                open(file_all, 'wb').write(ir.content)

            # urlretrieve(url=img_url, filename=title + '/' + filename)
            print('\r当前进度：' + str(round(i / img_count * 100)) + '%.', end='')
            i += 1
    print('\n下载完成.')


# 获取百度网盘链接
def get_baidu_url(title):
    global baidu_infos, it_save

    baidu_div = driver.find_element_by_xpath('//div[@class="content-hide-tips pos-r pd20b"]')
    baidu_info = baidu_div.text
    if 'baidu' not in baidu_info:
        baidu_a = driver.find_element_by_xpath('//div[@class="content-hide-tips pos-r pd20b"]/a')
        baidu_url = baidu_a.get_attribute("href")
        baidu_info = baidu_url + baidu_info
    print(baidu_info[4:])
    baidu_infos.append(title + '\n' + baidu_info[4:]+'\n')
    it_save = True


# 获取百度网盘链接之二
def get_p_url(ps, title):
    global baidu_infos, it_save

    for p in ps:
        content = p.get_text()[5:].replace(' 解压密码：jdlingyu.com', '')
        if content is not None and content != '' and content != '解压密码：jdlingyu.com':
            baidu_infos.append(title + '\n' + content + '\n')
            print(content)
            it_save = True
    if not it_save:
        print('没有百度网盘链接.')


# 保存链接到txt文件
def save_baidus(infos):
    for info in infos:
        with open('baiduyun.txt', "a", encoding='utf-8') as a:
            a.write(info)
            a.close()


# 主要流程
def do():
    global driver, baidu_infos, has_baidu, it_save

    targets = []
    # 获取【作品】单页所有作品的链接
    urls = driver.find_elements_by_xpath('//a[@class="link-block"]')
    for url in urls:
        target = url.get_attribute('href')
        targets.append(target)
    # 跳转作品页面
    number = 1
    while True:
        if number > len(targets):
            break
        driver.get(targets[number - 1])

        print('-'*70)
        # 获取标题
        title = driver.find_element_by_xpath('//h1[@class="entry-title"]')
        title = title.text[:-4].replace(' ', '').replace('/', '-')
        print(title)

        html = driver.page_source

        soup = BeautifulSoup(html, 'html.parser')
        # 获取包含图片链接及百度网盘链接的div
        div = soup.find('div', attrs={'id': 'content-innerText'})

        div = '<html><body>' + str(div) + '</body></html>'

        if '解压密码' in div:
            has_baidu = True

        soup = BeautifulSoup(div, 'html.parser')

        # 下载所有图片
        if tag_do_img == '1':
            img_list = soup.find_all('img')
            do_img(img_list, title)

        # 获取百度网盘链接（如有）
        try:
            get_baidu_url(title)
        except Exception as e:
            ps = soup.find_all('p')
            get_p_url(ps, title)
        finally:
            if has_baidu and not it_save:
                print('没有保存.')
            has_baidu = False
            it_save = False

        time.sleep(1)

        number += 1
    # 保存并返回【作品】页面
    save_baidus(baidu_infos)
    baidu_infos.clear()
    time.sleep(1)
    driver.get("http://www.jdlingyu.mobi/tuji/")


if __name__ == '__main__':
    with open('baiduyun.txt', "w", encoding='utf-8') as f:
        f.close()

    driver.get("http://www.jdlingyu.mobi/tuji/")

    login()

    time.sleep(2)

    init()
    op_count = 1
    while True:
        if op_count > page_to:
            break
        do()
        print('第' + str(page_from+op_count-1) + '页完成。')
        if op_count < page_to:
            next_page(op_count+page_from)
        op_count += 1
    driver.close()
