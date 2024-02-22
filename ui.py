import datetime
import os
import time

from prettytable import PrettyTable
from prompt_toolkit import PromptSession, prompt
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.shortcuts import message_dialog, input_dialog, checkboxlist_dialog, ProgressBar, yes_no_dialog, radiolist_dialog
from prompt_toolkit.shortcuts.progress_bar import formatters


from models import ElectivesCategory, DateValidator, YearValidator
from functions import save_to_env


def disclaimer():
    message_dialog(
        title='Внимание!',
        text='Това приложение е предоставено без никаква гаранция!\n'
             'Ако нещо се обърка жестоко и се прецаката, това не е мой проблем.\n'
             'Предупредени сте! Продължавате поемайки отговорността.\n'
              'Ако продължиш, значи си съгласен...',
        ok_text='Давай!'
    ).run()


def get_credentials():
    username = None
    password = None

    while username is None or password is None:
        username = input_dialog(
            title='Какво е потребителското ти име в СУСИ?',
            text='СУСИ потребител:',
            default=os.getenv('USER', ''),
            ok_text='Готово',
            cancel_text='Изход'
        ).run()

        if username is None:
            exit(0)

        password = input_dialog(
            title='Каква е паролата ти?',
            text='СУСИ парола:',
            password=True,
            default=os.getenv('PASSWORD', ''),
            ok_text='Готово',
            cancel_text='Назад'
        ).run()

    os.environ["USERNAME"] = username
    os.environ["PASSWORD"] = password
    save_to_env('USERNAME', username)
    save_to_env('PASSWORD', password)


def print_available_electives(electives: list):
    table = PrettyTable()
    table.title = 'Налични избираеми предмети'
    table.add_column("", electives)
    print(table)
    print('\n')


def select_electives(prompt_session: PromptSession, available_electives: list):
    selected_electives = []
    electives_completer = WordCompleter(available_electives, ignore_case=True, sentence=True)

    while True:
        try:
            elective = prompt_session.prompt(
                message='> ',
                bottom_toolbar=HTML(
                    f'Брой въведени избираеми: <b><style bg="ansired">{len(selected_electives)}</style></b>'
                ),
                completer=electives_completer
            )
            if elective not in available_electives:
                print('Тази избираема не е налична или вече е избрана, опитай пак!')
                continue
            selected_electives.append(elective)
            available_electives.remove(elective)
        except EOFError:
            if not selected_electives:
                print('Не си избрал нито една избираема, опитай пак! Ако искаш да излезеш натисни Ctrl+C')
                continue
            break
        except KeyboardInterrupt:
            print('Чао!')
            exit(0)

    return selected_electives


def verify_selected_electives(selected_electives: list):
    results_array = checkboxlist_dialog(
        title="Избрани избираеми дисциплини",
        text="Провери дали всички желани избираеми са тук, ако искаш да премахнеш някоя използвай тикчето ?",
        values=selected_electives,
        ok_text='Всичко е 6',
        cancel_text='Назад',
        default_values=[i for i in range(len(selected_electives))]
    ).run()

    return results_array


def last_confirmation_before_post(selected_electives: list):
    return yes_no_dialog(
        title='Потвърди избора си',
        text='Ще бъдете записани за следните избираеми:\n' + '\n * ' + '\n * '.join(selected_electives),
        yes_text='Да',
        no_text='Не'
    ).run()


def success_message(selected_electives: list):
    return yes_no_dialog(
        title='Успех!',
        text='Успешно записах следните избираеми:\n' + '\n * ' + '\n * '.join(selected_electives),
        yes_text='Покажи ми резултата!',
        no_text='Край'
    ).run()



def get_campaign_start_date():
    date_str = input_dialog(
        title='Кога започва кампанията?',
        text='Въведете дата във формат YYYY-MM-DD:',
        ok_text='Готово',
        cancel_text='Изход',
        validator=DateValidator()
    ).run()

    if date_str is None:
        exit(0)

    save_to_env('CAMPAIGN_START_DATE', date_str)

    return datetime.datetime.strptime(date_str, '%Y-%m-%d')


def select_electives_categories():
    plan_type = None
    semester = None
    year = None
    date = datetime.datetime.now()

    while not plan_type or not semester or not year:
        plan_type = radiolist_dialog(
            title='Избери категория на избираемите дисциплини',
            text='Избери категория на избираемите дисциплини,\nкато имаш предвид в коя категория спадат желаните от теб избираеми дисциплини.',
            values=[
                (ElectivesCategory.ElectivePlanType.INCLUDED_IN_EDUCATION_PLAN_CURRENT, 'Само тези към моя учебен план - текущ семестър'),
                (ElectivesCategory.ElectivePlanType.INCLUDED_IN_EDUCATION_PLAN_OTHERS, 'Само тези към моя учебен план - останали'),
                (ElectivesCategory.ElectivePlanType.NOT_INCLUDED, 'Само тези извън моя учебен план')
            ],
            ok_text='Давай',
            cancel_text='Изход'
        ).run()

        if plan_type is None:
            exit(0)

        semester = radiolist_dialog(
            title='Избери семестър',
            text='Избери семестър, в който ще се провежда избираемата дисциплина.',
            values=[
                (ElectivesCategory.Semester.WINTER, 'Зимен'),
                (ElectivesCategory.Semester.SUMMER, 'Летен')
            ],
            default=ElectivesCategory.Semester.WINTER if date.month > 9 else ElectivesCategory.Semester.SUMMER,
            ok_text='Давай',
            cancel_text='Назад'
        ).run()

        if semester is None:
            exit(0)

        year = input_dialog(
            title='Избери година',
            text='Избери година, в която ще се провежда избираемата дисциплина.',
            default=str(date.year if date.month > 9 else date.year - 1),
            ok_text='Готово',
            cancel_text='Назад',
            validator=YearValidator()
        ).run()

        if year is None:
            continue

    return ElectivesCategory(
        discipline_type=ElectivesCategory.ElectiveType.ELECTIVE,
        plan_type=plan_type,
        semester=semester,
        year=year
    )


def countdown_to_campaign(campaign_start):
    # Calculate the total seconds to the campaign start
    now = datetime.datetime.now()
    total_seconds = int((campaign_start - now).total_seconds())

    if total_seconds > 0:
        with ProgressBar(
            title='Отброяване до начало на кампанията',
            formatters=[
                formatters.Label(),
                formatters.Text(' '),
                formatters.Bar(sym_a='#', sym_b='#', sym_c='.'),
                formatters.Text(' ')
            ]
        ) as pb:
            for i in pb(range(total_seconds)):
                pb.counters[0].label = f'Остават {datetime.timedelta(seconds=total_seconds - i)} до начало на кампанията'
                time.sleep(1)  # Wait for 1 second
        # clear console
        print("\033[H\033[J")
    else:
        print('Кампанията вече е започнала!')