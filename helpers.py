import csv

def export_table_to_csv(table, filename):
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        headers = []
        for col in range(table.columnCount()):
            headers.append(table.horizontalHeaderItem(col).text())
        writer.writerow(headers)
        for row in range(table.rowCount()):
            row_data = []
            for col in range(table.columnCount()):
                item = table.item(row, col)
                row_data.append(item.text() if item else '')
            writer.writerow(row_data)