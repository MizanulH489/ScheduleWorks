"""Wrapper class to maintain cookies from NU Banner API"""
import requests
from bs4 import BeautifulSoup
import re


class Nub:
    """
    Wrapper api for NU Banner.
    https://jennydaman.gitlab.io/nubanned/dark.html

    """

    def __init__(self, base_url) -> None:
        self.base_url = base_url
        self.term = ""

    def get_terms(self, maximum=25, offset=0, search_term=""):
        """
        Generate a list of semesters and their term codes that are available to be viewed.

        Args:
        offset: starting index (default 1).
        maximum: number of semesters to return.
        searchTerm: keyword to filter by.
        """
        url = (
            self.base_url
            + f"/classSearch/getTerms?offset={offset}&max={maximum}&searchTerm={search_term}"
        )
        response = requests.get(url, timeout=10)

        if response.status_code != 200:
            return [{"Error": response.status_code}]

        return response.json()

    def set_term(self, term: str) -> None:
        """
        Set the term for lookups.

        Args:
        Term is a numeric string given from get_terms().
        """
        self.term = term
        return True

    def get_subject_code(self, search_term, maximum=10, offset=1):
        """
        Generate a list of subjects and their codes using a filter.

        Args:
        term
        offset: starting index (default 1).
        maximum: number of semesters to return.
        searchTerm: keyword to filter by.
        """
        url = (
            self.base_url
            + f"/classSearch/get_subject?offset={offset}&max={maximum}&searchTerm={search_term}&term={self.term}"
        )
        response = requests.get(url, timeout=10)

        if response.status_code != 200:
            return [{"Error": response.status_code}]

        return response.json()

    def enable_search(self):
        """
        Enable search cookies with a valid code. Takes no args.

        """
        url = self.base_url + f"/term/search"
        header = {
            "Content-Type": "application/x-www-form-urlencoded;charset=UT",
        }

        body = {
            "term": self.term,
            "studyPath": "",
            "studyPathText": "",
            "startDatepicker": "",
            "endDatepicker": "",
        }
        with requests.Session() as ses:
            response = ses.post(url, timeout=10, data=body, headers=header)
            self.session = ses

        if response.status_code != 200:
            return [{"Error": response.status_code}]

        return response.json()

    def reset_search(self):
        """Resetting form."""
        url = self.base_url + "/classSearch/resetDataForm"
        self.session.post(url)

    def look_up(self, subject_code):
        """Search for a course given its subject code."""

        self.reset_search()
        url = (
            self.base_url
            + f"/searchResults/searchResults?txt_subject={subject_code}&txt_term={self.term}&startDatepicker=&endDatepicker=&pageOffset=0&pageMaxSize=5000&sortColumn=subjectDescription&sortDirection=asc"
        )
        response = self.session.get(url)

        if response.status_code != 200:
            return [{"Error": response.status_code}]

        return response.json()

    def get_course_reference(self, subject_code, course_code):
        """Return class code for accessing its details."""
        self.reset_search()
        url = (
            self.base_url
            + f"/searchResults/searchResults?txt_subject={subject_code}&txt_term={self.term}&txt_courseNumber={course_code}&startDatepicker=&endDatepicker=&pageOffset=0&pageMaxSize=5000&sortColumn=subjectDescription&sortDirection=asc"
        )
        response = self.session.get(url, timeout=10)
        if response.status_code != 200:
            return [{"Error": response.status_code}]
        elif response.json()["totalCount"] <= 0:
            return [{"Error": "Cannot find class"}]

        course_reference_number = response.json()["data"][0]["courseReferenceNumber"]
        return course_reference_number

    def get_prerequistes(self, subject_code, course_code):
        """Obtain an array with course prequeistes given a course code and id."""
        course_reference_number = self.get_course_reference(subject_code, course_code)
        url = self.base_url + "/searchResults/getSectionPrerequisites"
        body = {"term": self.term, "courseReferenceNumber": course_reference_number}
        html_response = requests.post(url, data=body)
        if html_response.status_code != 200:
            return ["Error"]
        parsed_html = BeautifulSoup(html_response.content, features="lxml")
        prereq_table = parsed_html.body.find("table")

        track = False
        course_prereq_list = []
        word = ""
        # print(str(prereq_table))
        for letter in str(prereq_table):
            if letter == "\n" and word != "":
                track = False
                course_prereq_list.append(word)
                word = ""
            if track:
                word += letter
            if letter == ":":
                track = True

        print(course_prereq_list)

        for i, course in enumerate(course_prereq_list[1::]):
            course_prereq_list[i + 1] = {
                "course": re.sub(r"[^a-zA-Z ]+", "", course).strip(),
                "code": re.findall("\d+", course)[0],
            }
        course_prereq_list.pop(0)
        print(course_prereq_list)

        known_conversion = {}
        for course_data in course_prereq_list:
            course_name = course_data["course"]
            if course_name in known_conversion.keys():
                course_data["course"] = known_conversion[course_name]
            else:
                code = self.get_subject_code(course_name)[0]["code"]
                known_conversion[course] = code
                course_data["course"] = code

        print(course_prereq_list)


def main():
    """Example usage."""
    nub = Nub("https://registration.wayne.edu/StudentRegistrationSsb/ssb")
    print(nub.get_terms())
    nub.set_term("202301")
    nub.enable_search()
    print(nub.get_subject_code("Basic Engineering")[0])
    # lookup = pre_reqs.look_up("CSC")
    # nub.pre_reqs("CSC", "2200")
    nub.get_prerequistes("CSC", "2200")


if __name__ == "__main__":
    main()
