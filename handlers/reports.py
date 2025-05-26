from aiogram import Router, types
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from datetime import datetime, date
from states import Form
from utils.database import fetchall
from keyboards import main_menu, cancel_button
from typing import Tuple
from collections import defaultdict

import matplotlib.pyplot as plt
import csv
import os
import asyncio
from tempfile import NamedTemporaryFile
from aiogram.types import FSInputFile

router = Router()

def validate_date(date_str: str) -> Tuple[bool, datetime]:
    try:
        date = datetime.strptime(date_str, "%d.%m.%Y")
        return True, date
    except ValueError:
        return False, None

async def delayed_file_removal(path: str, delay: int = 60):
    await asyncio.sleep(delay)
    if os.path.exists(path):
        os.remove(path)

@router.message(Command("report"))
async def report_start(message: types.Message, state: FSMContext):
    await state.set_state(Form.REPORT_START_DATE)
    await message.answer(
        "\U0001F4C5 Введите начальную дату в формате ДД.ММ.ГГГГ\nПример: 01.05.2024",
        reply_markup=cancel_button()
    )

@router.message(Command("monthly"))
async def monthly_report(message: types.Message):
    today = date.today()
    start_date = today.replace(day=1).strftime("%Y-%m-%d")
    end_date = today.strftime("%Y-%m-%d")
    await generate_report(message, message.from_user.id, start_date, end_date)

@router.message(Command("compare"))
async def compare_months(message: types.Message):
    today = date.today()
    current_month_start = today.replace(day=1)
    previous_month_end = current_month_start - timedelta(days=1)
    previous_month_start = previous_month_end.replace(day=1)

    current_start = current_month_start.strftime("%Y-%m-%d")
    current_end = today.strftime("%Y-%m-%d")
    previous_start = previous_month_start.strftime("%Y-%m-%d")
    previous_end = previous_month_end.strftime("%Y-%m-%d")

    current = fetchall_summary(message.from_user.id, current_start, current_end)
    previous = fetchall_summary(message.from_user.id, previous_start, previous_end)

    if not current and not previous:
        return await message.answer("Нет данных за текущий и предыдущий месяцы.")

    def summary_text(summary, label):
        income = summary.get('income', 0)
        expense = summary.get('expense', 0)
        balance = income - expense
        return (
            f"\n📅 {label}:"
            f"💰 Доход: {income} ₽\n"
            f"📉 Расход: {expense} ₽\n"
            f"🏦 Баланс: {balance} ₽"
        )

    text = "📊 Сравнение двух месяцев:" + \
           summary_text(previous, "Предыдущий месяц") + \
           summary_text(current, "Текущий месяц")

    await message.answer(text)

from datetime import timedelta

def fetchall_summary(user_id: int, start: str, end: str) -> dict:
    transactions = fetchall('''
        SELECT t.amount, c.type
        FROM transactions t
        JOIN categories c ON t.category_id = c.id
        WHERE t.user_id = ? AND date(t.created_at) BETWEEN ? AND ?
    ''', (user_id, start, end))

    summary = defaultdict(float)
    for amount, type_ in transactions:
        summary[type_] += amount
    return summary

@router.message(Form.REPORT_START_DATE)
async def process_start_date(message: types.Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        return await message.answer("Отменено", reply_markup=main_menu())

    valid, date_obj = validate_date(message.text)
    if not valid:
        return await message.answer("\u274C Неверный формат даты! Используйте ДД.ММ.ГГГГ")

    await state.update_data(start_date=date_obj.strftime("%Y-%m-%d"))
    await state.set_state(Form.REPORT_END_DATE)
    await message.answer("\U0001F4C5 Введите конечную дату:", reply_markup=cancel_button())

@router.message(Form.REPORT_END_DATE)
async def process_end_date(message: types.Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        return await message.answer("Отменено", reply_markup=main_menu())

    valid, date_obj = validate_date(message.text)
    if not valid:
        return await message.answer("\u274C Неверный формат даты! Используйте ДД.ММ.ГГГГ")

    data = await state.get_data()
    start_date = data['start_date']
    end_date = date_obj.strftime("%Y-%m-%d")
    await generate_report(message, message.from_user.id, start_date, end_date)
    await state.clear()

async def generate_report(message: types.Message, user_id: int, start_date: str, end_date: str):
    transactions = fetchall('''
        SELECT 
            t.amount,
            c.name as category,
            c.type,
            t.description,
            strftime('%d.%m.%Y', t.created_at) as date
        FROM transactions t
        JOIN categories c ON t.category_id = c.id
        WHERE 
            t.user_id = ? AND
            date(t.created_at) BETWEEN ? AND ?
        ORDER BY t.created_at
    ''', (user_id, start_date, end_date))

    if not transactions:
        await message.answer("\U0001F4CA За указанный период операций не найдено")
        return

    total_income = 0
    total_expense = 0
    report = [f"\U0001F4CA Отчет с {start_date} по {end_date}:\n"]

    for amount, category, type_, description, date_str in transactions:
        line = (
            f"\U0001F4C5 {date_str} | "
            f"{'\U0001F4B5 Доход' if type_ == 'income' else '\U0001F4B8 Расход'} | "
            f"{category}: {amount} ₽"
        )
        if description:
            line += f"\n   \U0001F4DD {description}"
        report.append(line)

        if type_ == 'income':
            total_income += amount
        else:
            total_expense += amount

    report.append("\n\U0001F50D Итоги:")
    report.append(f"\U0001F4B0 Общий доход: {total_income} ₽")
    report.append(f"\U0001F4C9 Общий расход: {total_expense} ₽")
    report.append(f"\U0001F3E6 Баланс: {total_income - total_expense} ₽")

    chunk_size = 10
    for i in range(0, len(report), chunk_size):
        chunk = report[i:i+chunk_size]
        await message.answer("\n".join(chunk))

    # CSV
    with NamedTemporaryFile(mode='w+', newline='', delete=False, suffix=".csv") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Дата", "Тип", "Категория", "Сумма", "Описание"])
        for amount, category, type_, description, date_str in transactions:
            writer.writerow([
                date_str,
                "Доход" if type_ == "income" else "Расход",
                category,
                f"{amount:.2f}",
                description or ""
            ])
        csv_path = csvfile.name

    await message.answer_document(FSInputFile(csv_path), caption="\U0001F4C1 CSV-отчет")
    asyncio.create_task(delayed_file_removal(csv_path))

    # Диаграмма
    totals = defaultdict(float)
    for amount, category, type_, *_ in transactions:
        label = f"{category} ({'доход' if type_ == 'income' else 'расход'})"
        totals[label] += amount

    labels = list(totals.keys())
    sizes = list(totals.values())

    if sizes:
        fig, ax = plt.subplots()
        ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
        ax.axis('equal')
        graph_path = f"report_{user_id}.png"
        plt.savefig(graph_path)
        plt.close(fig)

        await message.answer_photo(FSInputFile(graph_path), caption="\U0001F4CA Диаграмма расходов/доходов")
        asyncio.create_task(delayed_file_removal(graph_path))
