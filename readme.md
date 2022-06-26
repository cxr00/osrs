# OSRS

Welcome! This library is a small but growing collection of utilities for analyzing content in [Old School RuneScape](https://oldschool.runescape.com). Its primary method of data collection involves scraping pages of the [OSRS Wiki](https://oldschool.runescape.wiki/) and compiling information into appropriate data structures.

One of the packages this library contains is called `cxr`. `cxr` is the name given to my private library, which includes modules like other custom data structures, game dev components, and math modules. I've only included edited versions of the modules which this library actually uses. No `pip` for this sort of thing yet, if you clone the repo you will have everything you need to run this code for yourself.

## Skillock

The concept of a skillocked IM/UIM is simple: You are limited to skills and activities which only train a particular skill (or small set of skills), then you can use the resources gathered from that training to increase your other skills.

The typical goal is to complete every quest which has a requirement in that skill. Because late-game quests often have high requirements in multiple skills, some exceptions will need to be made for each type of skillock. For example, the seven unboostable skills in *Song of the Elves* are inherently connected. This may limit variance in the concept, so you might choose to exclude SotE as a completion goal.

As this package develops, I'll get a better idea of how to structure these types of accounts. I'll write a short document explaining the process of designing and planning such an account, pitfalls, and common exceptions.

`skillock` has several modules for scraping, compiling, and analyzing skill requirements and quest prerequisites for quests found on [this page](https://oldschool.runescape.wiki/w/Quests/Skill_requirements).It will soon be expanded to include the remaining quests which have no explicit skill requirements like [Rag and Bone Man I](https://oldschool.runescape.wiki/w/Rag_and_Bone_Man_I).

### Quest dependency graph

After scraping and storing requirements in `txt` format, quests are connected based on their location in various questlines. This dependency graph can create a full list of every quest and every boostable or unboostable skill requirement to unlock and complete that quest. For example, we can write this very short script:

```python
import skillock.dag as dag

print(dag.create_quest_breakdown("Desert Treasure"))
```

This will give the following result:

```
Quest requirements
Priest in Peril
Death Plateau
Troll Stronghold
Waterfall Quest
Temple of Ikov
The Dig Site
The Tourist Trap

Skill requirements (boosted/unboosted)
Agility: 15/*
Firemaking: 50/*
Fletching: 10/*
Herblore: 10/*
Magic: */50
Ranged: */40
Slayer: */10
Smithing: */20
Thieving: 42/53
```

First, it lists every quest that must be completed to start Desert Treasure. Then it shows the highest skill requirements for the prerequisite quests and Desert Treasure itself. The left value is the highest boostable required level, while the right must be unboosted. Absent values are indicated with `*`, so you can boost to 50 Firemaking, but must have an unboosted 50 Magic. For Thieving you can make progress by boosting to 42, but ultimately must have an unboosted 53. If you run `skillock.dag.main()`, it will produce one of these for every scraped quest in the `txt` file.

### Text file format

There are two ways which requirements are organized: quest-based and skill-based. Each line of `quests.txt` looks like this:

```
Quest_Name:Quest_Prereq_1,Quest_Prereq_2:Skill_1-lvl,Skill_2*-lvl
```

The sections are divided by colons, and each section is subdivided with commas. Skill requirements with an asterisk `*` next to the name can be boosted. Lines of `skills.txt` are very similar:

```
Skill_Name:lvl-Quest_Name_1,lvl-Quest_Name_2*,lvl-Quest_Name_3
```

Quests marked with an asterisk are boostable. When reading this data from a file, take each line and use the `from_string` methods of either `QuestReq` or `SkillReq`.

Whenever you generate or submit this data to create one of these objects, it is automatically added to a register, a special dictionary within each class. These can be quickly accessed using the `get` and `items` static methods:

```python

# get without arguments returns the entire register
for quest_req in QuestReq.get().values():
    print(str(quest_req))

# Get the first element of the set of SkillReqs for Agility
print(str(SkillReq.get("Agility")[0]))

# Shorthand for QuestReq.get().items()
for quest_name, quest_req in QuestReq.items():
    print(str(quest_req))
```

## Roadmap

Right now I'm focusing on expanding the coverage and utility of `skillock` before moving on to other stuff. There are plenty of tools to perform things such as DPS calculations, but that sort of basic functionality might end up in a miscellaneous package for people who want to experiment with OSRS data who are also learning Python generally. For example, the current project has an uncommitted module that has some functions for calculating XP requirements for a certain level, basic Wintertodt calculations, and the effect of experience-boosting gear such as the Angler's outfit. Depending on the direction which the community pushes, such features may make their way into the public library.

#### Planned features

* Expanded quest data to include those with no explicit skill or quest point requirements
* Functions to generate a snapshot of every quest and skill requirement needed to complete a skillocked account
* Snapshots which include multiple skills
* Analysis of the overlap between skillocks for potential synergies
* Scraping features for item requirements, recommendations, and iron concerns
* Start designing UI and visual representations of the data using something like [matplotlib](https://github.com/matplotlib/matplotlib), perhaps alongside [pygame](https://github.com/pygame/pygame) or tkinter

Overall, I want this library to provide data analysis tools for creators trying to come up with interesting content and players looking to engage with unique challenges. There is a lot of wonderful theorycrafting and useful tools and plugins which emerged to augment such experiences. But I haven't seen much in the way of tools for the theorycrafting itself, and I hope as this library grows it will equip people to keep expanding their challenges.

If you would like to suggest a feature or share what you've done with this library, feel free to post it to [this GitHub discussion](https://github.com/cxr00/osrs/discussions/1)!
