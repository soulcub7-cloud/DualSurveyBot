"""Revision-safe questionnaire wizard. Only explicit confirmation writes a record."""
import asyncio
import html
import secrets
from datetime import datetime, timedelta, timezone
from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message
from database import get_mentor_id, get_student_by_telegram, save_survey, save_mentor_feedback
from questions import get_questions, NEW_OPEN_QUESTIONS, SECTION_TITLES, score_summary
from mentor_feedback_questions import MENTOR_FEEDBACK_QUESTIONS, MENTOR_FEEDBACK_OPEN_QUESTIONS, SCORE_SCALE
from keyboards import main_menu_builder, student_menu_builder
from lms_sync import sync_survey, sync_mentor_feedback

router = Router()
ACTIVE = 'Assessment:active'
TZ = timezone(timedelta(hours=5))
LABELS = {2:'Неудовлетворительно',3:'Удовлетворительно',4:'Хорошо',5:'Отлично'}

def make_steps(kind, key=None):
    if kind == 'survey':
        questions = get_questions(key)
        steps = [dict(q, type='score') for q in questions if q['section'] != 'suitability']
        steps += [dict(code=code, text=text, type='text') for code,text in zip(('best','improve'),NEW_OPEN_QUESTIONS)]
        steps += [dict(q, type='score') for q in questions if q['section'] == 'suitability']
    else:
        steps = [dict(q,type='score') for q in MENTOR_FEEDBACK_QUESTIONS]
        steps += [dict(code=key,text=text,type='text') for key,text in MENTOR_FEEDBACK_OPEN_QUESTIONS]
    return steps

async def begin(callback, state, kind):
    data = await state.get_data()
    if kind == 'survey' and (not get_mentor_id(callback.from_user.id) or data.get('questionnaire_key') not in ('ct_assembly','ct_agro') or not data.get('student_id') or not data.get('enterprise')):
        await callback.answer('Начните новую анкету и повторите выбор.',show_alert=True); return
    if kind == 'feedback' and (not get_student_by_telegram(callback.from_user.id) or not data.get('mentor') or not data.get('module')):
        await callback.answer('Повторите выбор наставника и модуля.',show_alert=True); return
    await callback.answer()
    await state.update_data(wizard_kind=kind, wizard_steps=make_steps(kind,data.get('questionnaire_key')), wizard_index=0, wizard_answers={}, wizard_nonce=secrets.token_hex(4), wizard_saved=False)
    await state.set_state(ACTIVE)
    await render(callback.message,state,edit=True)

def button(text, token, index, action):
    return InlineKeyboardButton(text=text,callback_data=f'aw:{token}:{index}:{action}')

async def render(message, state, edit=False, rubric=None):
    d=await state.get_data();i=d['wizard_index'];steps=d['wizard_steps'];token=d['wizard_nonce'];answers=d['wizard_answers'];kind=d['wizard_kind']
    rows=[]
    if i == len(steps):
        skipped=sum(value is None for value in answers.values())
        text=f'✅ <b>Анкета заполнена</b>\nОтветов: {len(answers)} из {len(steps)}.\nНе оценивалось: {skipped}.\n\nМожно вернуться назад и изменить ответы. Нажмите «Сохранить», чтобы отправить анкету.'
        rows.append([button('✅ Сохранить',token,i,'save')])
    else:
        step=steps[i];code=step['code'];section=SECTION_TITLES.get(step.get('section'),'Отзыв о наставнике' if kind=='feedback' else 'Открытый вопрос')
        text=f'<b>{html.escape(section)}</b> · Вопрос {i+1} из {len(steps)}\n\n<b>{html.escape(step["text"])}</b>\n\n'
        if rubric is not None and step.get('criteria'):
            if rubric == 'criteria':
                text+='Выберите оценку, чтобы прочитать её критерии.'
                rows += [[button(f'{n} — {LABELS[n]}',token,i,f'c{n}')] for n in range(2,6)]
            else:
                n=int(rubric[1:]);text+=f'<b>{n} — {LABELS[n]}</b>\n'+html.escape(step['criteria'][str(n)])
                rows += [[button('К другим критериям',token,i,'criteria')]]
            rows += [[button('← К вопросу',token,i,'question')]]
        elif step['type']=='score':
            minimum=2 if kind=='survey' else 1
            text+=('2 — неудовлетворительно\n3 — удовлетворительно\n4 — хорошо\n5 — отлично' if kind=='survey' else SCORE_SCALE)
            if step.get('section')=='suitability':text=text.replace('2 — неудовлетворительно\n3 — удовлетворительно','2 — слабо\n3 — средне')
            rows.append([button(str(n),token,i,f's{n}') for n in range(minimum,6)])
            if kind=='survey' and step.get('section') in ('hard','soft'):
                rows.append([button('Не оценивалось',token,i,'skip')])
            if step.get('criteria'):rows.append([button('📖 Критерии оценки',token,i,'criteria')])
        else:
            text+='Введите ответ текстом (до 3000 символов).'
        if code in answers and rubric is None:
            value=answers[code];label='Не оценивалось' if value is None else str(value)
            text+='\n\nСохранённый ответ: '+html.escape(label[:500])+('…' if len(label)>500 else '')
            rows.append([button('Оставить ответ →',token,i,'keep')])
    if i>0: rows.append([button('← Предыдущий вопрос',token,i,'back')])
    rows.append([button('Отменить анкету',token,i,'cancel')])
    markup=InlineKeyboardMarkup(inline_keyboard=rows)
    if edit:
        await message.edit_text(text,parse_mode='HTML',reply_markup=markup)
        msg=message
    else: msg=await message.answer(text,parse_mode='HTML',reply_markup=markup)
    await state.update_data(wizard_message_id=msg.message_id)

