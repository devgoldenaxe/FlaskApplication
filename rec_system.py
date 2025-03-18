import requests
import datetime
cache = {}

def get_students(schoolId, version):
    now = datetime.datetime.now()
    
    if schoolId in cache:
        students, timestamp = cache[schoolId]
        if now - timestamp < datetime.timedelta(days=1):
            print("Returning cached data.")
            return students

    # If no valid cached data is available, fetch new data.
    print("Fetching new data.")
    students = fetch_all_employee_details(schoolId, version)
    cache[schoolId] = (students, now)
    return students
 
page_count = 1000
def fetch_all_employee_details(company_id , version):
    url = "https://heartsend.io/version-test/api/1.1/obj/employeedetails"
    if version == "live":
        url = "https://heartsend.io/api/1.1/obj/employeedetails"
        
    headers = {
        "Authorization": "Bearer 7406b3c19debbbf1764237fa783e540f"
    }
    params = {
        "constraints": '[{"key": "company", "constraint_type": "equals", "value": "'+company_id+'"}]',
        "cursor": 0,
        "limit": page_count
    }
    print(company_id)
    all_results = []
    
    while True:
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code != 200:
            print(f"Error: {response.status_code}, {response.text}")
            break
        
        data = response.json().get("response", {})
        results = data.get("results", [])
        
        # Extract specific fields from each result
        # extracted_fields = [{'_id': result.get('_id', 'N/A'), 'Company': result.get('Company', 'N/A')} for result in results]
        all_results.extend(results)
        
        remaining = data.get("remaining", 0)
        cursor = data.get("cursor", 0)
        
        if remaining <= 0:
            break
        
        params["cursor"] = cursor + page_count
        
    
    return all_results

    
# Example usage:
# employee_details_df = fetch_all_employee_details("1713359491751x498199104691896300")
# print(employee_details_df)

##################################################
# 1. Constants & Configuration
##################################################

# (A) Availability penalties
AVAILABILITY_PENALTIES = {
    "Currently available": 0,
    "Limited availability": -2,
    "Currently Not available": -5
}

# (B) Weights for various feature matches
WEIGHT_HEALTH_CONDITION_MATCH = 2
WEIGHT_HOBBY_MATCH = 5
WEIGHT_SKILL_MATCH = 3
WEIGHT_RACE_MATCH = 1
WEIGHT_RELIGION_MATCH = 1
WEIGHT_GENDER_MATCH = 1

# (C) Intentions scoring approach:
#     - Mentor ↔ Mentee: +5
#     - Same intentions: +2
#     - "Skill sharing" ↔ "Skill building": +2
def intention_score(intA, intB):
    # Mentor ↔ Mentee
    mentor_mentee_pairs = {("Mentor", "Mentee"), ("Mentee", "Mentor")}
    if (intA, intB) in mentor_mentee_pairs:
        return 5
    # Same exact intention
    if intA == intB:
        return 2
    # Partial synergy: "Skill sharing" & "Skill building"
    synergy_pairs = {("Skill sharing", "Skill building"), ("Skill building", "Skill sharing")}
    if (intA, intB) in synergy_pairs:
        return 2
    # else
    return 0

# (D) Complementary skill pairs (we add +2 if userA has one and userB has the other)
complementary_skills = {
    ("Marketing", "Sales"),
    ("Emotional Intelligence", "Interpersonal Skills"),
    ("Coding ( SQL,Python, R, SAS)", "Data Analysis"),
    ("Decision-Making", "Problem Solving"),
    ("Leadership", "Management"),
    ("Communication Skills", "Presentation Skills"),
    ("Negotiation", "Conflict resolution"),
    ("Project Management", "Process improvements"),
    ("Design", "Graphic design"),
    ("Teamwork", "Interpersonal Skills")
}
COMPLEMENTARY_SKILL_POINTS = 2

