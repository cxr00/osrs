
"""
This module collects data from the OSRS wiki and uses it to compile quest requirements
for any quest which has at least one skill requirement.
"""

import bs4
from skillock import core

# alias classes being used from core.py
SkillReq = core.SkillReq
QuestReq = core.QuestReq


def scrape_skill_and_quest_requirements(show=False):
    """
    Gather the requirements for each quest, as well as lists of quest requirements for each skill
    """
    with open("quest_scrapes/!quest_skills.html", "r", encoding="utf-8") as f:
        s = "".join(f.readlines())
    soup = bs4.BeautifulSoup(s, "html.parser")

    # Iterate over all but the last mw-header, which is not a skill requirement section
    for mw_header in soup.find_all("h2", {"class": "mw-header"})[:-1]:
        skill = mw_header.find("span", {"class": "mw-headline"}).find("a")

        # Ignore mw-headline without link element
        if skill:
            skill = skill["title"]

            # Edge case because Combat level section is structured differently
            if skill == "Combat level":
                to_scrape = mw_header.find_next_sibling()
            else:
                to_scrape = mw_header.find_next("div")
                to_scrape = to_scrape.find("ul")

            # Use list elements to build SkillReqs and QuestReqs
            for li in to_scrape.find_all("li"):
                skillreq_scrape = li.text.split(" - ", 1)
                skill_req = SkillReq(skill, skillreq_scrape)
                QuestReq.create_or_update_questreq(skill_req)

    print()  # Stray print to separate isolation logs from quests w/o prerequisites

    # Test display
    if show:
        for skill, reqs in SkillReq.items():
            print(f"***{skill}***")
            for skillreq in reqs:
                print(f"\t{skillreq}")
            print()


def compile_and_save_quest_requirements():
    """
    Perform scrape and save the results to the relevant files
    """

    # Ensure that this is something you want to commit to
    # This lets you skip this step without needing to
    # comment out the function call in the if __name__ block
    user_confirmation = input("Press enter to continue, or type anything to abort.")
    if user_confirmation:
        return

    print("Compiling SkillReqs and QuestReqs...")
    scrape_skill_and_quest_requirements()
    print("Compilation complete")

    print(format(QuestReq.get("Jungle Potion")))

    with open(f"skillock\\data\\skills.txt", "w+") as f:
        for skill_name in SkillReq.get():
            f.write(f"{SkillReq.create_entry(skill_name)}\n")
            print(f"Wrote {skill_name}")

    with open(f"skillock\\data\\quests.txt", "w+") as f:
        for quest, req_obj in QuestReq.items():
            f.write(str(req_obj))
            print(f"Saved {quest}")

    print("\nSave complete")


def test_loading():
    """
    Check the integrity of the data produced by the previous function
    """
    with open(f"skillock\\data\\quests.txt", "r") as f:
        for line in f.readlines():
            line = line.strip()
            print(format(QuestReq.from_string(line)))


if __name__ == "__main__":
    compile_and_save_quest_requirements()
    test_loading()
