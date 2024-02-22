import datetime
import os
import json
import pickle
import requests
from bs4 import BeautifulSoup

from functions import *
from models import ElectivesCategory

LOGIN_URL = 'https://susi.uni-sofia.bg/ISSU/forms/Login.aspx'
ELECTIVES_URL = 'https://susi.uni-sofia.bg/ISSU/forms/students/ElectiveDisciplinesSubscribe.aspx'
PREFETCH_ELECTIVES_URL = 'https://susi.uni-sofia.bg/ISSU/forms/students/AllElectiveDisciplines.aspx'
HEADERS = {"sec-ch-ua": "\"Google Chrome\";v=\"117\", \"Not;A=Brand\";v=\"8\", \"Chromium\";v=\"117\"", "sec-ch-ua-mobile": "?0", "sec-ch-ua-platform": "Windows", "Upgrade-Insecure-Requests": "1", "Content-Type": "application/x-www-form-urlencoded", "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36", "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7", "host": "susi.uni-sofia.bg"}


def authenticate(session: requests.Session, progress_iter):
    progress_iter = iter(progress_iter)

    if os.path.exists('session'):
        # there is session file
        with open('session', 'rb') as f:
            # read timestamp
            try:
                data = pickle.load(f)
                # check if the session is older than 30 minutes
                if datetime.datetime.now().timestamp() - data['timestamp'] > 600:
                    # if it is, delete the file and authenticate
                    os.unlink('session')
                else:
                    # if it is not, load the session and return
                    session.cookies.update(data['session'])
                    print('Session loaded from file!')
                    for _ in progress_iter:
                        pass
                    return
            except EOFError:
                print('Session file is corrupted!')

    vstate_eventvalidation_request = session.get(LOGIN_URL)
    next(progress_iter)

    vstate_eventvalidation_page_soup = BeautifulSoup(vstate_eventvalidation_request.text, 'html.parser')
    vstate, eventvalidation = extract_vstate_eventvalidation(vstate_eventvalidation_page_soup)
    next(progress_iter)

    login_response = session.post(
        url=LOGIN_URL,
        data={
            '__EVENTARGUMENT': '',
            '__EVENTTARGET': '',
            '__EVENTVALIDATION': eventvalidation,
            '__VIEWSTATE': '',
            '__VSTATE': vstate,
            'btnSubmit': 'Влез',
            'txtUserName': os.getenv('USER'),
            'txtPassword': os.getenv('PASSWORD')
        },
        headers=HEADERS,
    )
    next(progress_iter)

    if login_response.status_code != 200:
        raise Exception('Failed to authenticate!')
    try:
        next(progress_iter)
    except StopIteration:
        pass

    # Save session to file
    file = open('session', 'wb')
    pickle.dump({'session': session.cookies, 'timestamp': datetime.datetime.now().timestamp()}, file)
    file.close()

    return login_response


def fetch_available_electives(session: requests.Session, categories: ElectivesCategory, progress_iter) -> list:
    """ Returns a list of all electives names from queries tab. """
    progress_iter = iter(progress_iter)

    vstate_eventvalidation_request = session.get(PREFETCH_ELECTIVES_URL)
    vstate, eventvalidation = extract_vstate_eventvalidation(
        BeautifulSoup(vstate_eventvalidation_request.text, 'html.parser')
    )
    next(progress_iter)

    electives_names_request = session.post(
        PREFETCH_ELECTIVES_URL,
        data={
            'SelectSemesterSessionMultiple1:cboSemester': categories.semester.value,
            'SelectSemesterSessionMultiple1:cboYearSemester': categories.year,
            'SelectSemesterSessionMultiple1:rptSemestriality:_ctl0:chkSemestriality': '1',
            'SelectSemesterSessionMultiple1:rptSemestriality:_ctl1:chkSemestriality': '2',
            'SelectSemesterSessionMultiple1:rptSemestriality:_ctl2:chkSemestriality': '3',
            'SelectSemesterSessionMultiple1:rptSemestriality:_ctl3:chkSemestriality': '4',
            'SelectSemesterSessionMultiple1:rptSemestriality:_ctl4:chkSemestriality': '5',
            '__VIEWSTATE': '',
            '__EVENTVALIDATION': eventvalidation,
            '__VSTATE': vstate,
            'cboCategories': '-1',
            'cmdSearchDisciplines': 'Търси',
            'disciplineType': categories.discipline_type.value,
            'includedInEducationPlan': categories.plan_type.value,
        },
        headers=HEADERS,
    )
    try:
        next(progress_iter)
    except StopIteration:
        pass

    return extract_electives_from_queries(electives_names_request)


def fetch_electives_ids(session: requests.Session, categories: ElectivesCategory):
    electives_request = session.get(ELECTIVES_URL)
    vstate, eventvalidation = extract_vstate_eventvalidation(BeautifulSoup(electives_request.text, 'html.parser'))
    electives_request = session.post(
        url=ELECTIVES_URL,
        data={
            'SelectSemesterSessionMultiple1:cboSemester': categories.semester.value,
            'SelectSemesterSessionMultiple1:cboYearSemester': categories.year,
            'SelectSemesterSessionMultiple1:rptSemestriality:_ctl0:chkSemestriality': '1',
            'SelectSemesterSessionMultiple1:rptSemestriality:_ctl1:chkSemestriality': '2',
            'SelectSemesterSessionMultiple1:rptSemestriality:_ctl2:chkSemestriality': '3',
            'SelectSemesterSessionMultiple1:rptSemestriality:_ctl3:chkSemestriality': '4',
            'SelectSemesterSessionMultiple1:rptSemestriality:_ctl4:chkSemestriality': '5',
            '__VIEWSTATE': '',
            '__EVENTVALIDATION': eventvalidation,
            '__VSTATE': vstate,
            'cboCategories': '-1',
            'disciplineType': categories.discipline_type.value,
            'includedInEducationPlan': categories.plan_type.value,
        },
        headers=HEADERS,
    )

    return extract_electives_ids(electives_request)


def enroll_selected_electives(session: requests.Session, categories: ElectivesCategory, wanted_electives: list, available_electives_ids: dict):
    enrollment_request = session.post(
        url=ELECTIVES_URL,
        data=prepare_electives_form_data(session, categories, wanted_electives, available_electives_ids),
        headers=HEADERS,
    )

    return enrollment_request