# (E) States adjacency list: which states border which
STATE_NEIGHBORS = {
    "AL": ["FL", "GA", "MS", "TN"],
    "AK": [],
    "AZ": ["CA", "NV", "UT", "CO", "NM"],
    "AR": ["MO", "TN", "MS", "LA", "TX", "OK"],
    "CA": ["OR", "NV", "AZ"],
    "CO": ["WY", "NE", "KS", "OK", "NM", "AZ", "UT"],
    "CT": ["NY", "MA", "RI"],
    "DE": ["MD", "PA", "NJ"],
    "FL": ["AL", "GA"],
    "GA": ["FL", "AL", "TN", "NC", "SC"],
    "HI": [],
    "ID": ["WA", "OR", "NV", "UT", "WY", "MT"],
    "IL": ["WI", "IA", "MO", "KY", "IN"],
    "IN": ["MI", "OH", "KY", "IL"],
    "IA": ["MN", "SD", "NE", "MO", "IL", "WI"],
    "KS": ["NE", "CO", "OK", "MO"],
    "KY": ["IN", "OH", "WV", "VA", "TN", "MO", "IL"],
    "LA": ["TX", "AR", "MS"],
    "ME": ["NH"],
    "MD": ["VA", "WV", "PA", "DE"],
    "MA": ["NY", "VT", "NH", "RI", "CT"],
    "MI": ["IN", "OH", "WI"],
    "MN": ["ND", "SD", "IA", "WI"],
    "MS": ["LA", "AR", "TN", "AL"],
    "MO": ["IA", "NE", "KS", "OK", "AR", "TN", "KY", "IL"],
    "MT": ["ID", "WY", "SD", "ND"],
    "NE": ["SD", "WY", "CO", "KS", "MO", "IA"],
    "NV": ["CA", "OR", "ID", "UT", "AZ"],
    "NH": ["ME", "MA", "VT"],
    "NJ": ["NY", "PA", "DE"],
    "NM": ["AZ", "UT", "CO", "OK", "TX"],
    "NY": ["PA", "NJ", "CT", "MA", "VT"],
    "NC": ["GA", "SC", "TN", "VA"],
    "ND": ["MT", "SD", "MN"],
    "OH": ["PA", "WV", "KY", "IN", "MI"],
    "OK": ["KS", "MO", "AR", "TX", "NM", "CO"],
    "OR": ["WA", "ID", "NV", "CA"],
    "PA": ["NY", "NJ", "DE", "MD", "WV", "OH"],
    "RI": ["CT", "MA"],
    "SC": ["GA", "NC"],
    "SD": ["ND", "MN", "IA", "NE", "WY", "MT"],
    "TN": ["KY", "VA", "NC", "GA", "AL", "MS", "AR", "MO"],
    "TX": ["NM", "OK", "AR", "LA"],
    "UT": ["ID", "WY", "CO", "NM", "AZ", "NV"],
    "VT": ["NY", "MA", "NH"],
    "VA": ["MD", "NC", "TN", "KY", "WV"],
    "WA": ["ID", "OR"],
    "WV": ["PA", "MD", "VA", "KY", "OH"],
    "WI": ["MN", "IA", "IL", "MI"],
    "WY": ["MT", "SD", "NE", "CO", "UT", "ID"],
    "DC": ["MD", "VA"]
}

##################################################
# 2. Rule-Based Scoring Function
##################################################

def compute_match_score(userA, userB):
    """
    Calculates a match score for two user dictionaries based on:
      - Availability
      - Location
      - Health Condition
      - hobbies
      - Intention
      - Race
      - Religion
      - Skills (shared + complementary)
      - Gender
    Returns an integer or float score (the higher, the better).
    """

    score = 0

    # A) AVAILABILITY (Penalties)
    penaltyA = AVAILABILITY_PENALTIES.get(userA.get("Availability"), 0)
    penaltyB = AVAILABILITY_PENALTIES.get(userB.get("Availability"), 0)
    score += (penaltyA + penaltyB)

    # B) LOCATION
    cityA = userA.get("City", "")
    cityB = userB.get("City", "")
    stateA = userA.get("City", "")
    stateB = userB.get("City", "")

    if cityA and cityB and cityA == cityB:
        score += 15
    else:
        if stateA == stateB and stateA:
            score += 5
        else:
            neighbors_of_A = STATE_NEIGHBORS.get(stateA, [])
            if stateB in neighbors_of_A:
                score += 2

    # C) HEALTH CONDITIONS
    hcA = userA.get("Health_Condition", "")
    if not isinstance(hcA, str):
        hcA = ""
    hcB = userB.get("Health_Condition", "")
    if not isinstance(hcB, str):
        hcB = ""

    if (not hcA or hcA.strip().lower() == "none"):
        setA = set()
    else:
        setA = set(h.strip() for h in hcA.split(","))

    if (not hcB or hcB.strip().lower() == "none"):
        setB = set()
    else:
        setB = set(h.strip() for h in hcB.split(","))

    shared_conditions = setA.intersection(setB)
    score += len(shared_conditions) * WEIGHT_HEALTH_CONDITION_MATCH

    # D) HOBBIES
    hobbyA = userA.get("Hobby", "")
    hobbyB = userB.get("Hobby", "")
    hobbiesA = set(h.strip().lower() for h in hobbyA.split(",")) if hobbyA else set()
    hobbiesB = set(h.strip().lower() for h in hobbyB.split(",")) if hobbyB else set()
    shared_hobbies = hobbiesA.intersection(hobbiesB)
    score += len(shared_hobbies) * WEIGHT_HOBBY_MATCH

    # E) INTENTIONS
    intA = userA.get("Intentions", "")
    intB = userB.get("Intentions", "")
    score += intention_score(intA, intB)

    # F) RACE
    raceA = userA.get("Race", "")
    raceB = userB.get("Race", "")
    if raceA and raceA == raceB:
        score += WEIGHT_RACE_MATCH

    # G) RELIGION
    relA = userA.get("Religion", "")
    relB = userB.get("Religion", "")
    if relA and relA == relB:
        score += WEIGHT_RELIGION_MATCH

    # H) SKILLS
    skillsA = set(s.strip() for s in userA.get("Skills", "").split(",") if s.strip())
    skillsB = set(s.strip() for s in userB.get("Skills", "").split(",") if s.strip())

    shared_skills = skillsA.intersection(skillsB)
    score += len(shared_skills) * WEIGHT_SKILL_MATCH

    # Complementary pairs
    for sA in skillsA:
        for sB in skillsB:
            if (sA, sB) in complementary_skills or (sB, sA) in complementary_skills:
                score += COMPLEMENTARY_SKILL_POINTS

    # I) GENDER
    genA = userA.get("Gender", "")
    genB = userB.get("Gender", "")
    # Only add if identical
    if genA and genB and genA == genB:
        score += WEIGHT_GENDER_MATCH

    return score

