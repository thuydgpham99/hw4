# AI Prompts Log

This file logs the prompts used to build each problem in this assignment (Campus Customs customer website + chatbot). One section per problem. Each section includes:

1. The problem number and title
2. At least one prompt I typed
3. A follow-up prompt (if one was needed), with one sentence on what was lacking after the first

Grading basis: this assignment is evaluated on (a) what's logged in this file and (b) the running site, database writes, and screenshots as evidence that each problem's work actually ran and completed. No separate proof write-up is required beyond these prompts.

Prompts are recorded verbatim as typed.

---

## Setup: Assignment background

**Prompt 1:**
> ok this is the background from this hw, campus customs needs a real customer website with a helpful chatbot. you will build a React + Vite TypeScript front end and a Python FasAPI backedn whose brain is a PydanticAI agent. shoppers should be able to browse products, create an account, chat about merch, see matching items appear on the page and get honest answers about price and stock from local database. in folder 4, there is campys_customs.db with tables for the product catalogue, inventory by size, and users (with hashed passwords). product image file paths are in the catalogue table. research yalebulldogblue.com to learn the style of the campus customs page and information for your agent prompts. you will use PORTKEY_API_KEY or whaterver API key you have for your agent's AI calls. moreover, you will work 1 problem at a time. my grade will be based on in the end, you will push your project to a public GitHub repo and submit the repo URL on canvas. do NOT commit the database or prodcut images. in the 2 files in HW4: one is data/campus_customs.db - SQLite database with tables catalogue, inventory and users (one test user is already there) and the other is data/products/ - product images ; paths match the catalogue table

**Follow-up:**
> do i have the API portkey?

What was lacking after the first prompt: the background named `PORTKEY_API_KEY` as the key to use but did not confirm that a working key actually existed on this machine, so a follow-up was needed to locate it and verify it with a live API call before any agent code was written.

---

## Problem 1: Vibe coder prompts

**Prompt 1:**
> Now we start with problem 1: vibe coder prompts. You need to create AI_prompts.md at the start of the assignment and keep it updated as you work. This file is the log of what I typed to you. Moreover, you need to put 1 section for each problem. Each section must include: 1. The problem number and title. 2. At least 1 prompt I typed. 3. One follow-up prompt if I needed it (and 1 sentence on what was lacking after the first). Keep in mind that my running site, database writes and screenshots are the evidence, you do not need an extra proof essay beyond these prompts.

**Follow-up:**
> remember to update it as last time you didnt

What was lacking after the first prompt: the first prompt created the log and its structure but did not make continuous upkeep an enforced habit — in HW 3 the log drifted behind the actual work — so a follow-up was needed to establish that this file gets updated as part of every problem, not reconstructed at the end.

---

## Problem 2: Analyze the database

**Prompt 1:**
> Problem 2: analyze the database. In this problem. You look at the database data/campus_customs.db and understand the fields of each table. at the min, you need to understand catalogue, inventory, and users. Then you start the file output/harness.md. write down each table and its fields, and one short line on why each field matters for the shop or the chatbot. You will keep growing this harness file in later problems (models, tools, safety, specs).

**Follow-up:** _None yet._

---

## Problem 3: Build the Campus Customs website

**Prompt 1:**
> Problem 3: build the campus customs website. In this problem, scaffold a React + Vite + TypeScript front end for Campus Customs. Put a nav bar at the top that links to the main pages. 1. Home, 2. Products, 3. About us, 4. Log in, 5. Create account/ pull campus customs-style wording from yalebulldogblue.com for Home and About Us, but write these pages in your own voice (do NOT copy the original site text). Then on the Products page, show product images from the catalogue (use the image paths in the database) with basic product info (name, price, short description). Make each product open a single-item page (large image on one side, full product text on the other – description, price, size/stock when you have them). Clicking a cad on Products should take the shopper there. Add a chat interface in the bottom right of the site (a floating chat panel is fine). It does not need to talk to an agent yet – a stub that will call your backend later is enough for this problem). You will need a small API soon to read the database. It is fine to start a simple FastAPI app in backend/main.py just to serve products and images, then grow it into the agent backend in Problem 5.

**Follow-up:**
> are you good to move the prob 4 or anything else need to be run?

What was lacking after the first prompt: the first prompt built the site but did not ask for a state check afterwards, so a follow-up was needed to confirm both servers were still up, the build was still clean, and nothing was left half-finished before starting the next problem.

---

## Problem 4: Create account and login

**Prompt 1:**
> Problem 4: create account and login. In this problem you will build a normal create-account / login flow. 1. Create account: first name, last name, email, password (confirm password is a nice touch). 2. Log in: email and password. New accounts go into the users table. make sure to store password securely to hackers (human or AI) cannot access them. The seed database already has a test user you can use while building. 1. Email: test@campuscustoms.yale.edu 2. Password: password. Confirm you can log in as that user, and that a brand-new account you create also works. Update output/harness.md with how auth words (what you store for a user and how passwords are protected).

