from __future__ import annotations

import re
from dataclasses import dataclass

from experiment import PERSONALITIES, TASKS, CodingTask, Personality
from llm_client import chat_completion


CODE_HINTS = (
    "vector<",
    "string",
    "unordered_map",
    "unordered_set",
    "stack<",
    "int ",
    "bool ",
    "return",
    "for ",
    "while ",
    "if ",
    "push_back",
    "cout",
    "#include",
    "::",
)
TEST_HINTS = ("assert", "测试", "test", "用例", "输入", "输出", "example", "例如", "比如")
DEBUG_HINTS = ("bug", "错误", "报错", "异常", "边界", "空", "重复", "越界", "漏", "错")
COMPLEXITY_HINTS = ("复杂度", "O(", "时间", "空间", "遍历一次", "哈希", "二分", "递归", "双指针", "set", "dict")


@dataclass
class InteractionState:
    session_id: str
    participant_id: str
    personality_key: str
    task_key: str
    turn_id: int = 0


def get_personality(key: str) -> Personality:
    if key not in PERSONALITIES:
        raise ValueError(f"Unknown personality: {key}")
    return PERSONALITIES[key]


def get_task(key: str) -> CodingTask:
    if key not in TASKS:
        raise ValueError(f"Unknown task: {key}")
    return TASKS[key]


def opening_message(personality_key: str, task_key: str) -> str:
    """参与者开始实验后，生成智能体的第一条开场消息。"""

    personality = get_personality(personality_key)
    task = get_task(task_key)
    points = "、".join(task.knowledge_points[:3])
    return (
        f"{personality.opening}\n\n"
        f"我现在要学的是「{task.title}」。我知道它可能会用到：{points}。"
    )


def analyze_student_message(message: str) -> dict[str, int | bool]:
    """为实验日志提取轻量级互动特征。

    这些规则只用于实验行为编码，不参与智能体回复生成。
    智能体回复由大模型根据人格提示词和对话上下文生成。
    """

    normalized = message.lower()
    code_present = any(hint in message for hint in CODE_HINTS) or bool(
        re.search(r"^\s{4,}\S+", message, flags=re.MULTILINE)
    )
    return {
        "code_present": code_present,
        "explanation_count": _count_any(message, ("因为", "所以", "意思是", "原理", "思路", "为了", "表示")),
        "example_count": _count_any(message, ("例如", "比如", "假设", "示例", "case", "输入")),
        "test_case_count": _count_any(normalized, TEST_HINTS),
        "debugging_count": _count_any(normalized, DEBUG_HINTS),
        "complexity_count": _count_any(message, COMPLEXITY_HINTS),
        "politeness_count": _count_any(message, ("请", "谢谢", "没关系", "可以", "你可以", "别担心")),
    }


def generate_agent_reply(
    *,
    personality_key: str,
    task_key: str,
    student_message: str,
    turn_id: int,
    history: list[dict[str, str]] | None = None,
) -> tuple[str, dict[str, int | bool]]:
    """生成可教智能体的下一轮回复，并返回可写入日志的特征。"""

    personality = get_personality(personality_key)
    task = get_task(task_key)
    features = analyze_student_message(student_message)
    messages = build_llm_messages(
        personality=personality,
        task=task,
        student_message=student_message,
        turn_id=turn_id,
        history=history or [],
        features=features,
    )
    reply = chat_completion(messages)
    return reply, features


def build_llm_messages(
    *,
    personality: Personality,
    task: CodingTask,
    student_message: str,
    turn_id: int,
    history: list[dict[str, str]],
    features: dict[str, int | bool],
) -> list[dict[str, str]]:
    """把实验条件、题目、历史对话和当前学生输入组装成模型消息。"""

    system_prompt = _build_system_prompt(personality, task, turn_id, features)
    messages = [{"role": "system", "content": system_prompt}]
    for item in history:
        student = item.get("student_message")
        agent = item.get("agent_message")
        if student:
            messages.append({"role": "user", "content": student})
        if agent:
            messages.append({"role": "assistant", "content": agent})
    messages.append({"role": "user", "content": student_message})
    return messages


def _build_system_prompt(
    personality: Personality,
    task: CodingTask,
    turn_id: int,
    features: dict[str, int | bool],
) -> str:
    """构造控制大模型行为的系统提示词。"""

    feature_notes = _feature_notes(features)
    personality_examples = "\n".join(f"- {item}" for item in personality.prompts)
    return f"""你正在参与一个编程教育研究。
你扮演一个“可教 AI 学生”，不是编程导师。
用户是你的老师，你的任务是通过提问、复述和表达困惑，让用户教会你解题。
本实验要求使用 C++ 解决编程题。除非用户主动比较其他语言，否则你只围绕 C++ 语法、STL 容器和 C++ 解题思路提问。

当前人格条件：{personality.name}
人格表现要求：
- {personality.description}
- 你需要稳定保持该人格特质。
- 可参考这些提问风格：
{personality_examples}

当前编程题：
题目：{task.title}
难度：{task.difficulty}
题干：{task.prompt}
数据范围：{"；".join(task.constraints)}
示例：{task.example}
知识点：{"、".join(task.knowledge_points)}

交互规则：
1. 不要直接给出完整答案或完整参考代码。
2. 不要替用户完成教学任务。
3. 每轮只提出一个主要问题。
4. 回复 2-4 句话，语气自然，符合当前人格。
5. 如果用户解释正确，先简短复述你的理解，再追问一个能促进教学的问题。
6. 如果用户解释不清或可能有误，以学生身份表达困惑，请用户澄清。
7. 优先引导用户解释算法思路、代码步骤、示例演算、边界情况、测试方法和复杂度。

当前轮次：{turn_id}
学生消息自动编码提示：{feature_notes}
"""


def _feature_notes(features: dict[str, int | bool]) -> str:
    notes = []
    if features["code_present"]:
        notes.append("学生已经给出或提到代码")
    else:
        notes.append("学生还没有给出代码")
    if features["test_case_count"] == 0:
        notes.append("学生还没有明显给出测试用例")
    if features["debugging_count"] == 0:
        notes.append("学生还没有明显讨论边界或错误情况")
    if features["complexity_count"] == 0:
        notes.append("学生还没有明显讨论复杂度")
    return "；".join(notes)


def _count_any(text: str, hints: tuple[str, ...]) -> int:
    return sum(text.count(hint) for hint in hints)
