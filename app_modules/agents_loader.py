"""
Agent initialization and loading
"""

# Import Form1dat2 agent for shape catalog integration
try:
    from agents.llm_agents.format1_agent.form1dat2 import Form1Dat2Agent
    form1dat2_agent = Form1Dat2Agent()
except ImportError:
    form1dat2_agent = None

# Import Form1OCR3 Rib-OCR agent for mapping catalog letters to drawings
try:
    from agents.llm_agents.format1_agent.form1ocr3_ribocr import create_form1ocr2_agent
    form1ocr3_agent = create_form1ocr2_agent()
except ImportError:
    form1ocr3_agent = None

# Commented out agents - can be enabled as needed:
# from agents.llm_agents.orderheader_agent import OrderHeaderAgent
# from agents.llm_agents.format1_agent.form1dat1 import Form1Dat1Agent
# from agents.llm_agents.format1_agent.use_area_table import UseAreaTableAgent
# from data.json_database import IronDrawingJSONDatabase

# orderheader_agent = OrderHeaderAgent()
# form1dat1_agent = Form1Dat1Agent()
# use_area_table_agent = UseAreaTableAgent()