import json
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from assessments.models import CodingChallenge, CodingTestCase

CHALLENGES = [
    {
        'title': 'Two Sum',
        'difficulty': 'Easy',
        'category': 'Arrays',
        'function_name': 'two_sum',
        'xp_reward': 50,
        'description': """### Description
Given an array of integers `nums` and an integer `target`, return **indices** of the two numbers such that they add up to `target`.

You may assume that each input would have **exactly one solution**, and you may not use the same element twice. You can return the answer in any order.

#### Example 1:
```text
Input: nums = [2, 7, 11, 15], target = 9
Output: [0, 1]
Explanation: Because nums[0] + nums[1] == 9, we return [0, 1].
```

#### Example 2:
```text
Input: nums = [3, 2, 4], target = 6
Output: [1, 2]
```
""",
        'constraints': "2 <= nums.length <= 10^4\n-10^9 <= nums[i] <= 10^9\n-10^9 <= target <= 10^9\nOnly one valid answer exists.",
        'hints': "Can you iterate through the list while storing seen numbers in a dictionary/hash map for O(1) complement lookup?\nRemember complement = target - num.",
        'python_starter': """def two_sum(nums, target):
    # TODO: Implement O(n) solution using hash map
    seen = {}
    for i, num in enumerate(nums):
        diff = target - num
        if diff in seen:
            return [seen[diff], i]
        seen[num] = i
    return []
""",
        'javascript_starter': """function twoSum(nums, target) {
    const map = new Map();
    for (let i = 0; i < nums.length; i++) {
        const diff = target - nums[i];
        if (map.has(diff)) {
            return [map.get(diff), i];
        }
        map.set(nums[i], i);
    }
    return [];
}
""",
        'test_cases': [
            {'input': [[2, 7, 11, 15], 9], 'output': [0, 1], 'hidden': False, 'order': 1},
            {'input': [[3, 2, 4], 6], 'output': [1, 2], 'hidden': False, 'order': 2},
            {'input': [[3, 3], 6], 'output': [0, 1], 'hidden': False, 'order': 3},
            {'input': [[-1, -2, -3, -4, -5], -8], 'output': [2, 4], 'hidden': True, 'order': 4},
            {'input': [[1, 5, 8, 12, 19, 23], 31], 'output': [3, 4], 'hidden': True, 'order': 5},
            {'input': [[0, 4, 3, 0], 0], 'output': [0, 3], 'hidden': True, 'order': 6},
        ]
    },
    {
        'title': 'Valid Parentheses',
        'difficulty': 'Easy',
        'category': 'Stack',
        'function_name': 'is_valid',
        'xp_reward': 50,
        'description': """### Description
Given a string `s` containing just the characters `'('`, `')'`, `'{'`, `'}'`, `'['` and `']'`, determine if the input string is valid.

An input string is valid if:
1. Open brackets must be closed by the same type of brackets.
2. Open brackets must be closed in the correct order.
3. Every close bracket has a corresponding open bracket of the same type.

#### Example 1:
```text
Input: s = "()"
Output: true
```

#### Example 2:
```text
Input: s = "()[]{}"
Output: true
```

#### Example 3:
```text
Input: s = "(]"
Output: false
```
""",
        'constraints': "1 <= s.length <= 10^4\ns consists of parentheses only '()[]{}'.",
        'hints': "Use a stack! Push opening brackets, and when encountering a closing bracket, check if it matches the top of the stack.",
        'python_starter': """def is_valid(s):
    # TODO: Implement stack-based bracket validation
    stack = []
    mapping = {')': '(', '}': '{', ']': '['}
    for char in s:
        if char in mapping:
            top = stack.pop() if stack else '#'
            if mapping[char] != top:
                return False
        else:
            stack.append(char)
    return not stack
""",
        'javascript_starter': """function isValid(s) {
    const stack = [];
    const map = { ')': '(', '}': '{', ']': '[' };
    for (const char of s) {
        if (map[char]) {
            const top = stack.length ? stack.pop() : '#';
            if (map[char] !== top) return false;
        } else {
            stack.push(char);
        }
    }
    return stack.length === 0;
}
""",
        'test_cases': [
            {'input': ["()"], 'output': True, 'hidden': False, 'order': 1},
            {'input': ["()[]{}"], 'output': True, 'hidden': False, 'order': 2},
            {'input': ["(]"], 'output': False, 'hidden': False, 'order': 3},
            {'input': ["([{}])"], 'output': True, 'hidden': True, 'order': 4},
            {'input': ["[(])"], 'output': False, 'hidden': True, 'order': 5},
            {'input': ["]"], 'output': False, 'hidden': True, 'order': 6},
        ]
    },
    {
        'title': 'Best Time to Buy and Sell Stock',
        'difficulty': 'Easy',
        'category': 'Two_Pointers',
        'function_name': 'max_profit',
        'xp_reward': 60,
        'description': """### Description
You are given an array `prices` where `prices[i]` is the price of a given stock on the `i-th` day.

You want to maximize your profit by choosing a **single day** to buy one stock and choosing a **different day in the future** to sell that stock.

Return the **maximum profit** you can achieve from this transaction. If you cannot achieve any profit, return `0`.

#### Example 1:
```text
Input: prices = [7, 1, 5, 3, 6, 4]
Output: 5
Explanation: Buy on day 2 (price = 1) and sell on day 5 (price = 6), profit = 6 - 1 = 5.
```
""",
        'constraints': "1 <= prices.length <= 10^5\n0 <= prices[i] <= 10^4",
        'hints': "Track the minimum price seen so far and update max profit at each step.",
        'python_starter': """def max_profit(prices):
    # Track min price and max profit in one pass
    min_price = float('inf')
    max_p = 0
    for price in prices:
        if price < min_price:
            min_price = price
        elif price - min_price > max_p:
            max_p = price - min_price
    return max_p
""",
        'javascript_starter': """function maxProfit(prices) {
    let minPrice = Infinity;
    let maxProfit = 0;
    for (const price of prices) {
        if (price < minPrice) {
            minPrice = price;
        } else if (price - minPrice > maxProfit) {
            maxProfit = price - minPrice;
        }
    }
    return maxProfit;
}
""",
        'test_cases': [
            {'input': [[7, 1, 5, 3, 6, 4]], 'output': 5, 'hidden': False, 'order': 1},
            {'input': [[7, 6, 4, 3, 1]], 'output': 0, 'hidden': False, 'order': 2},
            {'input': [[2, 4, 1]], 'output': 2, 'hidden': True, 'order': 3},
            {'input': [[1, 2, 3, 4, 5]], 'output': 4, 'hidden': True, 'order': 4},
        ]
    },
    {
        'title': 'Maximum Subarray',
        'difficulty': 'Medium',
        'category': 'DP',
        'function_name': 'max_sub_array',
        'xp_reward': 100,
        'description': """### Description
Given an integer array `nums`, find the subarray with the largest sum, and return *its sum*.

#### Example 1:
```text
Input: nums = [-2, 1, -3, 4, -1, 2, 1, -5, 4]
Output: 6
Explanation: The subarray [4, -1, 2, 1] has the largest sum 6.
```

#### Example 2:
```text
Input: nums = [1]
Output: 1
```
""",
        'constraints': "1 <= nums.length <= 10^5\n-10^4 <= nums[i] <= 10^4",
        'hints': "Kadane's Algorithm: at each index, decide whether to add nums[i] to the running current sum or start a fresh subarray at nums[i].",
        'python_starter': """def max_sub_array(nums):
    # Kadane's algorithm: O(n) time, O(1) space
    current_sum = max_sum = nums[0]
    for num in nums[1:]:
        current_sum = max(num, current_sum + num)
        max_sum = max(max_sum, current_sum)
    return max_sum
""",
        'javascript_starter': """function maxSubArray(nums) {
    let currentSum = nums[0];
    let maxSum = nums[0];
    for (let i = 1; i < nums.length; i++) {
        currentSum = Math.max(nums[i], currentSum + nums[i]);
        maxSum = Math.max(maxSum, currentSum);
    }
    return maxSum;
}
""",
        'test_cases': [
            {'input': [[-2, 1, -3, 4, -1, 2, 1, -5, 4]], 'output': 6, 'hidden': False, 'order': 1},
            {'input': [[1]], 'output': 1, 'hidden': False, 'order': 2},
            {'input': [[5, 4, -1, 7, 8]], 'output': 23, 'hidden': False, 'order': 3},
            {'input': [[-1, -2, -3]], 'output': -1, 'hidden': True, 'order': 4},
            {'input': [[-2, -1]], 'output': -1, 'hidden': True, 'order': 5},
        ]
    },
    {
        'title': 'Binary Search',
        'difficulty': 'Easy',
        'category': 'Binary_Search',
        'function_name': 'search',
        'xp_reward': 50,
        'description': """### Description
Given an array of integers `nums` which is sorted in ascending order, and an integer `target`, write a function to search `target` in `nums`. If `target` exists, then return its index. Otherwise, return `-1`.

You must write an algorithm with `O(log n)` runtime complexity.

#### Example 1:
```text
Input: nums = [-1, 0, 3, 5, 9, 12], target = 9
Output: 4
```

#### Example 2:
```text
Input: nums = [-1, 0, 3, 5, 9, 12], target = 2
Output: -1
```
""",
        'constraints': "1 <= nums.length <= 10^4\n-10^4 < nums[i], target < 10^4\nAll the integers in nums are unique.\nnums is sorted in ascending order.",
        'hints': "Maintain left and right pointers. Compute mid = left + (right - left) // 2 to avoid overflow.",
        'python_starter': """def search(nums, target):
    left, right = 0, len(nums) - 1
    while left <= right:
        mid = (left + right) // 2
        if nums[mid] == target:
            return mid
        elif nums[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    return -1
""",
        'javascript_starter': """function search(nums, target) {
    let left = 0, right = nums.length - 1;
    while (left <= right) {
        const mid = Math.floor((left + right) / 2);
        if (nums[mid] === target) return mid;
        if (nums[mid] < target) left = mid + 1;
        else right = mid - 1;
    }
    return -1;
}
""",
        'test_cases': [
            {'input': [[-1, 0, 3, 5, 9, 12], 9], 'output': 4, 'hidden': False, 'order': 1},
            {'input': [[-1, 0, 3, 5, 9, 12], 2], 'output': -1, 'hidden': False, 'order': 2},
            {'input': [[5], 5], 'output': 0, 'hidden': True, 'order': 3},
            {'input': [[2, 5], 0], 'output': -1, 'hidden': True, 'order': 4},
            {'input': [[1, 3, 5, 7, 9, 11, 13, 15, 17, 19], 19], 'output': 9, 'hidden': True, 'order': 5},
        ]
    }
]

