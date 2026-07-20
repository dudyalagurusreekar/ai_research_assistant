from smolagents import Tool
from datetime import datetime


class DateTimeTool(Tool):

    name = "datetime"

    description = (
        "Use this tool whenever the user asks for the "
        "current date, time, today's day, timestamp, "
        "or current local date and time."
    )

    inputs = {}

    output_type = "string"

    def forward(self):

        now = datetime.now()

        return (
            f"Date      : {now.strftime('%d-%m-%Y')}\n"
            f"Time      : {now.strftime('%I:%M:%S %p')}\n"
            f"Day       : {now.strftime('%A')}\n"
            f"Timestamp : {now.isoformat()}"
        )