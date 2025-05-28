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
from utils.formating import format_amount

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
            f"🏦 Баланс: {format_amount(balance)} ₽"
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


import os
import csv
import asyncio
from datetime import datetime
from collections import defaultdict
from tempfile import NamedTemporaryFile
from matplotlib import pyplot as plt
from aiogram.types import FSInputFile

from utils.database import fetchall
from utils.formating import format_amount
from utils.pdf_generator import create_pdf_report

async def generate_report(message, user_id: int, start_date: str, end_date: str):
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
        await message.answer("📉 За указанный период операций не найдено")
        return

    total_income = 0
    total_expense = 0
    from collections import defaultdict

    report = [f"Отчет с {start_date} по {end_date}:\n"]

    # Группируем транзакции по дате
    grouped = defaultdict(list)
    total_income = 0.0
    total_expense = 0.0

    for amount, category, type_, description, date_str in transactions:
        grouped[date_str].append((float(amount), category, type_, description))

    # Строим отчёт по дням
    for date_str in sorted(grouped.keys(), key=lambda d: datetime.strptime(d, "%d.%m.%Y")):
        report.append(f"\n {date_str}")
        for amount, category, type_, description in grouped[date_str]:
            type_label = "Доход" if type_ == "income" else "Расход"
            report.append(f"  {type_label:<6} | {category:<30} | {format_amount(amount)} ₽")

            if type_ == 'income':
                total_income += amount
            else:
                total_expense += amount

    # Итоги
    report.append("\nИтоги:")
    report.append(f"{'Общий доход':<20}: {format_amount(total_income)} ₽")
    report.append(f"{'Общий расход':<20}: {format_amount(total_expense)} ₽")
    report.append(f"{'Баланс':<20}: {format_amount(total_income - total_expense)} ₽")



    # Отправка текстового отчёта по частям
    for i in range(0, len(report), 10):
        await message.answer("\n".join(report[i:i + 10]))

    # CSV-файл
    with NamedTemporaryFile(mode='w+', newline='', delete=False, suffix=".csv", encoding='utf-8-sig') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Дата", "Тип", "Категория", "Сумма", "Описание"])
        for amount, category, type_, description, date_str in transactions:
            writer.writerow([
                date_str,
                "Доход" if type_ == "income" else "Расход",
                f"{category}",
                f"{amount:.2f}",
                description or ""
            ])
        csv_path = csvfile.name

    await message.answer_document(FSInputFile(csv_path), caption="📁 CSV-отчет")
    asyncio.create_task(delayed_file_removal(csv_path))

    image_paths = []

    # 1. Сводная диаграмма
    labels = ['Доходы', 'Расходы', 'Баланс']
    values = [total_income, total_expense, total_income - total_expense]
    colors = ['green', 'red', 'blue']
    fig, ax = plt.subplots(figsize=(8, 6))
    bars = ax.bar(labels, values, color=colors)
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2, height + 50, f'{height:.2f}', ha='center')
    ax.set_title('Сводная диаграмма')
    plt.tight_layout()
    path = f"summary_{user_id}.png"
    plt.savefig(path)
    plt.close(fig)
    image_paths.append((path, "Доходы, расходы и баланс"))

    # 2. По месяцам
    monthly_income = defaultdict(float)
    monthly_expense = defaultdict(float)
    for amount, _, type_, _, date_str in transactions:
        dt = datetime.strptime(date_str, "%d.%m.%Y")
        month = dt.strftime("%b %Y")
        if type_ == 'income':
            monthly_income[month] += amount
        else:
            monthly_expense[month] += amount

    all_months = sorted(set(monthly_income.keys()) | set(monthly_expense.keys()), key=lambda m: datetime.strptime(m, "%b %Y"))
    income_vals = [monthly_income[m] for m in all_months]
    expense_vals = [monthly_expense[m] for m in all_months]

    fig, ax = plt.subplots(figsize=(12, 6))
    x = range(len(all_months))
    ax.bar([i - 0.2 for i in x], income_vals, width=0.4, label='Доходы', color='green')
    ax.bar([i + 0.2 for i in x], expense_vals, width=0.4, label='Расходы', color='red')
    ax.set_xticks(x)
    ax.set_xticklabels(all_months, rotation=45)
    ax.set_title("Доходы и расходы по месяцам")
    ax.legend()
    plt.tight_layout()
    path = f"monthly_{user_id}.png"
    plt.savefig(path)
    plt.close(fig)
    image_paths.append((path, "По месяцам"))

    # 3. Накопительный баланс по месяцам
    running_total = 0
    cumulative = []
    for m in all_months:
        running_total += monthly_income.get(m, 0) - monthly_expense.get(m, 0)
        cumulative.append(running_total)

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(all_months, cumulative, marker='o', color='blue')
    ax.set_title("Накопительный баланс по месяцам")
    ax.axhline(0, color='gray', linestyle='--')
    plt.xticks(rotation=45)
    plt.tight_layout()
    path = f"cumulative_{user_id}.png"
    plt.savefig(path)
    plt.close(fig)
    image_paths.append((path, "Баланс по месяцам"))

    # 4. По дням
    daily_data = defaultdict(lambda: {'income': 0, 'expense': 0})
    for amount, _, type_, _, date_str in transactions:
        if type_ == 'income':
            daily_data[date_str]['income'] += amount
        else:
            daily_data[date_str]['expense'] += amount

    sorted_days = sorted(daily_data.keys(), key=lambda d: datetime.strptime(d, "%d.%m.%Y"))
    incomes = [daily_data[d]['income'] for d in sorted_days]
    expenses = [daily_data[d]['expense'] for d in sorted_days]
    balance = [i - e for i, e in zip(incomes, expenses)]

    fig, ax = plt.subplots(figsize=(14, 6))
    ax.plot(sorted_days, incomes, label='Доходы', color='green', marker='o')
    ax.plot(sorted_days, expenses, label='Расходы', color='red', marker='o')
    ax.plot(sorted_days, balance, label='Баланс (день)', color='blue', linestyle='--', marker='x')
    ax.set_title("Дневная динамика")
    ax.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()
    path = f"timeline_{user_id}.png"
    plt.savefig(path)
    plt.close(fig)
    image_paths.append((path, "Динамика по дням"))

    # 5. Накопительный по дням
    cumulative_daily = []
    running_total = 0
    net_by_day = {d: daily_data[d]['income'] - daily_data[d]['expense'] for d in sorted_days}
    for d in sorted_days:
        running_total += net_by_day[d]
        cumulative_daily.append(running_total)

    fig, ax = plt.subplots(figsize=(14, 6))
    ax.fill_between(sorted_days, cumulative_daily, step='pre', color='dodgerblue', alpha=0.4)
    ax.plot(sorted_days, cumulative_daily, marker='o', color='blue')
    ax.axhline(0, color='gray', linestyle='--')
    ax.set_title("Накопительный баланс по дням")
    plt.xticks(rotation=45)
    plt.tight_layout()
    path = f"cumulative_daily_{user_id}.png"
    plt.savefig(path)
    plt.close(fig)
    image_paths.append((path, "Баланс по дням (накопительный)"))

    # PDF
    summary_text = "\n".join(report)
    pdf_path = create_pdf_report(user_id, summary_text, image_paths)
    await message.answer_document(FSInputFile(pdf_path), caption="🧾 PDF-отчет")
    asyncio.create_task(delayed_file_removal(pdf_path))

    # Очистка изображений
    for path, _ in image_paths:
        asyncio.create_task(delayed_file_removal(path))
