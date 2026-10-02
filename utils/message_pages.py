"""Send long reports without truncating answers or splitting HTML entities."""
import html
import re
async def send_pages(message, text, reply_markup=None, edit=False):
    plain = html.unescape(re.sub(r'</?b>', '', text))
    chunks = [plain[i:i+3500] for i in range(0,len(plain),3500)] or ['Нет данных']
    for index, chunk in enumerate(chunks):
        keyboard = reply_markup if index == len(chunks)-1 else None
        if index == 0 and edit:
            await message.edit_text(chunk,parse_mode=None,reply_markup=keyboard)
        else:
            await message.answer(chunk,parse_mode=None,reply_markup=keyboard)
