"""
This module contains the classes which organize information about quest and skill requirements
gathered from each page of the wiki.

QuestPreReq contains methods for accessing pages and collecting that information,
and a register of scraped pages to prevent repetition.

SkillReq is a simple data frame which lists all of that skills level requirements
for OSRS quests.

QuestReq contains both quest prerequisites and skill requirements for a given quest.

This module is never run by itself, instead being accessed via scrape.py.
As such, file paths are based on that script's run configuration, which uses
a working directory of the root osrs folder.
"""

import bs4
import os
import requests


class QuestPreReq:
    """
    QuestPreReq avoids usage of the global namespace by encapsulating interrelated attributes and functions
    """

    register = {}  # The not-so-global collection of quests where isolate_and_gather has been completed

    @staticmethod
    def request_only_new_wiki_page(quest_name):
        """
        Gets the HTML of an OSRS wiki page if it has not already been collected
        """
        if f"{quest_name}.html" not in os.listdir("quest_scrapes"):
            print(f"Scraping {quest_name}...")
            url = quest_name.url
            wiki_request = requests.get(url)
            with open(f"quest_scrapes\\{quest_name}.html", "w+", encoding="utf-8") as f:
                f.write(wiki_request.text)

    @staticmethod
    def isolate_and_gather(quest_name, log=False):
        """
        -Uses a SkillReq to find or scrape the correct page.
        -Collects a list of quest prerequisites from the page
        -Updates the QuestPreReq register to prevent repetition
        -Returns quest prerequisites
        """
        if quest_name in QuestPreReq.register:
            return QuestPreReq.register[quest_name]

        QuestPreReq.request_only_new_wiki_page(quest_name)
        if log:
            print(f"Isolating quest prerequisites for {quest_name}...")
        with open(f"quest_scrapes\\{quest_name}.html", "r", encoding="utf-8") as f:
            text = "".join(f.readlines())
        soup = bs4.BeautifulSoup(text, "html.parser")
        output = []

        # Isolate quest prerequisite section of page
        deets = soup.select("td.questdetails-info.qc-input.qc-active")[0]

        # Dive into the subtree where quest prerequisites would be held
        # Dream Mentor uniquely does not contain the "Completion" indicator for quests in the requirements section
        # As a result, a special check must be included
        traversal_order = ["ul", "ul"] if quest_name == "Dream Mentor" else ["ul", "li", "ul"]
        traversal_state = 0
        while traversal_order and (deets is not None):
            temp = deets.find(traversal_order.pop(0))
            traversal_state += 1

            # Sometimes quest requirements are displayed in different ways, so this logic checks some conditions:
            # Does it require only one quest? If so, is the Quest Point icon present in the string?
            # Is the list of quest prerequisites preceded by "completion of the following quests"? (Dream Mentor)
            # Are quest prerequisites listed before or after skill requirements?
            if traversal_state == 2 and len(traversal_order):
                # Sometimes only one quest is required, so it is not display as part of a sublist
                if "complet" in temp.text.lower():
                    temp2 = temp.find_all("a")
                    for a in temp2:
                        if "Quest_points" in a["href"]:
                            continue
                        else:
                            temp2 = a
                            break
                    if temp2 and temp2["title"] not in output:
                        output.append(temp2["title"])
                else:
                    # Iterate through skill requirements until quest prerequisites are found
                    while "complet" not in temp.text.lower():
                        temp = temp.find_next_sibling()
                        if not temp:
                            deets = None
                            break

                    # Act on found section
                    if temp:
                        temp2 = temp.find_all("a")
                        for a in temp2:
                            # Skip quest point icon
                            if "Quest_points" in a["href"]:
                                continue
                            else:
                                temp2 = a
                                break
                        if temp2 and temp2["title"] not in output:
                            output.append(temp2["title"])
            else:
                deets = temp

        # Only act if a subtree remains after traversal
        if deets:
            for li in deets.find_all("li", recursive=False):
                elem = li.find("a")["title"]
                if elem not in output:
                    output.append(elem)

        QuestPreReq.register.update({quest_name: output})
        return output


