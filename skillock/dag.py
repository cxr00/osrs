from skillock import core
from cxr import dag

root = dag.Node("root")

# Populate SkillReqs and QuestReqs from files
with open("skillock\\data\\skills.txt", "r") as f:
    skills = []
    for line in f.readlines():
        skills.append(line.split(":")[0])

with open(f"skillock\\data\\quests.txt", "r") as f:
    for line in f.readlines():
        line = line.strip()
        core.QuestReq.from_string(line)
    quests = core.QuestReq.get()


def construct_dag():
    """
    Assemble the quest dependency graph
    """
    global root

    indy_nodes = {key: dag.Node(key, data=quest) for key, quest in quests.items()}
    other_nodes = {}  # For Nodes created for non-scraped quests

    for key, node in indy_nodes.items():
        if not node.data.prerequisites:
            root.add(node)
        for req in node.data.prerequisites:
            if req not in indy_nodes:
                if req not in other_nodes:
                    other_nodes[req] = dag.Node(req)
                other_nodes[req].add(node)
            else:
                indy_nodes[req].add(node)


def skill_and_quest_reqs(node, is_start=True):
    """
    Recursively gather all prerequisites from a Node and its parents
    until it reaches the root node. This is pivotal to create_quest_breakdown
    """

    def update_output(output, recursive_output):
        """
        Compare the current output with the results of the
        recursive call, updating maximum requirements in output
        """
        for skill in recursive_output[0]:
            if skill == "Combat level" or skill == "Quest points":
                if output[0][skill] < recursive_output[0][skill]:
                    output[0][skill] = recursive_output[0][skill]
            else:
                for boolean in (True, False):
                    if output[0][skill][boolean] < recursive_output[0][skill][boolean]:
                        output[0][skill][boolean] = recursive_output[0][skill][boolean]
        output[1].update(recursive_output[1])

    global skills

    output = {skill: {True: 0, False: 0} for skill in skills}, set()  # Skill and quest requirements
    output[0]["Quest points"] = 0
    output[0]["Combat level"] = 3

    # Add current quest's requirements only if it wouldn't be repetitive
    if is_start:
        for skill_req in node.data.skill_reqs:
            name = skill_req.skill_name
            if name not in output[0]:
                output[0][name] = {True: 0, False: 0}
                output[0][name][skill_req.boostable] = skill_req.level
            if name == "Quest points" or name == "Combat level":
                if skill_req.level > output[0][name]:
                    output[0][name] = skill_req.level
            elif skill_req.level > output[0][name][skill_req.boostable]:
                output[0][name][skill_req.boostable] = skill_req.level
        output[1].update(node.data.prerequisites)

    # Add parent prerequisites
    for each in node.parent:
        if each.data:
            for skill_req in each.data.skill_reqs:
                name = skill_req.skill_name
                if name not in output[0]:
                    output[0][name] = {True: 0, False: 0}
                    output[0][name][skill_req.boostable] = skill_req.level
                if name == "Quest points" or name == "Combat level":
                    if skill_req.level > output[0][name]:
                        output[0][name] = skill_req.level
                elif skill_req.level > output[0][name][skill_req.boostable]:
                    output[0][name][skill_req.boostable] = skill_req.level
            output[1].update(each.data.prerequisites)
        update_output(output, skill_and_quest_reqs(each, False))
    return output


def create_quest_breakdown(quest_name):
    """
    Traverses the dependency graph and compiles total skill and
    quest requirements in order to unlock and complete a given quest.
    The result is then written to skillock\\data\\breakdown
    """

    print(f"Analyzing {quest_name}...", end="")

    global root

    # Find node to analyze
    target_node = None
    for node in root.all_nodes():
        if node.key == quest_name:
            target_node = node
            break

    if target_node is None:
        print("Aborted")
        return

    output = skill_and_quest_reqs(target_node)

    # Create and write output to file
    to_write = [f"Quest requirements"]
    for quest in output[1]:
        to_write.append(quest)
    to_write.append('')

    to_write.append(f"Skill requirements (boosted/unboosted)")
    for skill, req in output[0].items():
        if not (skill == "Combat level" or skill == "Quest points"):
            r, z = req[True], req[False]
            if r or z:
                to_write.append(f"{skill}: {r if r else '*'}/{z if z else '*'}")
        else:
            if skill == "Combat level" and req > 3:
                to_write.append(f"{skill}: {req}")
            elif skill == "Quest points" and req > 0:
                to_write.append(f"{skill}: {req}")

    with open(f"skillock\\data\\breakdown\\{quest_name}.txt", "w+") as f:
        f.write("\n".join(to_write))

    print("Complete")


def main():
    print("Performing complete quest breakdown...")

    global root
    if not root.nodes:
        construct_dag()

    global quests
    for quest in quests:
        create_quest_breakdown(quest)

    print("Breakdown complete.")


if __name__ == "__main__":
    main()
