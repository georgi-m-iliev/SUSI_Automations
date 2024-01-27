from enum import Enum
from dataclasses import dataclass


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
