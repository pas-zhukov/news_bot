import freeGPT
import asyncio


async def _send_prompt(prompt: str):
    response = await getattr(freeGPT, "gpt3").Completion().create(prompt)
    return response


def shorten_text(text: str, symbols_count: int = 600):
    prompt = f'''
    Перескажи нижеследующий текст, сократив до {symbols_count} символов. Текст составь на русском языке.

    {text}
    '''
    print(prompt)
    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(_send_prompt(prompt))
    return result