class SkillReq:
    """
    A SkillReq filters the data from the <li> elements found within
    each section of the OSRS Wiki Quest Skill requirements page

    It contains a register which compiles each quest's requirement for that particular skill
    """

    _register = {}

    def __init__(self, skill, data):
        self.skill_name = skill
        if data[1].endswith("*"):
            self.quest_name = data[1][:-1]
            self.boostable = True
        else:
            self.quest_name = data[1]
            self.boostable = False

        self.level = int(data[0])

        if self.skill_name not in SkillReq._register:
            SkillReq._register[self.skill_name] = []

        SkillReq._register[self.skill_name].append(self)

    def __format__(self, format_spec):
        """
        String representation containing everything needed for
        an entry in skills.txt
        """
        return f"{self.level}-{self.quest_name}{'*' if self.boostable else ''}"

    def __str__(self):
        """
        String representation containing everything needed for
        an entry in quests.txt
        """
        return f"{self.skill_name}{'*' if self.boostable else ''}-{self.level}"

    @staticmethod
    def create_entry(skill_name):
        """
        Create an entry in skills.txt for the given skill name
        """
        if skill_name not in SkillReq._register:
            raise ValueError(f"Skill {skill_name} not found.")
        output = [skill_name, []]
        for req in SkillReq._register[skill_name]:
            output[1].append(format(req))
        return ":".join([
            output[0],
            ",".join(output[1])
        ])

    @staticmethod
    def from_string(s):
        """
        Construct a set of SkillReqs from an entry in skills.txt
        """
        skill, reqs = s.split(":", 1)
        reqs = reqs.split(',')
        for req in reqs:
            data = req.split("-", 1)
            SkillReq(skill, data)
        return SkillReq.get(skill)

    @staticmethod
    def get(skill_name=None):
        if skill_name is not None:
            return SkillReq._register[skill_name]
        return SkillReq._register

    @staticmethod
    def items():
        return SkillReq._register.items()


class QuestReq:
    """
    A QuestReq contains information about all its skill and quest prerequisites

    It also contains a compiled register of QuestReqs that have been completed
    """

    _register = {}

    def __init__(self, skill_req=None, data=None):
        """
        :param skill_req: the optional SkillReq which led to the creation of the QuestReq
        :param data: Existing data from quests.txt, collected using QuestReq.from_string
        """
        if data is not None:
            self.name = data[0]
            self.skill_reqs = data[1]
            self.prerequisites = data[2]
        else:
            self.name = skill_req.quest_name
            self.skill_reqs = [skill_req] if skill_req is not None else []
            self.prerequisites = QuestPreReq.isolate_and_gather(self.name)
        QuestReq._register[self.name] = self

    def __format__(self, format_spec):
        """
        Basic summary format for QuestReqs.

        This is independent of the DAG, so it only contains
        requirements specific to the QuestReq, and not its prerequisites.
        """
        output = [f"***{self.name}***", "Quest requirements:"]
        if not self.prerequisites:
            output.append("\tNone")
        else:
            for each in self.prerequisites:
                output.append(f"\t{each}")

        output.append("")
        output.append("Skill requirements:")
        if not self.skill_reqs:
            output.append("\tNone")
        else:
            for each in self.skill_reqs:
                output.append(f"\t{each.skill_name} - {each.level}{' (boostable)' if each.boostable else ''}")
        return "".join(["\n".join(output), "\n"])

    def __str__(self):
        """
        Create a complete entry for the QuestReq for quests.txt
        """
        output = [self.name, [], []]
        for prereq in self.prerequisites:
            output[1].append(prereq)
        output[1] = ",".join(output[1])
        for skill in self.skill_reqs:
            output[2].append(str(skill))
        output[2] = ",".join(output[2])
        return "".join([":".join(output), "\n"])

    @staticmethod
    def create_or_update_questreq(skill_req):
        """
        Adds a SkillReq to an existing QuestReq object, or creates a new QuestReq for it
        """
        if skill_req.quest_name in QuestReq._register:
            QuestReq._register[skill_req.quest_name].skill_reqs.append(skill_req)
        else:
            QuestReq(skill_req)

    @staticmethod
    def get(quest_name=None):
        if quest_name is not None:
            return QuestReq._register[quest_name]
        return QuestReq._register

    @staticmethod
    def from_string(s):
        """
        Construct a QuestReq from an entry in quests.txt
        """
        spl = s.split(":", 2)
        quest_name = spl[0]
        prerequisites = []
        for quest_prereq in spl[1].split(","):
            if quest_prereq:
                prerequisites.append(quest_prereq)
        quest_skill_reqs = []
        for skill_reqs in spl[2].split(","):
            skill_spl = skill_reqs.split("-")
            skill_name = skill_spl[0]
            boostable = False
            if skill_name[-1] == "*":
                skill_name = skill_name[:-1]
                boostable = True
            level = skill_spl[1]
            quest_skill_reqs.append(SkillReq(skill_name, (level, f"{quest_name}{'*' if boostable else ''}")))
        return QuestReq(data=[quest_name, quest_skill_reqs, prerequisites])

    @staticmethod
    def items():
        return QuestReq._register.items()
