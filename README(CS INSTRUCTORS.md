# Y2-Summer26-Pair-Project
# Objective

During Labs 1-3, each of you built an AI agent using the Claude API. Your agent could complete a task through the terminal, but it worked independently and had no graphical interface.

By the end of Lab 6, your team should have a working multi-agent application with a fully functional backend and a frontend built using Bolt.

# Requirements

Your finished project should include:

- **One AI agent per team member.** Teams of two should build two collaborating agents. Teams of three should build three.
- **A clear responsibility for each agent.** Every agent should contribute something different to the overall product.
- **A deliverable for the user.** The user should receive something useful—not just text. Examples include a study plan, checklist, report, travel plan, exported document, or another useful result.
- **One working tool call.** a python function, e.g.: export to PDF/text, save a file, search past results, or generate a calendar-style output.
- **Relevant responses.** Your agents should react to the user's input and to information received from the other agents. Avoid generic responses that could fit every conversation.
- **Functional User Interface.** Your app has a well designed user interface created by Bolt.

## Milestone 1 — Design Before You Build

Before writing new code, design your product as a team.

Decide:

- What is the main idea of the web app?
- What responsibility does each agent have?
- How does the user move through the application from beginning to end?
- What is the final product?

**Next, get your idea approved by your instructors**

## Milestone 2 — System Prompts

Build a strong and precise System Prompt for each agent

Your system prompt should answer the following statements:

- WHO the agent is (name and role)
- WHAT it does (specific task)
- WHAT IT WILL NOT DO (clear boundaries)

> 💡 **Remember, Agents have a role and a goal.**

Update the system prompt so every response uses this exact format:

- [Summary]: one sentence repeating what the user asked
- [Response]: the main answer
- [Next Step]: one concrete action the user can take

## Milestone 3 — Build the Backend

Now begin implementing your complete backend, each agent on a different python file, you should have: app1.py and app2.py

By the end of this milestone, your team should have:

- every agent working independently
- all required tool calls functioning (python function that produces
- the complete workflow running successfully from the terminal

Do **not** use Bolt yet.

At this stage, everything should work without a graphical interface.

**Test: send a few messages and confirm the agent stays in role, follows the format, and gives a better answer on a hard question.**

Your file structure should look like this:

![](https://raw.githubusercontent.com/meet-projects/Y2-Summer26-Pairs/refs/heads/main/backend.png
)
### ✅ Backend Checklist

Before moving on, make sure every statement below is true.

- [ ] Every agent works correctly by itself.
- [ ] Every agent has a clear responsibility.
- [ ] Tool calls work reliably.
- [ ] The complete workflow runs from start to finish in the terminal.
- [ ] Every team member understands how the backend works.

Only after completing this checklist should you continue.

## Milestone 4 — Connect your agents together

In this milestone, you'll bring both agents into one app. Instead of running app1.py and app2.py separately, the user picks which agent they want to use when they run the program.

What this means: you write one new file (like main.py) that starts by asking the user a question, like:

"Which agent do you want to use?

1. Agent 1 — [does X]
2. Agent 2 — [does Y]"

Based on what the user picks, main.py calls that agent's function and runs it.

Steps:

- Turn each agent into a callable function. Instead of running app1.py and app2.py on their own, each file should have one function like run_agent(input) that returns a result. main.py will import both.
- Write the selection menu. In main.py, ask the user which agent they want (by number or name), and use their answer to decide which function to call.
- Run only the chosen agent. Once the user picks, main.py should call that agent's function, pass along whatever input it needs, and show the result — the other agent should not run.
- Make sure both options actually work. Test picking Agent 1, then restart and test picking Agent 2. Each should complete its task and produce a result on its own.
- Handle a bad input. If the user types something that isn't a valid option, the app should ask again instead of crashing.

> 💡 **Remember Test each agent through the menu one at a time. Confirm Agent 1 works through main.py before testing Agent 2.**

Your file structure should look like this:

![](https://raw.githubusercontent.com/meet-projects/Y2-Summer26-Pairs/refs/heads/main/combined-back.png
)

### Connection Checklist

- [ ] Running main.py shows a clear menu asking which agent to use.
- [ ] Picking Agent 1 runs only Agent 1 and gives a correct result.
- [ ] Picking Agent 2 runs only Agent 2 and gives a correct result.
- [ ] Invalid input doesn't crash the app.
- [ ] Both partners understand how main.py picks and runs the chosen agent.

Once every box is checked, you're ready to build the Bolt frontend.

## Milestone 5 — Building the face

Now it's time to turn your working backend into a real app using Bolt.

Write one detailed prompt for Bolt that explains:

- What your app does and the problem it solves
- What each agent does (its specific job)
- How you want the app to look and the features of it:
  - A tab and chat page for each agent
  - A loading indicator while the agent is thinking
  - A send button
  - A chat bar, etc...


Since you already have 3 Python files (your agents), you can import your GitHub repository directly into Bolt. This lets Bolt read and use your existing backend code to build the app around it, instead of writing the backend from scratch.

Copy this and include it in your prompts:

```
"Update the Anthropic client initialization to read the base URL from the environment:
`new Anthropic({ apiKey, baseURL: process.env.ANTHROPIC_BASE_URL })`. Then add `ANTHROPIC_API_KEY=your-key-here`
and `ANTHROPIC_BASE_URL=your-base-url` to the environment variables."
```

- Next, in the Bolt editor, find the `.env` file or the environment variables section.
- Then in Bolt's env panel, set both:
  ```
  ANTHROPIC_API_KEY=your-key-here
  ANTHROPIC_BASE_URL=your-base-url
  ```

> 💡 **Remember what we talked about in our previous sessions about clarity, feedback, and focus? Make sure to keep those in mind when prompting!**

![](https://raw.githubusercontent.com/meet-projects/Y2-Summer26-Pairs/refs/heads/main/bolt_import_github.png)

## Milestone 6 — Test and Improve

Test your complete application like a real user.

Try different inputs, including unexpected ones.

When you find a problem, fix one issue at a time and test again.

Continue improving your prompts, backend, and frontend until the entire system works reliably.

Once you reach this stage, deploy your web app: click on the publish button in Bolt so your project goes live!