class Command(BaseCommand):
    help = 'Seeds initial FAANG coding challenges and test suites'

    def handle(self, *args, **options):
        self.stdout.write("Seeding coding challenges...")
        count = 0
        for item in CHALLENGES:
            slug = slugify(item['title'])
            challenge, created = CodingChallenge.objects.update_or_create(
                slug=slug,
                defaults={
                    'title': item['title'],
                    'difficulty': item['difficulty'],
                    'category': item['category'],
                    'function_name': item['function_name'],
                    'xp_reward': item['xp_reward'],
                    'description': item['description'],
                    'constraints': item['constraints'],
                    'hints': item['hints'],
                    'python_starter': item['python_starter'],
                    'javascript_starter': item['javascript_starter'],
                    'is_active': True,
                }
            )

            # Clear old test cases and insert
            challenge.test_cases.all().delete()
            for tc in item['test_cases']:
                CodingTestCase.objects.create(
                    challenge=challenge,
                    input_data=json.dumps(tc['input']),
                    expected_output=json.dumps(tc['output']),
                    is_hidden=tc['hidden'],
                    order=tc['order']
                )
            count += 1
            action = "Created" if created else "Updated"
            self.stdout.write(self.style.SUCCESS(f"{action} challenge: {challenge.title} with {len(item['test_cases'])} test cases"))

        self.stdout.write(self.style.SUCCESS(f"Successfully seeded {count} challenges!"))
