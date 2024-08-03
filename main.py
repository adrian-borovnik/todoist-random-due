import asyncio
import time
import os
from datetime import date
from random import randint
from typing import List
from dotenv import load_dotenv
from todoist_api_python.api_async import TodoistAPIAsync, Task

# TODO: Add logger

load_dotenv()

PERSONAL_PROJECT_ID: str = os.getenv('PROJECT_ID')
NEW_LABELS: List[str] = ["THIS WEEK", "NEXT WEEK", "THIS MONTH", "NEXT MONTH", "THIS YEAR", "NEXT YEAR"]


def get_days_in_month(month: int) -> int:
    if month == 2:
        return 28
    return 30 if month % 2 == 0 else 31


def get_overflow_date(_year: int, _month: int, _day: int) -> date:
    day = _day
    month = _month
    year = _year
    while day > get_days_in_month(month):
        day = day - get_days_in_month(month)
        month = month + 1
        while month > 12:
            month = month - 12
            year = year + 1
    return date(year, month, day)


async def get_no_due_tasks(api: TodoistAPIAsync) -> List[Task]:
    try:
        tasks = await api.get_tasks(project_id=PERSONAL_PROJECT_ID, due=None)
        return tasks
    except Exception as error:
        print(error)


async def get_labels(api: TodoistAPIAsync):
    try:
        labels = await api.get_labels()
        return labels
    except Exception as error:
        print(error)


async def create_new_labels(api: TodoistAPIAsync):
    try:
        existing_labels = await get_labels(api)
        new_labels = [label for label in NEW_LABELS]

        for label in existing_labels:
            if label.name in new_labels:
                new_labels.remove(label.name)

        print("# new labels:", len(new_labels))
        for new_label in new_labels:
            print(f"Adding label {new_label}")
            await api.add_label(name=new_label)

    except Exception as error:
        print(error)


async def delete_new_labels(api: TodoistAPIAsync):
    try:
        existing_labels = await get_labels(api)

        for label in existing_labels:
            if label.name in NEW_LABELS:
                print(f"Deleting label {label.name}")
                await api.delete_label(label_id=label.id)

    except Exception as error:
        print(error)


async def set_due_dates(api: TodoistAPIAsync, tasks: List[Task]):
    for task in tasks:
        periods = [label for label in task.labels if label in NEW_LABELS]
        if len(periods) == 0:
            continue

        # Chose due date based on today and period
        today = date.today()
        due_date = date.today()
        match periods[0]:
            case "THIS WEEK":
                add = randint(0, 6 - today.weekday())
                due_date = get_overflow_date(today.year, today.month, today.day + add)
            case "NEXT WEEK":
                add = 6 - today.weekday()
                add = add + randint(1, 7)
                due_date = get_overflow_date(today.year, today.month, today.day + add)
            case "THIS MONTH":
                days_in_month = get_days_in_month(today.month)
                add = randint(0, days_in_month - today.day)
                due_date = get_overflow_date(today.year, today.month, today.day + add)
                pass
            case "NEXT MONTH":
                day = randint(1, get_days_in_month(today.month + 1))
                due_date = get_overflow_date(today.year, today.month + 1, day)
                pass
            case "THIS YEAR":
                # FIXME: Correct the calculation of days left in a year
                add = randint(1, 365 - get_days_in_month(today.month) - today.day)
                due_date = get_overflow_date(today.year, today.month, today.day + add)
                pass
            case "NEXT YEAR":
                month = randint(1, 12)
                day = randint(1, get_days_in_month(month))
                due_date = get_overflow_date(today.year + 1, month, day)
                pass

        # Remove new labels
        labels = [label for label in task.labels if label not in NEW_LABELS]

        # Update task's due data and labels
        try:
            await api.update_task(task.id, labels=labels, due_date=str(due_date))
        except Exception as error:
            print(error)


async def main():
    api = TodoistAPIAsync(os.getenv('TODOIST_API_KEY'))

    # labels = await get_labels(api)
    # print(labels)

    await create_new_labels(api)
    # delete_new_labels(api)
    while True:
        tasks = await get_no_due_tasks(api)
        await set_due_dates(api, tasks)
        time.sleep(2)

if __name__ == "__main__":
    asyncio.run(main())
