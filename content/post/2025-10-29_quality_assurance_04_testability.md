---
layout:		 single
title:       "Quality Assurance 04 Testability"
subtitle:    ""
description: " "
date:        2025-10-29T22:01:28-05:00
author: LiYixian
image:       ""
tags:        ["cs", "quality assurance"]
categories:  ["Tech" ]
URL: "2025/10/quality-assurance-04/"
math: False
---

### What is Testability?

>  Testability is the extent to which a system’s behaviors can be exercised, observed, and reasoned about with fast, reliable tests.

- Controllability
	- steer the system under test into any path or behavior
	- How difficult is it to put the system into a particular state? How to write a test that covers that behavior?
- Observability
	- directly observe behaviors and check outcomes
	- How hard is it to determine if the system behaved as intended? Can we check that the system didn’t misbehave?
- Isolation
	- exercise the component under test without exercising the rest of the system
- Stability
	- produce the same test result across runs
	- Is the result independent of time, randomness, order, and load?

### Writing Testable Code

| Testability Inhibitors             | Phenomenon                                                   | Refactor                                                     |
| ---------------------------------- | ------------------------------------------------------------ | ------------------------------------------------------------ |
| Hidden Dependencies                | - Environment Variables<br>- Platform path rules<br>- Current working directory<br>- Ports and permissions<br>- Time zone / locale (machine dependent date handling)<br>- Machine sizing (CPU count) affecting behavior<br>- Filesystem permissions and layout | Make dependencies explicit via configuration                 |
| Poor Isolation                     | - Hardwired collaborators (direct instantations / static methods / singletons / service locators)<br>- Deep method chains | Dependency Injection                                         |
| Busy Constructors                  | - Side Effects (e.g., IO, timers, network, background jobs)<br>- Contain complex logic | Move logic out of the constructor                            |
| Non-Determinism                    | - Hidden clock (date / time)<br>- Randomness<br>- External API calls<br>- Networking<br>- Parallelism<br>- Race condition (no await) | Add deterministic seams via dependency injection             |
| Poor Observability                 | - Void functions with difficult to observe side effects<br>- Ambiguous returns (e.g., true/false → what succeeded or failed?)<br>- Hidden state (e.g., private state without getters) | Provide read access to important internal state;<br>Consider using informative return types;<br>Add observability hooks to avoid test doubles |
| Shared Mutable State               | - Globals, statics, singletons<br>- Mutable configurations<br>- Process-wide settings<br>- Exposed internals | Try to avoid shared mutable state                            |
| External Libraries and Legacy Code | - Application talks directly to external libraries or external code | Wrap external libraries and legacy code in wrappers and test via dependency injection |
| Too Much Responsibility            | - One class/function does orchestration, domain logic and I/O | Split into functions with a single responsibility            |

### Writing Good Test Code

Test code should be ...

- Simple: minimal logic; clear Arrange–Act–Assert.
- Readable: names tell the story; intent over mechanics.
- Maintainable: low coupling; stable helpers; clear failure messages
- DRY (not redundant): share setup wisely without hiding intent.
- Deterministic: controls time, randomness, and concurrency.
- Fast: no real I/O or sleeps; runs in milliseconds.
- Focused: verifies one behavior so failures point to a single cause.
	- Use table-driven testing for multiple inputs
- Independent: order-agnostic; no shared state; dependencies faked.
