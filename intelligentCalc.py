import math
import random
import re
import json
import difflib
import os
from datetime import datetime
from text2digits import text2digits
from sty import fg, bg, ef

from config import (
    ACTION_TYPE,
    OPERATIONS,
    NATURAL_LANGUAGE_PATH,
    GREETING,
    HELP,
    EXIT,
    HISTORY,
    LOGO
)

class IntelligentCalculator:
    def __init__(self):
        self.history = self.load_history()
        self.action_type = ACTION_TYPE
        self.operations = OPERATIONS
        self.natural_language = self.load_natural_language(NATURAL_LANGUAGE_PATH)
        self.t2d = text2digits.Text2Digits()

    def load_history(self):
        try:
            with open("history.txt", "r", encoding="utf-8") as f:
                return f.read().splitlines()
        except FileNotFoundError:
            if not os.path.exists("history.txt"):
                with open("history.txt", "w", encoding="utf-8"):
                    pass
            return []

    def load_natural_language(self, path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def welcome(self):
        print(LOGO)
        print("=" * 50)
        print(self.natural_language["Welcome"])
        print("=" * 50)

    def reply(self, action):
        if action == "Greeting":
            print("\n" + self.natural_language["Greeting"][random.randint(0, len(self.natural_language["Greeting"]) - 1)])
        elif action == "Help":
            print("\n" + self.natural_language["Help"])
        elif action == "Exit":
            print("\n" + self.natural_language["Exit"][random.randint(0, len(self.natural_language["Greeting"]) - 1)])
            exit()
        elif action == "History":
            self.show_history()

    def parse_input(self, user_input):
        user_input = user_input.strip().lower()

        for action, keywords in [("Greeting", GREETING), ("Help", HELP), ("Exit", EXIT), ("History", HISTORY)]:
            if any(re.search(r'\b' + re.escape(kw) + r'\b', user_input) for kw in keywords):
                return action, None

        return self.parse_natural_language(user_input)

    def parse_natural_language(self, text: str):
        text = self.t2d.convert(text)

        suggestion = self.suggest_correction(text)
        if suggestion:
            return "Suggestion", suggestion

        special_result = self.parse_special_patterns(text)
        if special_result is not None:
            return special_result

        for op_symbol, keywords in self.operations.items():
            for word in keywords:
                if word != "^":
                    text = re.sub(r'\b' + re.escape(word) + r'\b', f' {op_symbol} ', text)
                else:
                    text = text.replace(word, f' {op_symbol} ')
                    
        # Just get the mathematical expression only
        """
        For example:
        "What is 5 + 10?" -> ["5", "+", "10"]
        "Can u do 20 / 4?" -> ["20", "/", "4"]
        Operations included: - + / * ! % √ (** also supported cuz of ('*'))
        """
        expression = re.findall(r"[-+/*!%√\d\.]+", text)

        if expression:
            expr_str = " ".join(expression)
            try:
                if "**" in expr_str:
                    num = re.search(r"\d+", expr_str)
                    is_only_one_num = len(re.findall(r"\d+", expr_str)) == 1
                    if num and is_only_one_num:
                        num = int(num.group(0))
                        result = num ** 2
                        expr_str = f"{num}**2"
                        return "Operation", (expr_str, result)
                if "√" in expr_str:
                    num = re.search(r"\d+", expr_str)
                    if num:
                        num = float(num.group(0))
                        result = math.sqrt(num)
                        expr_str = f"sqrt({int(num)})"
                        return "Operation", (expr_str, result)
                if "%" in expr_str:
                    result = eval(expr_str.replace("%", "/ 100 * "))
                    return "Operation", (expr_str, result)
                if "!" in expr_str:
                    num = re.search(r"-?\d+", expr_str)
                    if num:
                        num = int(num.group(0))
                        result = math.factorial(num)
                        expr_str = f"{num}!"
                        return "Operation", (expr_str, result)

                result = eval(expr_str)
                return "Operation", (expr_str, result)
            except ZeroDivisionError:
                return "Error", self.natural_language["DivisionByZero"]
            except ValueError:
                return "Error", self.natural_language["FactorialError"]
            except Exception:
                return None, None
        return None, None

    def suggest_correction(self, text):
        words = text.split()
        all_keywords = [kw for lst in self.operations.values() for kw in lst]
        suggestions = {}

        for word in words:
            if any(word in kw for kw in all_keywords):
                continue

            close = difflib.get_close_matches(word, all_keywords, n=1, cutoff=0.75)
            if close and close[0] != word:
                suggestions[word] = close[0]

        return suggestions if suggestions else None

    def parse_special_patterns(self, text):
        patterns = {
            r"[sum\s+of|add]\s+([\d\s,]+)\s+and\s+([\d\s,]+)": "+",
            r"subtract\s+([\d\s,]+(?:\s+and\s+[\d\s,]+)?)\s+from\s+(\d+)": "-",
            r"multiply\s+([\d\s,]+(?:\s+and\s+[\d\s,]+)?)\s+by\s+(\d+)": "*",
            r"divide\s+([\d\s,]+(?:\s+and\s+[\d\s,]+)?)\s+by\s+(\d+)": "/",
            r"power\s+of\s+(\d+)\s+to\s+(\d+)": "**",
        }
        
        try:
            for pattern, op_symbol in patterns.items():
                match = re.search(pattern, text)
                if match:
                    numbers = [int(num) for num in re.findall(r'\d+', match.group(0))]

                    if op_symbol == "-":
                        for i in range(len(numbers) // 2):
                            numbers[i], numbers[-i - 1] = numbers[-i - 1], numbers[i]
                            
                    expr_str = f"{f' {op_symbol} '.join(map(str, numbers))}"
                    result = eval(expr_str)
                    return "Operation", (expr_str, result)
        except ZeroDivisionError:
            return "Error", self.natural_language["DivisionByZero"]
        except Exception:
            return None, None

    def calculation(self, data):
        if data:
            expr, result = data
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            if isinstance(result, float):
                result = round(result, 10)
            with open("history.txt", "a", encoding="utf-8") as f:
                f.write(f"{expr} = {result} | {now}\n")
            self.history.append(f"{expr} = {result} | {now}")
            print(f"\nResult: {expr} = {result}")

    def show_history(self):
        if not self.history:
            print("\nNo history yet.")
        else:
            print("\nCalculation History:")
            for i, record in enumerate(self.history):
                print(f" {i + 1}.", record)

    def main(self):
        self.welcome()

        while True:
            try:
                print(f"\n{fg.da_grey}> Ask some calculations{fg.rs}")
                user_input = input(f"{fg.li_cyan}{ef.bold}{ef.blink}>{ef.rs}{ef.rs}{fg.rs} ")
                action, data = self.parse_input(user_input)
                if action in self.action_type[0:4]:
                    self.reply(action)
                elif action == "Operation":
                    self.calculation(data)
                elif action == "Suggestion":
                    did_you_mean =  f"Did you mean: " + ", ".join(f"'{k}' → '{v}'" for k, v in data.items())
                    print("\n" + did_you_mean)
                    retry = input("Would you like to apply this correction and retry? (yes/no): ").strip().lower()
                    if retry == "yes":
                        corrected_input = user_input.lower()
                        for wrong, right in data.items():
                            corrected_input = re.sub(r'\b' + re.escape(wrong) + r'\b', right, corrected_input)
                        action, data = self.parse_input(corrected_input)
                        if action == "Operation":
                            self.calculation(data)
                        else:
                            print(self.natural_language["NotUnderstood"])
                elif action == "Error":
                    print(f"\n{bg.red}{ef.bold}Error:{ef.rs}{bg.rs} " + str(data))
                else:
                    print("\n" + self.natural_language["NotUnderstood"])
            except KeyboardInterrupt:
                self.reply("Exit")
                break
            except Exception as e:
                print("\n" + self.natural_language["NotUnderstood"])
                continue

    def run(self):
        self.main()

if __name__ == "__main__":
    i = IntelligentCalculator()
    i.run()