**Follow-up:** _None yet._

---

## Problem 5: PydanticAI agent backend

**Prompt 1:**
> ok good job, now move to prob 5: Problem 5: PydanticAI agent backend. You need to build the shop chatbot as PydanticAI agent behind FastAPI, plugged into your front end chat widget. Put the API app in backend/main.py – that is the file you run with Uvicorn. Keep the agent as these four files next to it (same idea as homework 3). 1. Backend/prompts/prompt.md – system prompt (grow this same file later). 2. Backend/agent.py – agent entry / wiring. 3. Backend/tools.py – tools the agent can call. 4. Backend/models.py – Pydantic / Pydantic AI structured types. In main.py, expose a chat route so a message from the website returns a reply from the agent (and whatever else you need for products/auth). You will need your AI model API key for the agent. The put campus customs voice and safety basics into prompts/prompt.md (you will expand tools and safety later). Start or update types in models.py for chat replies / product cards as needed. In output/harness.md, note how the front end talks for FastAPI and how the agent is loaded (prompt file + model). Make sure the backend runs from the backend/folder like this: uvicorn main:app --reload --port 8000

**Follow-up:**
> you should fix the bug

What was lacking after the first prompt: the first pass reported the port-8000 conflict as a known limitation and ran the backend on 8010 instead, rather than re-checking whether the blocking process was still alive — it had already exited, so a follow-up was needed to actually run it on the specified port.

---

## Problem 6: Tools — product info and stock

**Prompt 1:**
> yes, do it then move to Problem 6: Tools: product info and stock. You need to give the agent tools that look up real information from campus_customs.db: 1. Product description, 2. Price, 3. How many are in stock (by size when the customer asks). The agent must use the database – it should not invent prices or quantities. If a size is out of stock, say so clearly. Expand prompts/prompt.md so the agent knows to call these tools for price and stock questions. Add or update return types in models.py. in output/harness.md, list each tool and explain which model fields you chose for lookup results and why. you need to work faster, max 5 mins per problem

**Follow-up:** _None yet._

---

## Problem 7: Chat search that updates the page

**Prompt 1:**
> Problem 7: chat search that updates the page. Now we will add a neat feature to the site. When a customer asks about a type of item – for example "what hoodies do you have" – the agent should search the catalogue and the website should dynamically show those matching items as product cards (image, name, price, short info). This is an API contract: the agent returns structured product matches and then the front end renders them on the website. It looks really cool. After the dynamic product cards are loaded by your new feature, make sure the same single-item page behaviour you built in problem 3 still works: each product card – including the ones the chat just put on the page – should still open that detail view (large image + full info) when clicked. Update prompts/prompt.md and output/harness.md so it is clear how search results reach the page. max 5 mins

**Follow-up:** _None yet._

---

## Problem 8: Customer memory

**Prompt 1:**
> fix the probkem then move to Problem 8: customer memory: when a shopper is logged in, save their chat history in the database in an appropriate table and reload it when they return. The agent should know WHO is chatting (name, email) – put that in agent deps (or an equivalent clear pattern) and/or tolls the agent can call. Also pass enough page context that if someone is on a product page and asks "do you have this in pink" the agent knows which item they meant. Hint: you can put code into the agent context. Guests can still chat, but history only needs to persist for logged-in users. Document in output/harness.md: how user chat history is stored, what customer fields the agent sees and how page context is passed. max 5 mis

**Follow-up:** _None yet._

---

## Problem 9: Usability improvements

**Prompt 1:**
> fix the bug and move to Problem 9: usability improvements. Now that the core shop works, improve it. Choose and implement: 1. 2 front-end usability improvements. 2. 2 agent/backend usability improvements. Front-end improvements are things that make the site look better and make it easier to use. Agent / backend improvements are things that make the agent output better, more accurate, or safer. These could be new agent tools or things that make the agent run faster or cheaper. Write output/usability.md BEFORE OR AS you build. For each of the improvements, say: 1. What you added, 2. Why it helps a campus customs shopper or the business. Then make sure all improvements actually show up in the running app. Graders will read the write-up and look for the features. Therefore, need to make sure this part is done properly so I will have the full grade.

**Follow-up:** _None yet._

---

## Problem 10: Style the website

**Prompt 1:**
> Problem 10: style the website. Add creative design so the site feels like a real campus customs storefront – fonts, color, hierarchy, motion, product presentation, chat feel. I will get more points for imaginative and innovative design so be CREATIVE!!! Write output/design.md: what you changed and why it should help customers stick around and buy. Keep it concrete and short.

**Follow-up:** _None yet._

---
