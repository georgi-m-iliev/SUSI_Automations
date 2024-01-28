import requests
from dotenv import load_dotenv
from prompt_toolkit import PromptSession
from prompt_toolkit.shortcuts import ProgressBar

from ui import *
from models import ElectivesCategory
from actions import authenticate, fetch_available_electives, fetch_electives_ids, enroll_selected_electives
from functions import visualize_response


def setup():
    pass


def run():
    disclaimer()
    get_credentials()

    session = requests.Session()

    with ProgressBar() as pb:
        progress_iter = pb(range(3), label='Вписване...')
        authenticate(session, progress_iter)
    print('Успешно вписан!\n')

    with ProgressBar() as pb:
        progress_iter = pb(range(1), label='Извличане на избираеми...')
        electives_categories = ElectivesCategory(
            discipline_type=ElectivesCategory.ElectiveType.ELECTIVE,
            plan_type=ElectivesCategory.ElectivePlanType.INCLUDED_IN_EDUCATION_PLAN_CURRENT,
            semester=ElectivesCategory.Semester.WINTER,
            year=2023
        )
        available_electives = fetch_available_electives(session, electives_categories, progress_iter)
        print('\nИзбираемите са извлечени успешно!')
        time.sleep(2)

    # sort electives by length
    available_electives.sort(key=len)

    verified_selection = []
    selected_electives = []
    last_confirmation_before_post_result = False
    prompt_session = PromptSession()

    while not verified_selection or last_confirmation_before_post_result is False:
        # clear console
        print("\033[H\033[J")
        temp_electives = available_electives.copy()

        print_available_electives(temp_electives)
        print('Сега трябва да избереш желаните избираеми, въвеждай ги по един на ред, след което натисни Ctrl+D')

        selected_electives = select_electives(prompt_session, temp_electives)
        verified_selection = verify_selected_electives([(i, name) for i, name in enumerate(selected_electives)])
        if not verified_selection:
            continue
        selected_electives = [selected_electives[i] for i in verified_selection]

        last_confirmation_before_post_result = last_confirmation_before_post(selected_electives)
        if not last_confirmation_before_post_result:
            continue

    # clear console
    print("\033[H\033[J")
    if last_confirmation_before_post_result:
        with ProgressBar() as pb:
            progress_iter = iter(pb(range(2), label='Извличане на id на избираеми за form-data...'))
            next(progress_iter)
            electives_ids = fetch_electives_ids(session)
            try:
                next(progress_iter)
            except StopIteration:
                pass
            progress_iter = iter(pb(range(2), label='Записване за избираеми...'))
            next(progress_iter)
            enroll_selected_electives(session, selected_electives, electives_ids)
            try:
                next(progress_iter)
            except StopIteration:
                pass
            success_message(selected_electives)
            #TODO: add visualization of

    else:
        print('Край!')


def main():
    setup()
    run()


if __name__ == '__main__':
    load_dotenv()
    main()
