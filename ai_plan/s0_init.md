 can you help setup project, read @docs/brief-init.md the goal is email turn emails into structured prioritised data.
  Create a plan in @ai_plan/s1_app_init.

  What i need is to implement demo of email omes into output calendar, PowerAutomate has automation sends API request with output email contents including attachments to app in this container container with api running that is this project. Agent that is llm with tools reads email with attachment (e.g. pdf) convert to .md (save all made documents backend for evaluation)  that can turn email into structure and prioritised data. Because structure and prioritised is loosely definited proposed make it a pydantic model that is configurable so it can be updated over time.

  This needs to be a docker container deployed on Azure stack. but lets start with the goal of this plan is to stand up version 1 of a docker container fastapi app, that received a post request from PowerAutomate with outlook email.

  You need to do research to solve this looking into:
  * pydantic for data models https://github.com/pydantic/pydantic
  * fastapi for app https://github.com/fastapi/fastapi
  * docker for deployment
  * microsoft markitdown to convert pdf https://github.com/microsoft/markitdown


  The API needs to output a JSON list of tasks with priority to it will be [{email:'asdf','taskid':1, 'category':'', 'summary':'', 'priority':''}] or whatever better solution you come up with and a email can have multiple tasks and priorities where the summary is a summary of the task.

  Outputs, every requests should save the incoming email request and all the interim steps the app made like if it converting pdf to md and a reasoning output from every LLM call and tracking for entire LLM. What is a good tracking app for a docker container app deployed on azure, MLFlow?.

   I need to be able to step through every time this agent is invoked through LLM to inspect all steps to be able to evaluate and improve.