SCHEMA_DESCRIPTION = """
Table: sales
Columns:
- date DATE: sale date
- week_day TEXT: day of week in English, e.g. Monday, Tuesday, Friday
- hour TEXT: sale time as HH:MM
- ticket_number TEXT: receipt/ticket identifier
- waiter TEXT: waiter or seller identifier
- product_name TEXT: product sold
- quantity FLOAT: number of units sold
- unitary_price NUMERIC: price per unit
- total NUMERIC: line total amount
""".strip()
