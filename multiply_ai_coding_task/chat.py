import os
from dataclasses import dataclass, field
from enum import Enum
import datetime as dt
import re
from multiply_ai_coding_task.factfind import GoalType, NewHomeGoalInformation,  NewCarInformation, OtherGoalInformation, Goal, User
from google import genai

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")


def llm(prompt: str) -> str:
    client = genai.Client(api_key=GEMINI_API_KEY)
    response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
    return response.text


class Sender(Enum):
    USER = "Vibhu"
    AI = "Gemi"


@dataclass
class Message:
    text: str
    sender: Sender


@dataclass
class ExtractedInformation:
    user: User = None

    def __str__(self) -> str:
        return(
        f"Name: {self.user.first_name} {self.user.last_name}\n"
        f"Email: {self.user.email}\n"
        f"DOB: {self.user.date_of_birth}\n"
        f"Goals:\n" +
        "\n".join([
            f"- {goal.goal_type.value}: {goal.goal_specific_information}"
            for goal in self.user.goals
        ])
        )


@dataclass
class ConversationState:
    finished: bool = False
    messages: list[Message] = field(default_factory=list)
    new_messages: list[Message] = field(default_factory=list)
    extracted_information: ExtractedInformation = field(default_factory=ExtractedInformation)


def parse_info(text: str) -> dict:
    """
    Very simple key-based parsing. In production, you can replace this
    with structured output from Gemini (e.g., function calling).
    """
    result = {}
    lines = iter(text.lower().split("\n"))
    for line in lines:
        if "name" in line:
            result["first_name"] = line.split(":")[-1].split(" ")[-2].strip()[1:]
            result["last_name"] = line.split(":")[-1].split(" ")[-1].strip()[:-2]

        if "email" in line:
            result["email"] = line.split()[-1]

        if "date_of_birth" in line:
            dob = line.split()[-1]
            try:
                result["date_of_birth"] = match = re.search(r"\d{4}-\d{2}-\d{2}", line)
                if match:
                    result["date_of_birth"] = dt.datetime.strptime(match.group(), "%Y-%m-%d").date()
                else:
                    result["date_of_birth"] = dt.datetime.strptime(dob, "%Y-%m-%d").date()  
            except:
                pass
        if "newhomegoalinformation" in line:
            result['NewHomeGoalInformation'] = {}
            while '},' not in line:
                try:
                    line = next(lines)
                    # Assuming the line contains JSON-like structure
                    # Extract the relevant information
                    if 'location' in line:
                        result['NewHomeGoalInformation']['location'] = line.split(": ")[1].strip()[:-2][1:]
                    if 'house_price' in line:
                        price_str = line.split('"house_price": ')[1].split(',')[0].strip().strip('"')
                        result['NewHomeGoalInformation']['house_price'] = float(price_str)                
                    if 'deposit_amount' in line:
                        deposit_str = line.split('"deposit_amount": ')[1].split(',')[0].strip().strip('"')
                        result['NewHomeGoalInformation']['deposit_amount'] = float(deposit_str)
                    if 'purchase_date' in line:
                        match = re.search(r"\d{4}-\d{2}-\d{2}", line)
                        result['NewHomeGoalInformation']['purchase_date'] = dt.datetime.strptime(match.group(), "%Y-%m-%d").date()
                except StopIteration:   
                    break

        if "newcarinformation" in line:
            result['NewCarInformation'] = {}
            while '},' not in line:
                try:
                    line = next(lines)
                    # Assuming the line contains JSON-like structure
                    # Extract the relevant information
                    if 'car_type' in line:
                        result['NewCarInformation']['car_type'] = line.split(": ")[1].strip()[:-2][1:]
                    if 'car_price' in line:
                        price_str = line.split('"car_price": ')[1].split(',')[0].strip().strip('"')
                        result['NewCarInformation']['car_price'] = float(price_str)    
                    if 'purchase_date' in line:
                        match = re.search(r"\d{4}-\d{2}-\d{2}", line)
                        result['NewCarInformation']['purchase_date'] = dt.datetime.strptime(match.group(), "%Y-%m-%d").date()
                except StopIteration:
                    break
        if "othergoalinformation" in line:
            result['OtherGoalInformation'] = {}
            while '},' not in line:
                try:
                    line = next(lines)
                    # Assuming the line contains JSON-like structure
                    # Extract the relevant information
                    if 'description' in line:
                        result['OtherGoalInformation']['description'] = line.split(": ")[1].strip()[:-2][1:]
                    if 'amount_required' in line:
                        price_str = line.split('"amount_required": ')[1].split(',')[0].strip().strip('"')
                        result['OtherGoalInformation']['amount_required'] = float(price_str)    
                    if 'target_date' in line:
                        match = re.search(r"\d{4}-\d{2}-\d{2}", line)
                        result['OtherGoalInformation']['target_date'] = dt.datetime.strptime(match.group(), "%Y-%m-%d").date()
                except StopIteration:
                    break
    return result


