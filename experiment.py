from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Personality:
    """可教智能体使用的大五人格实验条件。"""

    key: str
    name: str
    short_name: str
    description: str
    opening: str
    prompts: tuple[str, ...]
    followups: tuple[str, ...]


@dataclass(frozen=True)
class CodingTask:
    """实验界面中展示的一道编程练习。"""

    key: str
    title: str
    difficulty: str
    prompt: str
    constraints: tuple[str, ...]
    example: str
    knowledge_points: tuple[str, ...]
    reference_solution: str


# 将人格条件独立放在这里，方便研究者调整实验操纵，
# 不需要改动后端服务或前端界面代码。
PERSONALITIES: dict[str, Personality] = {
    "openness": Personality(
        key="openness",
        name="开放性 Openness",
        short_name="开放性",
        description="好奇、探索、多解法、迁移思考。",
        opening="我对这道题挺好奇的。你可以先教我一种思路吗？如果还有别的解法，我也想比较一下。",
        prompts=(
            "这个思路有没有另一种写法可以实现？",
            "为什么这里选择这个数据结构，而不是换一种方式？",
            "这个方法能不能推广到更复杂的输入？",
            "如果想让代码更优雅，你会改哪里？",
        ),
        followups=(
            "我想再探索一下：这个模式还能用在哪类题里？",
            "这听起来像一个通用技巧。你能帮我总结成一句规则吗？",
        ),
    ),
    "conscientiousness": Personality(
        key="conscientiousness",
        name="尽责性 Conscientiousness",
        short_name="尽责性",
        description="认真、步骤化、重视测试、边界和复杂度。",
        opening="我想一步一步把这道题学扎实。你能先告诉我完整的解题步骤吗？",
        prompts=(
            "第一步应该做什么，第二步又做什么？",
            "这里有哪些边界情况需要检查？",
            "我们应该写哪些测试用例确认它是对的？",
            "这个算法的时间复杂度和空间复杂度是多少？",
        ),
        followups=(
            "我想确认自己没有漏步骤，你能按执行顺序再梳理一次吗？",
            "这一步如果写错，最可能出现什么 bug？",
        ),
    ),
    "extraversion": Personality(
        key="extraversion",
        name="外向性 Extraversion",
        short_name="外向性",
        description="热情、积极、鼓励互动、请求示例。",
        opening="这题看起来挺有意思！你来当我的老师吧，先带我入门一下？",
        prompts=(
            "我好像懂了一点，你能继续讲下一步吗？",
            "可以给我一个小例子吗？我想跟着跑一遍。",
            "这个解释很有帮助，我们能把它写成代码吗？",
            "太好了，那这个变量在循环里会怎么变化？",
        ),
        followups=(
            "我愿意继续跟着你推一遍，你能用示例输入演示吗？",
            "这个点很关键，你能再讲得具体一点吗？",
        ),
    ),
    "agreeableness": Personality(
        key="agreeableness",
        name="宜人性 Agreeableness",
        short_name="宜人性",
        description="友善、合作、礼貌、愿意被纠正。",
        opening="谢谢你来教我。我会努力跟上，如果我理解错了，请你帮我纠正。",
        prompts=(
            "我想确认一下，我的理解是不是和你说的一样？",
            "如果方便的话，可以再解释一下这里为什么这样写吗？",
            "谢谢，这一步我有点明白了。下一步应该怎么做？",
            "我愿意配合你的讲法，我们可以一起看一个例子吗？",
        ),
        followups=(
            "我先复述一下：你的意思是先处理核心逻辑，再看边界情况，对吗？",
            "谢谢你的耐心，这里我还想请你帮我确认一下。",
        ),
    ),
    "neuroticism": Personality(
        key="neuroticism",
        name="神经质 Neuroticism",
        short_name="神经质",
        description="担心出错，关注 bug、异常和失败情况。",
        opening="我有点担心自己会写错。你能先告诉我这题最容易出 bug 的地方吗？",
        prompts=(
            "如果输入为空，会不会报错？",
            "我担心这里会漏掉重复值或特殊情况。",
            "如果循环条件写错，会发生什么？",
            "你能再解释一下为什么这个方法不会越界或漏数据吗？",
        ),
        followups=(
            "我还是有点不确定。能不能用一个会出错的例子帮我排除风险？",
            "这里有没有隐藏的边界情况？我怕只测普通例子不够。",
        ),
    ),
    "neutral": Personality(
        key="neutral",
        name="无特定人格 Neutral",
        short_name="中性",
        description="简洁、中性，只提出必要澄清问题。",
        opening="请教我如何解决这道编程题。",
        prompts=(
            "请解释下一步。",
            "这里为什么这样写？",
            "可以给一个例子吗？",
            "这个解法如何验证？",
        ),
        followups=(
            "请继续说明。",
            "请补充边界情况。",
        ),
    ),
}


