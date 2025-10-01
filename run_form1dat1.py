#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.llm_agents.format1_agent.form1dat1 import Form1Dat1Agent

def main():
    # Initialize the agent
    agent = Form1Dat1Agent()

    # Process the order - this will delete existing file and recreate from scratch
    order_number = "CO25S006375"
    result = agent.process_order(order_number)

    print(f"Result: {result}")

if __name__ == "__main__":
    main()