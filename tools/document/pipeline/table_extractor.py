"""TableExtractorStep for formatting extracted tables into CSV and JSON representations."""

import json
import csv
import io
from tools.document.interfaces.pipeline import IPipelineStep
from tools.document.models.document import NormalizedDocument
from tools.document.models.context import ProcessingContext


class TableExtractorStep(IPipelineStep):
    """Pipeline step formatting extracted tables into structured CSV and JSON outputs."""

    @property
    def name(self) -> str:
        return "TableExtractorStep"

    async def process(
        self,
        document: NormalizedDocument,
        context: ProcessingContext,
    ) -> NormalizedDocument:
        if not context.config.enable_table_extraction or not document.tables:
            return document

        for table in document.tables:
            # Build matrix if missing
            if not table.matrix and (table.headers or table.rows):
                matrix = []
                if table.headers:
                    matrix.append(table.headers)
                matrix.extend(table.rows)
                table.matrix = matrix

            # Build CSV representation
            if not table.csv_content and table.matrix:
                output = io.StringIO()
                writer = csv.writer(output)
                writer.writerows(table.matrix)
                table.csv_content = output.getvalue()

            # Build JSON representation
            if not table.json_content and (table.headers and table.rows):
                dict_rows = [dict(zip(table.headers, row)) for row in table.rows]
                table.json_content = json.dumps(dict_rows, indent=2)

        return document
