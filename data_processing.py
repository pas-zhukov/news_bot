import os
import asyncio
import openai


def shorten_text(api_token:str, text: str, symbols_count: int = 600):
    prompt = f'''
    Перескажи нижеследующий текст, сократив до {symbols_count} символов.

    {text}
    '''
    openai.api_key = api_token
    completion = openai.ChatCompletion.create(model="gpt-3.5-turbo-16k",
                                              messages=[{"role": "assistant", "content": prompt}])
    return completion.choices[0].message.content