@router.callback_query(F.data.startswith('aw:'))
async def action(callback:CallbackQuery,state:FSMContext):
    d=await state.get_data()
    try:_,token,index,action=callback.data.split(':');index=int(index)
    except (ValueError,AttributeError):await callback.answer();return
    if await state.get_state()!=ACTIVE or token!=d.get('wizard_nonce') or index!=d.get('wizard_index') or callback.message.message_id!=d.get('wizard_message_id'):
        await callback.answer('Это предыдущий экран. Используйте кнопки текущего вопроса.');return
    await callback.answer()
    steps=d['wizard_steps'];answers=dict(d['wizard_answers'])
    if action=='cancel':
        await state.clear();await callback.message.edit_text('Анкета отменена. Ответы не отправлены.')
        await callback.message.answer('Главное меню',reply_markup=student_menu_builder() if d['wizard_kind']=='feedback' else main_menu_builder(callback.from_user.id));return
    if action=='back':
        await state.update_data(wizard_index=max(0,index-1));await render(callback.message,state,True);return
    if action=='save' and index==len(steps):
        if len(answers)!=len(steps):return
        await commit(callback,state,d);return
    if index>=len(steps):return
    step=steps[index]
    if action in ('criteria','c2','c3','c4','c5','question'):
        if action!='question' and not step.get('criteria'):return
        await render(callback.message,state,True,None if action=='question' else action);return
    if action=='keep':
        if step['code'] not in answers:return
    elif action=='skip' and d['wizard_kind']=='survey' and step.get('section') in ('hard','soft'):answers[step['code']]=None
    elif action in ('s1','s2','s3','s4','s5') and step['type']=='score':
        value=int(action[1:])
        if d['wizard_kind']=='survey' and value<2:return
        answers[step['code']]=value
    else:return
    await state.update_data(wizard_answers=answers,wizard_index=index+1)
    await render(callback.message,state,True)

@router.message(StateFilter(ACTIVE))
async def answer_text(message:Message,state:FSMContext):
    d=await state.get_data();i=d['wizard_index'];steps=d['wizard_steps']
    if i>=len(steps) or steps[i]['type']!='text':
        await message.answer('Используйте кнопки текущего вопроса.');return
    answer=(message.text or '').strip()
    if not answer or len(answer)>3000:
        await message.answer('Введите текст от 1 до 3000 символов.');return
    answers=dict(d['wizard_answers']);answers[steps[i]['code']]=answer
    await state.update_data(wizard_answers=answers,wizard_index=i+1)
    await render(message,state)

async def commit(callback,state,d):
    a=d['wizard_answers'];kind=d['wizard_kind'];date=datetime.now(TZ).strftime('%d.%m.%Y %H:%M')
    if kind=='survey':
        questions=[{k:v for k,v in s.items() if k!='type'} for s in d['wizard_steps'] if s['type']=='score']
        ratings=[a[q['code']] for q in questions];summary=score_summary(questions,ratings)
        record_id=save_survey(mentor_id=get_mentor_id(callback.from_user.id),student_id=d['student_id'],enterprise=d['enterprise'],answers=ratings,best=a['best'],improve=a['improve'],recommendation='',survey_date=date,questionnaire_key=d['questionnaire_key'],questions=questions,**summary)
        asyncio.create_task(sync_survey(record_id));avg=summary['average'];menu=main_menu_builder(callback.from_user.id)
    else:
        student=get_student_by_telegram(callback.from_user.id);ratings=[a[q['code']] for q in MENTOR_FEEDBACK_QUESTIONS];avg=round(sum(ratings)/len(ratings),2)
        record_id=save_mentor_feedback(student_id=student[0],mentor=d['mentor'],module=d['module'],submitted_at=date,ratings=ratings,questions=MENTOR_FEEDBACK_QUESTIONS,average=avg,open_answers={k:a[k] for k,_ in MENTOR_FEEDBACK_OPEN_QUESTIONS})
        asyncio.create_task(sync_mentor_feedback(record_id));menu=student_menu_builder()
    await state.clear()
    await callback.message.edit_text(f'✅ Анкета №{record_id} сохранена.\nСредний балл: {avg if avg is not None else "Не оценивалось"}.')
    await callback.message.answer('Спасибо за участие!',reply_markup=menu)
