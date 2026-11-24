import os
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Add references
from agent_framework import tool, Agent
from agent_framework.foundry import FoundryChatClient
from azure.identity import AzureCliCredential
from pydantic import Field
from typing import Annotated

load_dotenv()

async def main():
    # Clear the console
    os.system('cls' if os.name=='nt' else 'clear')

    # Load the expnses data file
    script_dir = Path(__file__).parent
    file_path = script_dir / 'data.txt'
    with file_path.open('r') as file:
        data = file.read() + "\n"

    # Ask for a prompt
    user_prompt = input(f"Here is the expenses data in your file:\n\n{data}\n\nWhat would you like me to do with it?\n\n")
    
    # Run the async agent code
    await process_expenses_data(user_prompt, data)
    
async def process_expenses_data(prompt, expenses_data):

    # Create a foundry chat client
    client = FoundryChatClient(
        project_endpoint=os.getenv("PROJECT_ENDPOINT"),
        model=os.getenv("MODEL_DEPLOYMENT_NAME"),
        credential=AzureCliCredential()
    )
    # expenses@contoso.com
    # Initialize an agent with the tool and instructions
    async with (
        Agent(
            client=client,
            name="ExpenseClaimAgent",
            instructions="""You are an AI assistant for expense claim submission.
                        At the user's request, create an expense claim and use the plug-in function to send an email to satishkurula073@gmail.com with the subject 'Expense Claim`and a body that contains itemized expenses with a total.
                        Then confirm to the user that you've done so. Don't ask for any more information from the user, just use the data provided to create the email.""",
            tools=[submit_claim],
        ) as agent,
    ):

        # Use the agent to process the expenses data   
        try:
            # Add the input prompt to a list of messages to be submitted
            prompt_messages = [f"{prompt}: {expenses_data}"]
            # Invoke the agent for the specified thread with the messages
            response = await agent.run(prompt_messages)
            # Display the response
            print(f"\n# Agent:\n{response}")
        except Exception as e:
            # Something went wrong
            print (e)


# Create a tool function for the email functionality
# @tool(approval_mode="never_require")
# def submit_claim(
#     to: Annotated[str, Field(description="Who to send the email to")],
#     subject: Annotated[str, Field(description="The subject of the email.")],
#     body: Annotated[str, Field(description="The text body of the email.")]):
#         print("\nTo:", to)
#         print("Subject:", subject)
#         print(body, "\n")

import smtplib
from email.message import EmailMessage
import os
from pydantic import Field
# from typing import Annotated
# from agent_framework import tool

# Create a tool function for the email functionality
@tool(approval_mode="never_require")
def submit_claim(
    to: Annotated[str, Field(description="Who to send the email to")],
    subject: Annotated[str, Field(description="The subject of the email.")],
    body: Annotated[str, Field(description="The text body of the email.")]
):
    # Fetch email credentials from your .env file
    sender_email = os.getenv("SENDER_EMAIL")
    sender_password = os.getenv("SENDER_PASSWORD") 
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", 587))

    if not sender_email or not sender_password:
        error_msg = "Email credentials missing in .env file. Cannot send real email."
        print(f"\n{error_msg}")
        return error_msg

    # Construct the email message
    msg = EmailMessage()
    msg.set_content(body)
    msg['Subject'] = subject
    msg['From'] = sender_email
    msg['To'] = to

    try:
        # Connect to the SMTP server and send the email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()  # Secure the connection
            server.login(sender_email, sender_password)
            server.send_message(msg)
        
        success_msg = f"Successfully sent real email to {to}."
        print(f"\n{success_msg}")
        return success_msg
        
    except Exception as e:
        error_msg = f"Failed to send email: {str(e)}"
        print(f"\n{error_msg}")
        return error_msg

if __name__ == "__main__":
    asyncio.run(main())
