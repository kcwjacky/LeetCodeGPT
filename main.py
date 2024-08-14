import openai
import requests
from googlesearch import search
from bs4 import BeautifulSoup
import gradio as gr


OPENAI_KEY = ('sk-proj-h0z3KO9hl7hzplzFv3TOefN-VEaIQ0d2Dvsa6RxmdorEQzc'
              '40JVRXSi-caveCYNr4zbV_8CggFT3BlbkFJr-ZjhPPHVn5qWak4BUSO'
              '_K_NYDIGZEmyEeL63RrwbUXLHyqswqWIOOFxloMAneQuB-k435u38A')
MODEL = 'gpt-4o-mini'

openai.api_key = OPENAI_KEY
requirement = ('請用搜尋結果，整理出該 LeetCode 問題的 '
               '1. 問題敘述 2. 解題思路 3. 帶有中文註解的 Python code 4. 時間與空間複雜度'
               '當有多個解法時 2 - 4 會重複出現，並且解法順序越好的解放後面，例如第一個放暴力解而最優解放在最後一個\n')
context = ''


def get_reply_s(messages):
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        stream=True
    )
    for chunk in response:
        yield chunk.choices[0].delta.content or ''


def chat(user_msg, lang):
    def get_url_content(url):
        page = requests.get(url)
        soup = BeautifulSoup(page.content, 'html.parser')
        paragraphs = soup.find_all('p')
        return "\n".join([para.get_text() for para in paragraphs])

    search_results = []
    user_msg = "LeetCode " + user_msg
    for res in search(user_msg, advanced=True, num_results=5, lang='zh-TW'):
        search_result = f"""標題：{res.title}\n 摘要：{res.description}\n"""
        search_result += f"""內文：{get_url_content(res.url)}\n\n"""
        search_results.append(search_result)

    # 將所有搜尋結果串接當作輸入
    content = '\n'.join(search_results) + requirement
    web_res = [{"role": "user", "content": content},
               {"role": "user", "content": user_msg},
               {"role": "user", "content": f'範例程式語言使用 {lang}'}]
    for _reply in get_reply_s(web_res + [{"role": "system", "content": "使用繁體中文的小助理"}]):
        yield _reply


def lc_search(problem_num: str, lang: str):
    if not problem_num.isdigit():
        print("please input the number of LeetCode problem.")
        return
    reply = ''
    for chunk in chat(problem_num, lang):
        reply += chunk
        yield reply
    global context
    context = f"Solution for LeetCode problem {problem_num}" + reply


def ask_followup(question):
    global context
    if not context:
        yield "Please first input a LeetCode problem number."
    cmd = f"Based on the previous solution: {context}, my question is: {question}"
    reply = ''
    for _reply in get_reply_s([{"role": "user", "content": cmd},
                               {"role": "system", "content": "使用繁體中文的小助理"}]):
        reply += _reply
        yield reply


if __name__ == '__main__':
    language_dropdown = gr.Dropdown(
        choices=["C++", "Python"],
        label="Select Programming Language",
        value="Python"
    )

    web_interface = gr.Interface(
        fn=lc_search,
        inputs=[gr.Textbox(label='The number of the LeetCode problem'), language_dropdown],
        outputs=[gr.Markdown()],
        title="Input a LeetCode problem number to get a reference solution",
        allow_flagging="never"
    )

    followup_interface = gr.Interface(
        fn=ask_followup,
        inputs=[gr.Textbox(label='Ask a follow-up question')],
        outputs=[gr.Markdown()],
        title="Ask a follow-up question based on the solution",
        allow_flagging="never"
    )

    # 使用 gr.TabbedInterface 來整合兩個界面
    tabbed_interface = gr.TabbedInterface(
        [web_interface, followup_interface],
        ["LeetCode Search", "Ask Follow-up"])
    tabbed_interface.queue()
    tabbed_interface.launch(share=True)