##################################################
# 3. Generating Recommendations
##################################################

def recommend_for_user(user, all_users, top_n=5):
    """
    Return the top_n recommended users for the given 'user'
    based on the rule-based scoring function.
    ALSO: we skip users who are "Currently Not available."
    """
    scores = []
    for other in all_users:
        # Skip comparing user to themselves
        if other.get("Employee Email") == user.get("Employee Email"):
            continue

        # NEW RULE: skip if the other user is "Currently Not available"
        if other.get("Availability") == "Currently Not available":
            continue

        match_score = compute_match_score(user, other)
        scores.append((other, match_score))

    # Sort by descending score
    scores.sort(key=lambda x: x[1], reverse=True)
    return scores[:top_n]



##################################################
# 4. Example Usage with an Excel File
##################################################

def module(company_id, user_id , version):
    # 1) Load the data from Excel (the xlsx you created).


    # excel_file_path = "synthetic_output.xlsx"  # <-- CHANGE THIS to your actual file name/path
    # sheet_name = 0  # or the name of the sheet, e.g. "Sheet1"
    print(version)
    df_out = get_students(company_id , version)
    
    

    # 2) Convert to a list of dictionaries
    # list_of_users = df_out.to_dict(orient="records")

    # 3) Create or pick a test user to get recommendations FOR.


    #    Option B: create a brand new user dictionary (not in Excel) to see how they'd match
    # test_user = {
    #     "Full name": "Testy",
    #     "Employee Email": "[email protected]",
    #     "Availability": "Limited availability",
    #     "Health Condition": "None",
    #     "hobbies": "reading, cooking/baking",
    #     "Intention": "Mentee",
    #     "Race": "White or Caucasian",
    #     "Religion": "Christianity",
    #     "Skills desired": "Management, Writing Skills, Data Analysis",
    #     "State": "New York",
    #     "state_id": "NY",
    #     "Gender": "Other"
    # }

    # 4) Get the top 5 recommended matches for the test user

    # extended_users = df_out + [test_user]
    # print(df_out[0])
    # print(len(df_out))
    # for item in df_out:
    #     print("id: " + item["_id"])
    test_user = next((item for item in df_out if item['_id'] == user_id), None)
    # Now let's retrieve top 5 for the test_user
    ids = []
    if test_user:
        top_5 = recommend_for_user(test_user, df_out, top_n=20)
        ids = [item['_id'] for item, score in top_5]
    # print(top_5,"------")
    # 5) Print out the recommended matches
    # print(f"Top 5 recommendations for {test_user['Full name']} ({test_user['Employee Email']}):\n")
    # for match_user, score in top_5:
    #     print(f"Name: {match_user['Full name']}")
    #     print(f"Email: {match_user['Employee Email']}")
    #     print(f"Score: {score}")
    #     print("Features:")
    #     print(f"  Availability: {match_user.get('Availability', '')}")
    #     print(f"  Health_Condition: {match_user.get('Health Condition', '')}")
    #     print(f"  Hobby: {match_user.get('hobbies', '')}")
    #     print(f"  Intentions: {match_user.get('Intention', '')}")
    #     print(f"  Race: {match_user.get('Race', '')}")
    #     print(f"  Religion: {match_user.get('Religion', '')}")
    #     print(f"  Skills: {match_user.get('Skills desired', '')}")
    #     print(f"  Location: {match_user.get('State', '')}, {match_user.get('state_id', '')}")
    #     print(f"  Gender: {match_user.get('Gender', '')}")
    #     print("-" * 40)


    # test_user = {
    #     "Full name": "Testy",
    #     "Employee Email": "[email protected]",
    #     "Availability": "Limited availability",
    #     "Health Condition": "None",
    #     "hobbies": "reading, cooking/baking",
    #     "Intention": "Mentee",
    #     "Race": "White or Caucasian",
    #     "Religion": "Christianity",
    #     "Skills desired": "Management, Writing Skills, Data Analysis",
    #     "State": "New York",
    #     "state_id": "NY",
    #     "Gender": "Other"
    # }

    # print(type(top_5))
    
    print(ids)
    return ids

# if __name__ == "__main__":
#     module("1715320195395x862460891761909300","1724149699789x546285759204683260")