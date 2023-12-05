import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem
import pymysql

class DatabaseDisplayApp(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Database Display")
        self.layout = QVBoxLayout()

        self.setGeometry(100, 100, 500, 200)  # Set the window size (width x height)

        # Results display with an expanded table
        self.result_table = QTableWidget()
        # self.result_table.setRowCount(500)  # Increase row count
        # self.result_table.setColumnCount(10)  # Increase column count
        self.result_table.horizontalHeader().setStretchLastSection(True)

        self.result_table.horizontalHeader().setDefaultSectionSize(150)  # Set column width
        self.result_table.verticalHeader().setDefaultSectionSize(40)  # Set row height


        # Add table widget to the layout
        self.layout.addWidget(self.result_table)
        self.setLayout(self.layout)

        self.display_database_contents()

    def display_database_contents(self):
        try:
            conn = pymysql.connect(
                host='192.168.0.70',
                user='ubuntu',
                password='1q2w3e4r',
                database='brand'
            )
            
            cursor = conn.cursor()
            query = "SELECT * FROM type"
            cursor.execute(query)
            
            data = cursor.fetchall()
            
            if not data:
                return  # No data found
            
            self.result_table.setRowCount(len(data))
            self.result_table.setColumnCount(len(data[0]))
            headers = [i[0] for i in cursor.description]
            self.result_table.setHorizontalHeaderLabels(headers)
                
            for row_num, row_data in enumerate(data):
                for col_num, col_data in enumerate(row_data):
                    self.result_table.setItem(row_num, col_num, QTableWidgetItem(str(col_data)))

            cursor.close()
            conn.close()
        
        except pymysql.Error as e:
            print(f"Error: {e}")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = DatabaseDisplayApp()
    window.show()
    sys.exit(app.exec_())
