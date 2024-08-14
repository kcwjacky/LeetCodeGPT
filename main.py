import openai
import requests
from googlesearch import search
from bs4 import BeautifulSoup
import gradio as gr

# OPENAI_KEY = ('sk-proj-SOMbJv_xNkR8k4rhhqWDVmQBDhlnaxWuwDbPWQs_5nUyXbNsvhJ'
#               'C0WNj0jdWa0urtEIqQSHJtcT3BlbkFJ6mUwd_3XC5G2VEXvyb-oXGMKgTUW'
#               'M2WJEjVW_UfuWaak-LvqwMEmWHP5D0yB_cHWHZT53GZVwA')
OPENAI_KEY = ('sk-proj-h0z3KO9hl7hzplzFv3TOefN-VEaIQ0d2Dvsa6RxmdorEQzc'
              '40JVRXSi-caveCYNr4zbV_8CggFT3BlbkFJr-ZjhPPHVn5qWak4BUSO'
              '_K_NYDIGZEmyEeL63RrwbUXLHyqswqWIOOFxloMAneQuB-k435u38A')
MODEL = 'gpt-4o-mini'

openai.api_key = OPENAI_KEY
requirement = ('請用搜尋結果，整理出該 LeetCode 問題的 '
               '1. 問題敘述 2. 解題思路 3. 帶有中文註解的 Python code 4. 時間與空間複雜度'
               '當有多個解法時 2 - 4 會重複出現，並且解法順序越好的解放後面，例如第一個放暴力解而最優解放在最後一個\n')


def get_url_content(url):
    page = requests.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')
    paragraphs = soup.find_all('p')
    return "\n".join([para.get_text() for para in paragraphs])


def get_reply_s(messages):
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        stream=True
    )
    for chunk in response:
        yield chunk.choices[0].delta.content or ''


def chat(user_msg):
    search_results = []  # 搜尋紀錄
    # [search] 開頭代表要搜尋網路再回答
    user_msg = "LeetCode " + user_msg
    search_result = ""
    for res in search(user_msg, advanced=True, num_results=5, lang='zh-TW'):
        search_result = f"""標題：{res.title}\n 摘要：{res.description}\n"""
        search_result += f"""內文：{get_url_content(res.url)}\n\n"""
    search_results.append(search_result)

    # 將所有搜尋結果串接當作輸入
    content = '\n'.join(search_results) + requirement
    web_res = [{"role": "user", "content": content},
               {"role": "user", "content": user_msg}]
    reply_full = ""
    for _reply in get_reply_s(web_res + [{"role": "system", "content": "使用繁體中文的小助理"}]):
        reply_full += _reply  # 記錄到目前為止收到的訊息
        yield _reply  # 傳回本次收到的片段訊息


def lc_search(problem_num: str):
    """
    Search for the solution of the given LeetCode problem number.
    :param problem_num: the number of LeetCode problem
    :return: solution text
    """
    if not problem_num.isdigit():
        print("please input the number of LeetCode problem.")
        return
    reply = ''
    for chunk in chat(problem_num):
        reply += chunk
        yield reply


if __name__ == '__main__':
    web_interface = gr.Interface(
        fn=lc_search,
        inputs=[gr.Textbox(label='The number of the LeetCode problem')],
        outputs=[gr.Markdown()],
        title="Input a LeetCode problem number to get a reference solution",
        allow_flagging="never"
    )
    web_interface.queue()
    web_interface.launch(share=True)
