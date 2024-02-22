import datetime
from enum import Enum
from dataclasses import dataclass

from prompt_toolkit.validation import Validator, ValidationError



@dataclass
class ElectivesCategory:
    class ElectivePlanType(Enum):
        INCLUDED_IN_EDUCATION_PLAN_CURRENT = 'radioIncludedInEducationPlan'
        INCLUDED_IN_EDUCATION_PLAN_OTHERS = 'radioIncludedInEducationPlanRest'
        NOT_INCLUDED = 'radioNotIncludedInEducationPlan'

    class ElectiveType(Enum):
        ELECTIVE = 'radioElective'
        FACULTATIVE = 'radioFacultative'

    class Semester(Enum):
        WINTER = '1'
        SUMMER = '2'

    discipline_type: ElectiveType
    plan_type: ElectivePlanType
    semester: Semester
    year: int


class DateValidator(Validator):
    def validate(self, document):
        text = document.text

        try:
            test = datetime.datetime.strptime(text, '%Y-%m-%d')
        except ValueError:
            raise ValidationError(message='Грешен формат на датата', cursor_position=len(text))

        if test < datetime.datetime.now():
            raise ValidationError(message='Дата не може да бъде в миналото', cursor_position=len(text))


class YearValidator(Validator):
    def validate(self, document):
        text = document.text

        if not text.isdigit():
            raise ValidationError(message='Годината трябва да бъде число!', cursor_position=len(text))

        if len(text) != 4:
            raise ValidationError(message='Годината трябва да бъде четирицифрено число!', cursor_position=len(text))
