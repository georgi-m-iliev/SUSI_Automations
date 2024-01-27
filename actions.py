import os
import json
import requests
from bs4 import BeautifulSoup

from functions import *
from models import ElectivesCategory


def authenticate(session: requests.Session):
    vstate_eventvalidation_request = session.get(os.getenv('LOGIN_URL'))
    vstate_eventvalidation_page_soup = BeautifulSoup(vstate_eventvalidation_request.text, 'html.parser')
    vstate, eventvalidation = extract_vstate_eventvalidation(vstate_eventvalidation_page_soup)

    login_response = session.post(
        url=os.getenv('LOGIN_URL'),
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
        headers=json.loads(os.getenv('HEADERS')),
    )

    if login_response.status_code != 200:
        raise Exception('Failed to authenticate!')


def fetch_available_electives(session: requests.Session, categories: ElectivesCategory) -> list:
    """ Returns a list of all electives names from queries tab. """
    vstate_eventvalidation_request = session.get(os.getenv('PREFETCH_ELECTIVES_URL'))
    vstate, eventvalidation = extract_vstate_eventvalidation(
        BeautifulSoup(vstate_eventvalidation_request.text, 'html.parser')
    )

    electives_names_request = session.post(
        os.getenv('PREFETCH_ELECTIVES_URL'),
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
        headers=json.loads(os.getenv('HEADERS')),
    )

    return extract_electives_from_queries(electives_names_request)


def fetch_electives_ids(session: requests.Session):
    electives_request = session.get(os.getenv('ELECTIVES_URL'))

    return extract_electives_ids(electives_request)


def enroll_selected_electives(session: requests.Session, wanted_electives: list, available_electives: dict):
    enrollment_request = session.post(
        url=os.getenv('ELECTIVES_URL'),
        data=prepare_electives_form_data(session, wanted_electives, available_electives),
        headers=json.loads(os.getenv('HEADERS')),
    )

    return enrollment_request