def chat_response(state: ConversationState) -> ConversationState:

    last_msg = state.messages[-1].text

    # Ask LLM to identify user info
    prompt = (
        "Extract structured user info from the following message without reasoning and don't pass the keys if they are null:\n"
        "Expected keys: name, email, date_of_birth (YYYY-MM-DD)\n, NewHomeGoalInformation(location,house_price,deposit_amount,purchase_date(YYYY-MM-DD))\n, NewCarInformation(car_type,car_price,purchase_date(YYYY-MM-DD))\n, OtherGoalInformation(description,amount_required,target_date(YYYY-MM-DD))\n"
        f"{last_msg}"
    )

    gemini_response = llm(prompt)
    print("Gemini response:", gemini_response)
    parsed_info = parse_info(gemini_response)
    print("Parsed info:", parsed_info)
    # If no user exists yet, create one with what we have
    user = state.extracted_information.user
    if not user:
        user = User(
            first_name=parsed_info.get("first_name", ""),
            last_name=parsed_info.get("last_name", ""),
            email=parsed_info.get("email", ""),
            date_of_birth=parsed_info.get("date_of_birth", dt.date.today()),
            goals=[]
        )
    else:
        # Update only missing fields
        user.first_name = user.first_name or parsed_info.get("first_name")
        user.last_name = user.last_name or parsed_info.get("last_name")
        user.email = user.email or parsed_info.get("email")
        user.date_of_birth = user.date_of_birth or parsed_info.get("date_of_birth")
        # Add goal information if present 
    if "NewHomeGoalInformation" in parsed_info:
            info = parsed_info["NewHomeGoalInformation"]
            home_goal = NewHomeGoalInformation(
                location=info["location"],
                house_price=info["house_price"],
                deposit_amount=info["deposit_amount"],
                purchase_date=info["purchase_date"],
            )
            user.goals.append(
                Goal(
                    goal_type=GoalType.NEW_HOME,
                    goal_name="New Home",
                    goal_specific_information = home_goal,
                )
            )
    if "NewCarInformation" in parsed_info and len(parsed_info["NewCarInformation"])>0:
                info = parsed_info["NewCarInformation"]
                car_goal = NewCarInformation(
                    car_type=info["car_type"],
                    car_price=info["car_price"],
                    purchase_date=info["purchase_date"],
                )
                user.goals.append(
                    Goal(
                        goal_type=GoalType.NEW_CAR,
                        goal_name="New Car",
                        goal_specific_information=car_goal,
                    )
                )
    if "OtherGoalInformation" in parsed_info:
            info = parsed_info["OtherGoalInformation"]
            other_goal = OtherGoalInformation(
                description=info["description"],
                amount_required=info["amount_required"],
                target_date=info["target_date"],
            )
            user.goals.append(
                Goal(
                    goal_type=GoalType.OTHER,
                    goal_name="Other Goal",
                    goal_specific_information=other_goal,
                )
            )
    # Update the user in the extracted information

    state.extracted_information.user = user

    extracted_info = ExtractedInformation(user=user)

    # Check if all required info collected
    finished = all([
        user.first_name,
        user.last_name,
        user.email,
        user.date_of_birth
    ])

    # Generate response text
    response_text = gemini_response if not finished else f"Thanks, all info collected!\n\n{extracted_info}"

    return ConversationState(
        finished=finished,
        messages=state.messages,
        new_messages=[
            Message(
                text=response_text,
                sender=Sender.AI,
            )
        ],
        extracted_information=extracted_info,
    )