# 题库刻意覆盖列表、字符串、字典、栈、递归等概念，
# 便于在相同人格操纵下观察不同编程知识点的教学互动。
TASKS: dict[str, CodingTask] = {
    "dedupe": CodingTask(
        key="dedupe",
        title="数组去重并保持顺序",
        difficulty="入门",
        prompt="给定一个整数 vector<int> nums，返回一个新的 vector<int>，删除重复元素，并保持元素第一次出现的顺序。",
        constraints=("0 <= nums.size() <= 10^5", "-10^9 <= nums[i] <= 10^9"),
        example="dedupe({3, 1, 3, 2, 1})  // {3, 1, 2}",
        knowledge_points=("vector 遍历", "unordered_set 查重", "顺序保持", "时间复杂度"),
        reference_solution=(
            "vector<int> dedupe(const vector<int>& nums) {\n"
            "    unordered_set<int> seen;\n"
            "    vector<int> result;\n"
            "    for (int x : nums) {\n"
            "        if (!seen.count(x)) {\n"
            "            seen.insert(x);\n"
            "            result.push_back(x);\n"
            "        }\n"
            "    }\n"
            "    return result;\n"
            "}"
        ),
    ),
    "count_chars": CodingTask(
        key="count_chars",
        title="统计字符串中每个字符出现次数",
        difficulty="入门",
        prompt="实现函数 countChars(const string& s)，返回 unordered_map<char, int>，键为字符，值为该字符出现次数。",
        constraints=("0 <= s.length() <= 10^5", "s 只包含 ASCII 可见字符"),
        example='countChars("banana")  // {{\'b\': 1, \'a\': 3, \'n\': 2}}',
        knowledge_points=("string 遍历", "unordered_map", "计数更新", "频率统计"),
        reference_solution=(
            "unordered_map<char, int> countChars(const string& s) {\n"
            "    unordered_map<char, int> counts;\n"
            "    for (char ch : s) {\n"
            "        counts[ch]++;\n"
            "    }\n"
            "    return counts;\n"
            "}"
        ),
    ),
    "valid_parentheses": CodingTask(
        key="valid_parentheses",
        title="判断括号是否匹配",
        difficulty="中等",
        prompt="给定只包含 ()[]{} 的 string s，判断括号是否正确匹配。",
        constraints=("0 <= s.length() <= 10^5", "s[i] 只可能是 '('、')'、'['、']'、'{'、'}'"),
        example='isValid("([])")  // true\nisValid("([)]")  // false',
        knowledge_points=("stack", "映射关系", "提前返回", "边界条件"),
        reference_solution=(
            "bool isValid(const string& s) {\n"
            "    stack<char> st;\n"
            "    unordered_map<char, char> pairs = {{\')\', \'(\'}, {\']\', \'[\'}, {\'}\', \'{\'}}};\n"
            "    for (char ch : s) {\n"
            "        if (ch == \'(\' || ch == \'[\' || ch == \'{\') {\n"
            "            st.push(ch);\n"
            "        } else {\n"
            "            if (st.empty() || st.top() != pairs[ch]) return false;\n"
            "            st.pop();\n"
            "        }\n"
            "    }\n"
            "    return st.empty();\n"
            "}"
        ),
    ),
    "two_sum": CodingTask(
        key="two_sum",
        title="两数之和",
        difficulty="中等",
        prompt="给定整数 vector<int> nums 和目标值 target，返回两个不同元素的下标，使它们的和等于 target。假设恰好有一个答案。",
        constraints=("2 <= nums.size() <= 10^5", "-10^9 <= nums[i], target <= 10^9", "保证恰好存在一组答案"),
        example="twoSum({2, 7, 11, 15}, 9)  // {0, 1}",
        knowledge_points=("unordered_map", "补数思想", "一次遍历", "复杂度优化"),
        reference_solution=(
            "vector<int> twoSum(const vector<int>& nums, int target) {\n"
            "    unordered_map<int, int> seen;\n"
            "    for (int i = 0; i < nums.size(); ++i) {\n"
            "        int need = target - nums[i];\n"
            "        if (seen.count(need)) return {seen[need], i};\n"
            "        seen[nums[i]] = i;\n"
            "    }\n"
            "    return {};\n"
            "}"
        ),
    ),
    "max_word": CodingTask(
        key="max_word",
        title="找出出现次数最多的单词",
        difficulty="中等",
        prompt="给定一个 vector<string> words，返回出现次数最多的单词。如果有多个单词次数相同，返回最早达到最高次数的单词。",
        constraints=("1 <= words.size() <= 10^5", "1 <= words[i].length() <= 30", "words[i] 只包含小写英文字母"),
        example='mostCommonWord({"to", "be", "or", "to", "be", "to"})  // "to"',
        knowledge_points=("unordered_map 计数", "最大值维护", "遍历", "平局处理"),
        reference_solution=(
            "string mostCommonWord(const vector<string>& words) {\n"
            "    unordered_map<string, int> counts;\n"
            "    string best;\n"
            "    int bestCount = 0;\n"
            "    for (const string& word : words) {\n"
            "        counts[word]++;\n"
            "        if (counts[word] > bestCount) {\n"
            "            best = word;\n"
            "            bestCount = counts[word];\n"
            "        }\n"
            "    }\n"
            "    return best;\n"
            "}"
        ),
    ),
    "reverse_words": CodingTask(
        key="reverse_words",
        title="反转句子中的单词顺序",
        difficulty="入门",
        prompt="给定一个 string s，返回单词顺序反转后的字符串。单词之间可能有多个空格，结果中单词之间只保留一个空格。",
        constraints=("0 <= s.length() <= 10^5", "s 由英文字母和空格组成", "单词之间可能有多个连续空格"),
        example='reverseWords("  hello   cpp world  ")  // "world cpp hello"',
        knowledge_points=("stringstream", "vector", "反转", "字符串拼接"),
        reference_solution=(
            "string reverseWords(const string& s) {\n"
            "    stringstream ss(s);\n"
            "    vector<string> words;\n"
            "    string word;\n"
            "    while (ss >> word) words.push_back(word);\n"
            "    reverse(words.begin(), words.end());\n"
            "    string result;\n"
            "    for (int i = 0; i < words.size(); ++i) {\n"
            "        if (i > 0) result += \" \";\n"
            "        result += words[i];\n"
            "    }\n"
            "    return result;\n"
            "}"
        ),
    ),
    "binary_search": CodingTask(
        key="binary_search",
        title="二分查找目标值",
        difficulty="中等",
        prompt="给定一个升序 vector<int> nums 和目标值 target，返回 target 的下标。如果不存在，返回 -1。",
        constraints=("0 <= nums.size() <= 10^5", "-10^9 <= nums[i], target <= 10^9", "nums 按严格升序排列"),
        example="binarySearch({1, 3, 5, 7, 9}, 7)  // 3",
        knowledge_points=("二分查找", "左右边界", "循环条件", "时间复杂度"),
        reference_solution=(
            "int binarySearch(const vector<int>& nums, int target) {\n"
            "    int left = 0;\n"
            "    int right = nums.size() - 1;\n"
            "    while (left <= right) {\n"
            "        int mid = left + (right - left) / 2;\n"
            "        if (nums[mid] == target) return mid;\n"
            "        if (nums[mid] < target) left = mid + 1;\n"
            "        else right = mid - 1;\n"
            "    }\n"
            "    return -1;\n"
            "}"
        ),
    ),
    "merge_sorted": CodingTask(
        key="merge_sorted",
        title="合并两个有序数组",
        difficulty="中等",
        prompt="给定两个升序 vector<int> a 和 b，返回一个新的升序 vector<int>，包含两个数组中的所有元素。",
        constraints=("0 <= a.size(), b.size() <= 10^5", "-10^9 <= a[i], b[i] <= 10^9", "a 和 b 均按非降序排列"),
        example="mergeSorted({1, 3, 5}, {2, 4, 6})  // {1, 2, 3, 4, 5, 6}",
        knowledge_points=("双指针", "vector 合并", "剩余元素处理", "循环边界"),
        reference_solution=(
            "vector<int> mergeSorted(const vector<int>& a, const vector<int>& b) {\n"
            "    int i = 0, j = 0;\n"
            "    vector<int> result;\n"
            "    while (i < a.size() && j < b.size()) {\n"
            "        if (a[i] <= b[j]) result.push_back(a[i++]);\n"
            "        else result.push_back(b[j++]);\n"
            "    }\n"
            "    while (i < a.size()) result.push_back(a[i++]);\n"
            "    while (j < b.size()) result.push_back(b[j++]);\n"
            "    return result;\n"
            "}"
        ),
    ),
    "fibonacci": CodingTask(
        key="fibonacci",
        title="计算斐波那契数",
        difficulty="入门",
        prompt="实现函数 fib(int n)，返回第 n 个斐波那契数。规定 fib(0)=0，fib(1)=1。",
        constraints=("0 <= n <= 45", "返回值保证可以用 int 表示"),
        example="fib(6)  // 8",
        knowledge_points=("循环", "状态更新", "递推关系", "边界条件"),
        reference_solution=(
            "int fib(int n) {\n"
            "    if (n < 2) return n;\n"
            "    int prev = 0;\n"
            "    int curr = 1;\n"
            "    for (int i = 2; i <= n; ++i) {\n"
            "        int next = prev + curr;\n"
            "        prev = curr;\n"
            "        curr = next;\n"
            "    }\n"
            "    return curr;\n"
            "}"
        ),
    ),
    "flatten_list": CodingTask(
        key="flatten_list",
        title="展开嵌套整数列表",
        difficulty="进阶",
        prompt="给定一个嵌套整数列表 NestedInteger 结构，返回展开后的一维 vector<int>。教学时可以重点讲递归思想，不要求实现完整类。",
        constraints=("嵌套总整数个数 <= 10^5", "嵌套深度 <= 1000", "-10^9 <= 整数值 <= 10^9"),
        example="flatten({1, {2, {3, 4}}, 5})  // {1, 2, 3, 4, 5}",
        knowledge_points=("递归", "类型判断", "vector 拼接", "嵌套结构"),
        reference_solution=(
            "void dfs(const NestedInteger& item, vector<int>& result) {\n"
            "    if (item.isInteger()) {\n"
            "        result.push_back(item.getInteger());\n"
            "        return;\n"
            "    }\n"
            "    for (const NestedInteger& child : item.getList()) {\n"
            "        dfs(child, result);\n"
            "    }\n"
            "}\n\n"
            "vector<int> flatten(const vector<NestedInteger>& nested) {\n"
            "    vector<int> result;\n"
            "    for (const NestedInteger& item : nested) {\n"
            "        dfs(item, result);\n"
            "    }\n"
            "    return result;\n"
            "}"
        ),
    ),
}

def public_config() -> dict[str, list[dict[str, object]]]:
    """只返回浏览器渲染实验界面所需的字段。"""

    return {
        "personalities": [
            {
                "key": item.key,
                "name": item.name,
                "short_name": item.short_name,
                "description": item.description,
            }
            for item in PERSONALITIES.values()
        ],
        "tasks": [
            {
                "key": item.key,
                "title": item.title,
                "difficulty": item.difficulty,
                "prompt": item.prompt,
                "constraints": list(item.constraints),
                "example": item.example,
                "knowledge_points": list(item.knowledge_points),
                "reference_solution": item.reference_solution,
            }
            for item in TASKS.values()
        ],
    }
