from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import engine
from engine import analyze_student_message, build_llm_messages, generate_agent_reply, opening_message


def test_opening_message_contains_task_title():
    message = opening_message("conscientiousness", "dedupe")
    assert "数组去重" in message
    assert "一步一步" in message


def test_message_analysis_detects_code_and_tests():
    features = analyze_student_message(
        "例如输入 {3,1,3}，可以测试输出 {3,1}。\n"
        "vector<int> dedupe(const vector<int>& nums) {\n"
        "    return nums;\n"
        "}\n"
    )
    assert features["code_present"] is True
    assert features["example_count"] >= 1
    assert features["test_case_count"] >= 1


def test_personality_reply_is_generated():
    original_chat_completion = engine.chat_completion
    engine.chat_completion = lambda messages: "我大概理解了字典保存已见数字的思路。你能用一个具体输入带我跑一遍吗？"
    try:
        reply, features = generate_agent_reply(
            personality_key="neuroticism",
            task_key="two_sum",
            student_message="因为我们可以用字典保存已经见过的数字，然后查找 target - x。",
            turn_id=1,
        )
    finally:
        engine.chat_completion = original_chat_completion

    assert reply
    assert "具体输入" in reply
    assert features["explanation_count"] >= 1


def test_llm_messages_include_personality_and_task():
    features = analyze_student_message("我会用二分查找，每次缩小一半范围。")
    messages = build_llm_messages(
        personality=engine.get_personality("conscientiousness"),
        task=engine.get_task("binary_search"),
        student_message="我会用二分查找，每次缩小一半范围。",
        turn_id=2,
        history=[],
        features=features,
    )
    assert messages[0]["role"] == "system"
    assert "尽责性" in messages[0]["content"]
    assert "二分查找目标值" in messages[0]["content"]
    assert "数据范围" in messages[0]["content"]
    assert "C++" in messages[0]["content"]
    assert messages[-1]["role"] == "user"


if __name__ == "__main__":
    test_opening_message_contains_task_title()
    test_message_analysis_detects_code_and_tests()
    test_personality_reply_is_generated()
    test_llm_messages_include_personality_and_task()
    print("All engine tests passed.")
